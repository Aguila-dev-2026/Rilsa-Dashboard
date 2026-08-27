"""Importador provisional del proceso físico-químico.

Convierte una planilla Excel de origen al formato largo consumido por el
dashboard. La selección final de hoja y columnas se definirá al validar la
planilla real; por ahora detecta una hoja y una columna de fecha de forma
segura y conserva solo columnas con valores numéricos.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parent
ENTRADA_PREDETERMINADA = RAIZ_PROYECTO / "datos" / "Planilla Procesos RILES.xlsx"
SALIDA_PREDETERMINADA = RAIZ_PROYECTO / "datos_generados" / "fisico_quimico.xlsx"
NOMBRE_AREA = "Físico-químico"

HOJAS_PREFERIDAS = (
    "fisico quimico",
    "fisico-quimico",
    "fisicoquimico",
    "f q",
)
COLUMNAS_FECHA = ("fecha", "date", "dia")
COLUMNAS_A_IGNORAR = {
    "fecha",
    "date",
    "dia",
    "mes",
    "ano",
    "year",
    "semana",
}


def normalizar_nombre(valor: object) -> str:
    texto = unicodedata.normalize("NFD", str(valor))
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return re.sub(r"\s+", " ", texto.strip().lower())


def elegir_hoja(ruta: Path, hoja_solicitada: str | None) -> str:
    hojas = pd.ExcelFile(ruta).sheet_names

    if hoja_solicitada:
        if hoja_solicitada not in hojas:
            disponibles = ", ".join(hojas)
            raise ValueError(f"La hoja '{hoja_solicitada}' no existe. Disponibles: {disponibles}")
        return hoja_solicitada

    for hoja in hojas:
        if normalizar_nombre(hoja) in HOJAS_PREFERIDAS:
            return hoja

    return hojas[0]


def elegir_columna_fecha(datos: pd.DataFrame) -> str:
    nombres = {normalizar_nombre(columna): columna for columna in datos.columns}

    for candidato in COLUMNAS_FECHA:
        if candidato in nombres:
            return nombres[candidato]

    conversiones = {
        columna: pd.to_datetime(datos[columna], errors="coerce", dayfirst=True).notna().sum()
        for columna in datos.columns
    }
    columna, cantidad = max(conversiones.items(), key=lambda elemento: elemento[1])

    if cantidad == 0:
        raise ValueError("No se encontró una columna de fecha. Indica la hoja y revisa los encabezados.")

    return columna


def convertir_a_numero(serie: pd.Series) -> pd.Series:
    texto = (
        serie.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(texto, errors="coerce")


def importar_fisico_quimico(
    ruta_entrada: Path = ENTRADA_PREDETERMINADA,
    ruta_salida: Path = SALIDA_PREDETERMINADA,
    hoja: str | None = None,
) -> pd.DataFrame:
    if not ruta_entrada.exists():
        raise FileNotFoundError(f"No existe la planilla de origen: {ruta_entrada}")

    hoja_elegida = elegir_hoja(ruta_entrada, hoja)
    datos_origen = pd.read_excel(ruta_entrada, sheet_name=hoja_elegida)
    datos_origen = datos_origen.dropna(axis=1, how="all")

    columna_fecha = elegir_columna_fecha(datos_origen)
    fechas = pd.to_datetime(datos_origen[columna_fecha], errors="coerce", dayfirst=True)

    registros = []
    for columna in datos_origen.columns:
        nombre_normalizado = normalizar_nombre(columna)

        if nombre_normalizado in COLUMNAS_A_IGNORAR or nombre_normalizado.startswith("unnamed"):
            continue

        valores = convertir_a_numero(datos_origen[columna])
        validos = fechas.notna() & valores.notna()

        if not validos.any():
            continue

        registros.append(
            pd.DataFrame(
                {
                    "Fecha": fechas[validos],
                    "Area": NOMBRE_AREA,
                    "Parametro": str(columna).strip(),
                    "Valor": valores[validos],
                    "Unidad": "",
                }
            )
        )

    if not registros:
        raise ValueError(
            "No se encontraron columnas numéricas importables. "
            "Revisaremos la hoja y las columnas de la planilla."
        )

    resultado = (
        pd.concat(registros, ignore_index=True)
        .sort_values(["Fecha", "Parametro"])
        .reset_index(drop=True)
    )

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_excel(ruta_salida, index=False)

    print(f"Hoja importada: {hoja_elegida}")
    print(f"Columna de fecha: {columna_fecha}")
    print(f"Parámetros importados: {resultado['Parametro'].nunique()}")
    print(f"Archivo generado: {ruta_salida}")
    return resultado


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera datos_generados/fisico_quimico.xlsx desde una planilla RILES."
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=ENTRADA_PREDETERMINADA,
        help="Ruta de la planilla de origen.",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=SALIDA_PREDETERMINADA,
        help="Ruta del archivo normalizado que leerá el dashboard.",
    )
    parser.add_argument(
        "--hoja",
        help="Nombre exacto de la hoja a importar. Si se omite, se detecta automáticamente.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    opciones = argumentos()
    importar_fisico_quimico(opciones.entrada, opciones.salida, opciones.hoja)
