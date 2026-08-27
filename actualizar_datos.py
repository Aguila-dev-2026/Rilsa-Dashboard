"""Actualización segura y transaccional del almacenamiento operacional.

Las planillas Excel son fuentes de solo lectura. La aplicación consulta SQLite
como almacenamiento principal y conserva los Excel normalizados como respaldo
temporal durante la migración.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from importar import (
    ENTRADA_PREDETERMINADA as ENTRADA_FISICO_QUIMICO,
    importar_fisico_quimico,
)
from importar_analisis_aerobico import (
    ENTRADA_PREDETERMINADA as ENTRADA_ANALISIS_AEROBICO,
    importar_analisis_aerobico,
)


RAIZ_PROYECTO = Path(__file__).resolve().parent
CARPETA_GENERADOS = RAIZ_PROYECTO / "datos_generados"
BASE_DATOS = CARPETA_GENERADOS / "riles.db"
BASE_DATOS_TEMPORAL = CARPETA_GENERADOS / "riles_temporal.db"
BASE_DATOS_ANTERIOR = CARPETA_GENERADOS / "riles_anterior.db"
VERSION_ESQUEMA = 1

SALIDA_FISICO_QUIMICO = CARPETA_GENERADOS / "fisico_quimico.xlsx"
SALIDA_ANALISIS_AEROBICO = CARPETA_GENERADOS / "analisis_planta_aerobica.xlsx"
SALIDA_FISICO_TEMPORAL = CARPETA_GENERADOS / "fisico_quimico_temporal.xlsx"
SALIDA_ANALISIS_TEMPORAL = (
    CARPETA_GENERADOS / "analisis_planta_aerobica_temporal.xlsx"
)

COLUMNAS_MEDICIONES = [
    "Fecha",
    "Area",
    "Punto",
    "Turno",
    "Parametro",
    "Valor",
    "Unidad",
    "TipoDato",
    "Calificador",
    "Fuente",
    "Hoja",
]


def huella_archivo(ruta: Path) -> dict:
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la planilla de origen: {ruta}")

    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)

    estado = ruta.stat()
    return {
        "Nombre": ruta.name,
        "Ruta": str(ruta),
        "SHA256": digest.hexdigest(),
        "Tamano": estado.st_size,
        "MtimeNS": estado.st_mtime_ns,
    }


def base_vigente_y_sin_cambios(huellas: list[dict]) -> bool:
    if not BASE_DATOS.exists():
        return False

    try:
        with sqlite3.connect(BASE_DATOS) as conexion:
            integridad = conexion.execute("PRAGMA integrity_check").fetchone()[0]
            if integridad != "ok":
                return False

            version = conexion.execute(
                "SELECT Valor FROM metadata_sistema WHERE Clave = 'version_esquema'"
            ).fetchone()
            if not version or int(version[0]) != VERSION_ESQUEMA:
                return False

            guardadas = {
                fila[0]: fila[1]
                for fila in conexion.execute(
                    "SELECT Nombre, SHA256 FROM metadata_fuentes"
                ).fetchall()
            }
    except (sqlite3.DatabaseError, OSError, TypeError, ValueError):
        return False

    actuales = {huella["Nombre"]: huella["SHA256"] for huella in huellas}
    return guardadas == actuales


def preparar_datos(
    fisico_quimico: pd.DataFrame,
    analisis_aerobico: pd.DataFrame,
) -> pd.DataFrame:
    fisico_quimico = fisico_quimico.copy()
    valores_fisico = {
        "Punto": "Físico-químico",
        "Turno": "",
        "TipoDato": "Medición",
        "Calificador": "",
        "Fuente": "Planilla Procesos RILES.xlsx",
        "Hoja": "Físico-químico",
    }
    for columna, valor in valores_fisico.items():
        fisico_quimico[columna] = valor

    analisis_aerobico = analisis_aerobico.copy()
    fisico_quimico["_PrioridadFuente"] = 0
    analisis_aerobico["_PrioridadFuente"] = 100

    datos = pd.concat(
        [fisico_quimico, analisis_aerobico],
        ignore_index=True,
        sort=False,
    )
    for columna in COLUMNAS_MEDICIONES:
        if columna not in datos.columns:
            datos[columna] = ""

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce").dt.normalize()
    datos["Valor"] = pd.to_numeric(datos["Valor"], errors="coerce")
    columnas_texto = [
        columna
        for columna in COLUMNAS_MEDICIONES
        if columna not in {"Fecha", "Valor"}
    ]
    for columna in columnas_texto:
        datos[columna] = datos[columna].fillna("").astype(str).str.strip()

    datos = datos.dropna(subset=["Fecha", "Valor"])
    datos = datos[
        datos["Area"].ne("")
        & datos["Parametro"].ne("")
        & datos["Fecha"].between(
            pd.Timestamp("2020-01-01"),
            pd.Timestamp.today().normalize(),
        )
    ]

    claves = ["Fecha", "Area", "Punto", "Turno", "Parametro"]
    datos = (
        datos.sort_values([*claves, "_PrioridadFuente"])
        .drop_duplicates(subset=claves, keep="last")
        .drop(columns="_PrioridadFuente")
        .sort_values(["Fecha", "Area", "Punto", "Turno", "Parametro"])
        .reset_index(drop=True)
    )
    return datos[COLUMNAS_MEDICIONES]


def conteos_base(ruta: Path) -> dict[str, int]:
    if not ruta.exists():
        return {}
    try:
        with sqlite3.connect(ruta) as conexion:
            return {
                area: int(cantidad)
                for area, cantidad in conexion.execute(
                    "SELECT Area, COUNT(*) FROM mediciones GROUP BY Area"
                ).fetchall()
            }
    except (sqlite3.DatabaseError, OSError):
        return {}


def validar_datos(datos: pd.DataFrame, conteos_anteriores: dict[str, int]) -> None:
    faltantes = set(COLUMNAS_MEDICIONES).difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas normalizadas: {', '.join(sorted(faltantes))}")
    if datos.empty:
        raise ValueError("La actualización no produjo mediciones.")

    esperadas = {"Físico-químico", "Planta Alta", "Planta Aeróbica", "Efluente"}
    faltan_areas = esperadas.difference(datos["Area"].unique())
    if faltan_areas:
        raise ValueError(f"La actualización perdió áreas: {', '.join(sorted(faltan_areas))}")

    claves = ["Fecha", "Area", "Punto", "Turno", "Parametro"]
    if datos[claves + ["Valor"]].isna().any().any():
        raise ValueError("Existen campos obligatorios vacíos en la actualización.")
    if datos.duplicated(claves).any():
        raise ValueError("La actualización contiene mediciones duplicadas.")
    if (datos["Fecha"] > pd.Timestamp.today().normalize()).any():
        raise ValueError("La actualización contiene fechas futuras.")

    conteos_nuevos = datos.groupby("Area").size().to_dict()
    for area, cantidad_anterior in conteos_anteriores.items():
        cantidad_nueva = int(conteos_nuevos.get(area, 0))
        if cantidad_anterior >= 20 and cantidad_nueva < cantidad_anterior * 0.8:
            raise ValueError(
                f"La cantidad de registros de {area} cayó más de 20 % "
                f"({cantidad_anterior} → {cantidad_nueva})."
            )


def construir_sqlite(
    datos: pd.DataFrame,
    huellas: list[dict],
    ruta_temporal: Path,
) -> None:
    ruta_temporal.unlink(missing_ok=True)
    datos_sql = datos.copy()
    datos_sql["Fecha"] = datos_sql["Fecha"].dt.strftime("%Y-%m-%d")

    with sqlite3.connect(ruta_temporal) as conexion:
        conexion.execute("PRAGMA journal_mode = DELETE")
        conexion.execute("PRAGMA synchronous = FULL")
        datos_sql.to_sql("mediciones", conexion, index=False, if_exists="replace")
        pd.DataFrame(huellas).to_sql(
            "metadata_fuentes",
            conexion,
            index=False,
            if_exists="replace",
        )
        pd.DataFrame(
            [
                {"Clave": "version_esquema", "Valor": str(VERSION_ESQUEMA)},
                {"Clave": "actualizado_en", "Valor": datetime.now().isoformat()},
                {"Clave": "registros", "Valor": str(len(datos))},
            ]
        ).to_sql("metadata_sistema", conexion, index=False, if_exists="replace")

        conexion.executescript(
            """
            CREATE INDEX idx_mediciones_area
                ON mediciones (Area);
            CREATE INDEX idx_mediciones_contexto
                ON mediciones (Area, Punto, Turno, TipoDato);
            CREATE INDEX idx_mediciones_parametro_fecha
                ON mediciones (Parametro, Fecha);
            CREATE INDEX idx_mediciones_consulta
                ON mediciones (Area, Punto, Turno, TipoDato, Parametro, Fecha);
            """
        )
        conexion.commit()
        integridad = conexion.execute("PRAGMA integrity_check").fetchone()[0]
        if integridad != "ok":
            raise ValueError(f"SQLite no superó la validación de integridad: {integridad}")


def reemplazar_archivos() -> None:
    if BASE_DATOS.exists():
        respaldo_temporal = CARPETA_GENERADOS / "riles_anterior_temporal.db"
        respaldo_temporal.unlink(missing_ok=True)
        shutil.copy2(BASE_DATOS, respaldo_temporal)
        os.replace(respaldo_temporal, BASE_DATOS_ANTERIOR)

    os.replace(BASE_DATOS_TEMPORAL, BASE_DATOS)
    os.replace(SALIDA_FISICO_TEMPORAL, SALIDA_FISICO_QUIMICO)
    os.replace(SALIDA_ANALISIS_TEMPORAL, SALIDA_ANALISIS_AEROBICO)


def actualizar_datos(
    entrada_fisico_quimico: Path = ENTRADA_FISICO_QUIMICO,
    entrada_analisis_aerobico: Path = ENTRADA_ANALISIS_AEROBICO,
) -> dict:
    CARPETA_GENERADOS.mkdir(parents=True, exist_ok=True)
    huellas = [
        huella_archivo(Path(entrada_fisico_quimico)),
        huella_archivo(Path(entrada_analisis_aerobico)),
    ]
    if base_vigente_y_sin_cambios(huellas):
        with sqlite3.connect(BASE_DATOS) as conexion:
            registros = conexion.execute("SELECT COUNT(*) FROM mediciones").fetchone()[0]
        return {"estado": "sin_cambios", "registros": int(registros)}

    temporales = [
        BASE_DATOS_TEMPORAL,
        SALIDA_FISICO_TEMPORAL,
        SALIDA_ANALISIS_TEMPORAL,
    ]
    for ruta in temporales:
        ruta.unlink(missing_ok=True)

    try:
        fisico = importar_fisico_quimico(
            Path(entrada_fisico_quimico),
            SALIDA_FISICO_TEMPORAL,
        )
        aerobico = importar_analisis_aerobico(
            Path(entrada_analisis_aerobico),
            SALIDA_ANALISIS_TEMPORAL,
        )
        datos = preparar_datos(fisico, aerobico)
        validar_datos(datos, conteos_base(BASE_DATOS))
        construir_sqlite(datos, huellas, BASE_DATOS_TEMPORAL)
        reemplazar_archivos()
    except Exception:
        for ruta in temporales:
            ruta.unlink(missing_ok=True)
        raise

    return {
        "estado": "actualizado",
        "registros": len(datos),
        "areas": datos.groupby("Area").size().to_dict(),
    }
