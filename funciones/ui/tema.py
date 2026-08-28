"""Paleta y configuración visual compartida por la aplicación."""

import streamlit as st


CONFIGURACION_GRAFICO = {
    "displayModeBar": "always",
    # La rueda/gesto del touchpad queda para el scroll horizontal del gráfico;
    # el zoom se realiza desde los botones nativos de la barra.
    "scrollZoom": False,
    "responsive": True,
    "displaylogo": False,
    # Herramientas nativas del gráfico; resetScale2d restaura la vista inicial.
    "modeBarButtons": [[
        "zoom2d",
        "pan2d",
        "autoScale2d",
        "resetScale2d",
        "toImage",
    ]],
}

VINO = "#6D1F2B"
VINO_PROFUNDO = "#48121A"
COBRE = "#B36F3D"
AZUL_CORPORATIVO = "#147EAF"
AZUL_BORDE = "#0C638D"
AZUL_CIELO = "#67C5E8"
COLOR_TURNO_MANANA = AZUL_CORPORATIVO
COLOR_TURNO_TARDE = "#C47A45"
COLOR_TURNO_SIN_DEFINIR = "#8A8F98"
ROJO_ALERTA = "#A12C32"
TINTA_PDF = "#171514"


def tema_nativo_oscuro():
    """Consulta el tema elegido en el selector nativo de Streamlit."""
    try:
        return st.context.theme.type == "dark"
    except (AttributeError, RuntimeError):
        return False


def paleta_grafico(oscuro):
    """Devuelve los colores necesarios para gráficos fuera del DOM principal."""
    if oscuro:
        return {
            "template": "plotly_dark",
            "texto": "#FAFAFA",
            "texto_eje": "#C8CBD4",
            "cuadricula": "rgba(250,250,250,0.14)",
            "borde_marcador": "#0E1117",
            "fin_semana": "#72B7E3",
        }
    return {
        "template": "plotly_white",
        "texto": "#171514",
        "texto_eje": "#332E2A",
        "cuadricula": "rgba(23,21,20,0.24)",
        "borde_marcador": "#FFFDF8",
        "fin_semana": "#4F92BD",
    }


def colores_turnos():
    """Paleta estable para comparar los turnos en líneas y barras."""
    return {
        "Mañana": COLOR_TURNO_MANANA,
        "Tarde": COLOR_TURNO_TARDE,
        "Sin turno": COLOR_TURNO_SIN_DEFINIR,
    }
