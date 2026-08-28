"""Renderizado de tendencias para gráficos Plotly."""

from funciones.dominio.tendencias import (
    calcular_tendencia,
    metodo_tendencia_recomendado,
    tipo_grafico_recomendado,
)
from funciones.ui.tema import COBRE

"""Cálculo y visualización de tendencias de series operacionales."""


import numpy as np


from funciones.ui.tema import COBRE


def agregar_tendencia(fig, datos, parametro, unidad):
    tendencia, metodo = calcular_tendencia(datos, parametro, unidad)
    if tendencia is None:
        return metodo

    sufijo_unidad = f" {unidad}" if unidad else ""
    fig.add_scatter(
        x=tendencia["Fecha"],
        y=tendencia["Tendencia"],
        mode="lines",
        name=f"Tendencia · {metodo}",
        line=dict(color=COBRE, width=3.2, dash="dot"),
        hovertemplate=(
            "<b>%{x|%d/%m/%Y}</b><br>"
            f"Tendencia: %{{y:,.2f}}{sufijo_unidad}<extra></extra>"
        ),
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=0.99,
        )
    )
    return metodo

