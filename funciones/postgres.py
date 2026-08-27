"""Acceso PostgreSQL para el modo multiusuario en Azure."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

VERSION_ESQUEMA = 6

COLUMNAS_SQL = {
    "Fecha": "fecha",
    "Area": "area",
    "Punto": "punto",
    "Turno": "turno",
    "Parametro": "parametro",
    "Valor": "valor",
    "Unidad": "unidad",
    "TipoDato": "tipo_dato",
    "Calificador": "calificador",
    "Fuente": "fuente",
    "Hoja": "hoja",
}

SELECCION_MEDICIONES = """
    SELECT
        fecha AS "Fecha",
        area AS "Area",
        punto AS "Punto",
        turno AS "Turno",
        parametro AS "Parametro",
        valor AS "Valor",
        unidad AS "Unidad",
        tipo_dato AS "TipoDato",
        calificador AS "Calificador",
        fuente AS "Fuente",
        hoja AS "Hoja"
    FROM mediciones
"""


@lru_cache(maxsize=4)
def obtener_motor(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        hide_parameters=True,
    )


def tabla_existe(conexion, nombre: str) -> bool:
    consulta = text("SELECT to_regclass(:nombre) IS NOT NULL")
    return bool(conexion.execute(consulta, {"nombre": f"public.{nombre}"}).scalar())


def hay_mediciones(database_url: str) -> bool:
    with obtener_motor(database_url).connect() as conexion:
        if not tabla_existe(conexion, "mediciones"):
            return False
        return bool(conexion.execute(text("SELECT 1 FROM mediciones LIMIT 1")).first())


def consultar_mediciones(
    database_url: str,
    *,
    nombre_area=None,
    punto=None,
    parametro=None,
    fecha_inicio=None,
    fecha_fin=None,
) -> pd.DataFrame:
    condiciones = []
    parametros_sql = {}
    filtros = {
        "area": nombre_area,
        "punto": punto,
        "parametro": parametro,
    }
    for columna, valor in filtros.items():
        if valor is not None:
            condiciones.append(f"{columna} = :{columna}")
            parametros_sql[columna] = valor
    if fecha_inicio is not None:
        condiciones.append("fecha >= :fecha_inicio")
        parametros_sql["fecha_inicio"] = fecha_inicio
    if fecha_fin is not None:
        condiciones.append("fecha <= :fecha_fin")
        parametros_sql["fecha_fin"] = fecha_fin

    consulta = SELECCION_MEDICIONES
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY fecha"

    return pd.read_sql_query(
        text(consulta),
        obtener_motor(database_url),
        params=parametros_sql,
        parse_dates=["Fecha"],
    )


def consultar_catalogo(database_url: str, nombre_area=None) -> pd.DataFrame:
    consulta = """
        SELECT
            area AS "Area",
            punto AS "Punto",
            parametro AS "Parametro",
            COALESCE(unidad, '') AS "Unidad",
            MIN(fecha) AS "FechaMin",
            MAX(fecha) AS "FechaMax",
            COUNT(*) AS "Registros"
        FROM mediciones
    """
    parametros_sql = {}
    if nombre_area is not None:
        consulta += " WHERE area = :nombre_area"
        parametros_sql["nombre_area"] = nombre_area
    consulta += """
        GROUP BY area, punto, parametro, COALESCE(unidad, '')
        ORDER BY area, punto, parametro
    """
    return pd.read_sql_query(
        text(consulta),
        obtener_motor(database_url),
        params=parametros_sql,
        parse_dates=["FechaMin", "FechaMax"],
    )


def conteos_por_area(database_url: str) -> dict[str, int]:
    with obtener_motor(database_url).connect() as conexion:
        if not tabla_existe(conexion, "mediciones"):
            return {}
        filas = conexion.execute(
            text("SELECT area, COUNT(*) FROM mediciones GROUP BY area")
        )
        return {area: int(cantidad) for area, cantidad in filas}


def base_vigente_y_sin_cambios(database_url: str, huellas: list[dict]) -> bool:
    with obtener_motor(database_url).connect() as conexion:
        requeridas = {"mediciones", "metadata_sistema", "metadata_fuentes"}
        if not all(tabla_existe(conexion, tabla) for tabla in requeridas):
            return False
        version = conexion.execute(
            text("SELECT valor FROM metadata_sistema WHERE clave = 'version_esquema'")
        ).scalar()
        if version is None or int(version) != VERSION_ESQUEMA:
            return False
        guardadas = {
            nombre: sha
            for nombre, sha in conexion.execute(
                text("SELECT nombre, sha256 FROM metadata_fuentes")
            )
        }
    actuales = {huella["Nombre"]: huella["SHA256"] for huella in huellas}
    return guardadas == actuales


def reemplazar_mediciones(
    database_url: str,
    datos: pd.DataFrame,
    huellas: list[dict],
) -> None:
    datos_sql = datos.rename(columns=COLUMNAS_SQL).copy()
    datos_sql["fecha"] = pd.to_datetime(datos_sql["fecha"]).dt.normalize()
    metadata_fuentes = pd.DataFrame(huellas).rename(
        columns={
            "Nombre": "nombre",
            "Ruta": "ruta",
            "SHA256": "sha256",
            "Tamano": "tamano",
            "MtimeNS": "mtime_ns",
        }
    )
    metadata_sistema = pd.DataFrame(
        [
            {"clave": "version_esquema", "valor": str(VERSION_ESQUEMA)},
            {
                "clave": "actualizado_en",
                "valor": datetime.now(timezone.utc).isoformat(),
            },
            {"clave": "registros", "valor": str(len(datos_sql))},
        ]
    )

    motor = obtener_motor(database_url)
    with motor.begin() as conexion:
        datos_sql.to_sql(
            "mediciones_nuevas",
            conexion,
            index=False,
            if_exists="replace",
            chunksize=2000,
        )
        metadata_fuentes.to_sql(
            "metadata_fuentes",
            conexion,
            index=False,
            if_exists="replace",
        )
        metadata_sistema.to_sql(
            "metadata_sistema",
            conexion,
            index=False,
            if_exists="replace",
        )
        conexion.execute(text("DROP TABLE IF EXISTS mediciones_anterior"))
        conexion.execute(
            text("ALTER TABLE IF EXISTS mediciones RENAME TO mediciones_anterior")
        )
        conexion.execute(text("ALTER TABLE mediciones_nuevas RENAME TO mediciones"))
        conexion.execute(text("DROP TABLE IF EXISTS mediciones_anterior"))
        conexion.execute(text("CREATE INDEX idx_mediciones_area ON mediciones (area)"))
        conexion.execute(
            text(
                "CREATE INDEX idx_mediciones_contexto "
                "ON mediciones (area, punto, turno, tipo_dato)"
            )
        )
        conexion.execute(
            text(
                "CREATE INDEX idx_mediciones_parametro_fecha "
                "ON mediciones (parametro, fecha)"
            )
        )
        conexion.execute(
            text(
                "CREATE INDEX idx_mediciones_dashboard "
                "ON mediciones (area, punto, parametro, fecha)"
            )
        )

    motor.dispose()
    obtener_motor.cache_clear()
