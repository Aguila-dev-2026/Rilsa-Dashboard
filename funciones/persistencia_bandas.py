"""Persistencia sencilla de preferencias de bandas del dashboard."""

import json
import os
import tempfile
from pathlib import Path


RUTA_PREFERENCIAS = Path(__file__).resolve().parents[1] / "datos_generados" / "preferencias_bandas.json"


def cargar_preferencias_bandas():
    try:
        with RUTA_PREFERENCIAS.open("r", encoding="utf-8") as archivo:
            contenido = json.load(archivo)
        return contenido if isinstance(contenido, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def guardar_preferencia_banda(clave, preferencia):
    preferencias = cargar_preferencias_bandas()
    preferencias[str(clave)] = preferencia
    RUTA_PREFERENCIAS.parent.mkdir(parents=True, exist_ok=True)
    fd, ruta_temporal = tempfile.mkstemp(
        prefix="preferencias_bandas_",
        suffix=".json",
        dir=RUTA_PREFERENCIAS.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as archivo:
            json.dump(preferencias, archivo, ensure_ascii=False, indent=2)
        os.replace(ruta_temporal, RUTA_PREFERENCIAS)
    finally:
        try:
            os.unlink(ruta_temporal)
        except FileNotFoundError:
            pass
