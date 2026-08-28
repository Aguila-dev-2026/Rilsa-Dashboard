"""Importación y validación de fuentes de datos operacionales."""

from __future__ import annotations

__all__ = ["importar_analisis_aerobico", "importar_fisico_quimico"]


def __getattr__(nombre: str):
    """Carga los importadores bajo demanda para evitar ciclos con los CLI."""
    if nombre == "importar_analisis_aerobico":
        from .aerobico import importar_analisis_aerobico

        return importar_analisis_aerobico
    if nombre == "importar_fisico_quimico":
        from .fisico_quimico import importar_fisico_quimico

        return importar_fisico_quimico
    raise AttributeError(f"El módulo {__name__!r} no contiene {nombre!r}")
