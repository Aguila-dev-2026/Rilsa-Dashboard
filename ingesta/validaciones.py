"""Validaciones comunes de resultados normalizados de importación."""

from __future__ import annotations

import pandas as pd


def validar_datos(
    datos: pd.DataFrame,
    conteos_anteriores: dict[str, int],
    *,
    columnas_mediciones: list[str],
    areas_esperadas: set[str],
) -> None:
    """Valida integridad, duplicados y pérdidas anómalas de registros."""
    faltantes = set(columnas_mediciones).difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas normalizadas: {', '.join(sorted(faltantes))}")
    if datos.empty:
        raise ValueError("La actualización no produjo mediciones.")

    faltan_areas = areas_esperadas.difference(datos["Area"].unique())
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
