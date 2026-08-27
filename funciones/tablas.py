"""Limpieza de tablas para presentación, sin alterar la fuente de datos."""

from __future__ import annotations

import pandas as pd


VALORES_SIN_INFORMACION = {"", "-", "none", "null", "nan", "nat", "<na>"}


def preparar_columnas_visibles(datos: pd.DataFrame) -> pd.DataFrame:
    """Oculta columnas vacías y elimina marcadores textuales de ausencia."""
    tabla = datos.copy()
    columnas_visibles = []

    for columna in tabla.columns:
        nombre = "" if columna is None else str(columna).strip()
        if nombre.casefold() in VALORES_SIN_INFORMACION:
            continue

        texto = tabla[columna].astype("string").str.strip()
        sin_informacion = (
            tabla[columna].isna()
            | texto.str.casefold().isin(VALORES_SIN_INFORMACION)
        )
        if sin_informacion.all():
            continue

        if sin_informacion.any():
            tabla.loc[sin_informacion, columna] = ""
        columnas_visibles.append(columna)

    return tabla.loc[:, columnas_visibles]
