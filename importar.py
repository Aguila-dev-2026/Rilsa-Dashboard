"""Importador de la hoja físico-química de la planilla RILES.

Genera datos_generados/fisico_quimico.xlsx en el formato consumido por el
dashboard. Las columnas permitidas se definieron durante la primera revisión
de la planilla; las demás se ignoran deliberadamente.
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
HOJA_FISICO_QUIMICO = "Físico-químico"
FILA_ENCABEZADOS = 1
NOMBRE_AREA = "Físico-químico"

# Solo estas mediciones entran al dashboard. Las lecturas acumuladas, horas de
# bombas, columnas vacías y campos con "-" quedan fuera de la importación.
COLUMNAS_PERMITIDAS = {
    "ingresos [ton]": "Ingresos [Ton]",
    "consumo p. cationico [kg]": "Consumo P. Catiónico [kg]",
    "consumo p. anionico [kg]": "Consumo P. Aniónico [kg]",
    "consumo pac [kg]": "Consumo PAC [kg]",
    "consumo cal [kg]": "Consumo Cal [kg]",
    "% humedad lodo 1": "% Humedad Lodo 1",
    "% humedad lodo 2": "% Humedad Lodo 2",
    "energia electrica consumida": "Energía eléctrica consumida",
    "[m3]": "Volumen TK3 [m3]",
    "dqo tk3 [mg/l]": "DQO TK3 [mg/l]",
    "ph": "pH",
    "conductividad [ms]": "Conductividad [mS]",
    "turbiedad [ntu]": "Turbiedad [NTU]",
}


def normalizar_nombre(valor: object) -> str:
    texto = unicodedata.normalize("NFD", str(valor))
    texto = "".join(
        caracter for caracter in texto if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"\s+", " ", texto.strip().lower())


def convertir_a_numero(serie: pd.Series) -> pd.Series:
    """Convierte números Excel y texto con coma decimal de forma compatible."""

    def convertir_valor(valor: object) -> float:
        if pd.isna(valor):
            return float("nan")

        if isinstance(valor, (int, float)):
            return float(valor)

        texto = str(valor).strip().replace("\u00a0", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")

        try:
            return float(texto)
        except ValueError:
            return float("nan")

    return serie.map(convertir_valor).astype("float64")

def unidad_de(parametro: str) -> str:
    coincidencia = re.search(r"\[([^\]]+)\]", parametro)
    if coincidencia:
        return coincidencia.group(1)

    return "%" if parametro.startswith("%") else ""


def importar_fisico_quimico(
    ruta_entrada: Path = ENTRADA_PREDETERMINADA,
    ruta_salida: Path = SALIDA_PREDETERMINADA,
) -> pd.DataFrame:
    if not ruta_entrada.exists():
        raise FileNotFoundError(f"No existe la planilla de origen: {ruta_entrada}")

    datos_origen = pd.read_excel(
        ruta_entrada,
        sheet_name=HOJA_FISICO_QUIMICO,
        header=FILA_ENCABEZADOS,
    ).dropna(axis=1, how="all")

    nombres = {normalizar_nombre(columna): columna for columna in datos_origen.columns}
    if "dia" not in nombres:
        raise ValueError("La hoja Físico-químico no contiene la columna 'Día'.")

    fechas = pd.to_datetime(datos_origen[nombres["dia"]], errors="coerce", dayfirst=True)
    registros = []
    columnas_encontradas = []

    for nombre_normalizado, parametro in COLUMNAS_PERMITIDAS.items():
        columna = nombres.get(nombre_normalizado)
        if columna is None:
            continue

        valores = convertir_a_numero(datos_origen[columna])
        validos = fechas.notna() & valores.notna()
        if not validos.any():
            continue

        columnas_encontradas.append(parametro)
        registros.append(
            pd.DataFrame(
                {
                    "Fecha": fechas[validos],
                    "Area": NOMBRE_AREA,
                    "Parametro": parametro,
                    "Valor": valores[validos],
                    "Unidad": unidad_de(parametro),
                }
            )
        )

    if not registros:
        raise ValueError("No se encontraron mediciones válidas para importar.")

    resultado = (
        pd.concat(registros, ignore_index=True)
        .sort_values(["Fecha", "Parametro"])
        .reset_index(drop=True)
    )

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_excel(ruta_salida, index=False)

    print(f"Hoja importada: {HOJA_FISICO_QUIMICO}")
    print(f"Parámetros importados ({len(columnas_encontradas)}):")
    print(", ".join(columnas_encontradas))
    print(f"Archivo generado: {ruta_salida}")
    return resultado


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera datos_generados/fisico_quimico.xlsx desde la planilla RILES."
    )
    parser.add_argument("--entrada", type=Path, default=ENTRADA_PREDETERMINADA)
    parser.add_argument("--salida", type=Path, default=SALIDA_PREDETERMINADA)
    return parser.parse_args()


if __name__ == "__main__":
    opciones = argumentos()
    importar_fisico_quimico(opciones.entrada, opciones.salida)
