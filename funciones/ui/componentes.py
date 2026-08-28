"""Componentes visuales pequeños reutilizables por las páginas."""

from pathlib import Path

import streamlit as st


def aplicar_detalles_grafico() -> None:
    """Conserva retoques neutrales sin interferir con el tema nativo."""
    st.html(
        """
        <style>
          .js-plotly-plot .hoverlayer .bg {
            stroke-width: 3px !important;
            rx: 7px;
            ry: 7px;
          }
          .js-plotly-plot .hoverlayer .axistext {
            display: none !important;
          }
        </style>
        """
    )


def mostrar_ruta_origen(ruta: str | Path) -> Path:
    """Muestra rutas relativas cuando pertenecen al proyecto actual."""
    ruta = Path(ruta)
    return ruta.relative_to(Path.cwd()) if ruta.is_relative_to(Path.cwd()) else ruta
