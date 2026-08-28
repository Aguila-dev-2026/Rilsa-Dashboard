"""API pública de reglas de dominio bajo el namespace instalable."""

from funciones.dominio.bandas import obtener_banda_normativa, obtener_limites_activos
from funciones.dominio.tendencias import calcular_tendencia

__all__ = [
    "calcular_tendencia",
    "obtener_banda_normativa",
    "obtener_limites_activos",
]
