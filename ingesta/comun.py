"""Utilidades compartidas por los importadores de planillas."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd


def normalizar_nombre(valor: object) -> str:
    """Normaliza encabezados para tolerar acentos y espacios variables."""
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


def huella_archivo(ruta: Path) -> dict:
    """Genera la huella SHA-256 y metadatos de una fuente de datos."""
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
