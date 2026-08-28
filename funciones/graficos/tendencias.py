"""Cálculo y visualización de tendencias de series operacionales."""

import numpy as np

from funciones.ui.tema import COBRE

TIPO_GRAFICO_RECOMENDADO = {
    "Ingresos [Ton]": "Barras",
    "Consumo P. Catiónico [kg]": "Barras",
    "Consumo P. Aniónico [kg]": "Barras",
    "Consumo PAC [kg]": "Barras",
    "Consumo Cal [kg]": "Barras",
    "% Humedad Lodo 1": "Líneas",
    "% Humedad Lodo 2": "Líneas",
    "Energía eléctrica consumida": "Barras",
    "Volumen TK3 [m3]": "Barras",
    "DQO TK3 [mg/l]": "Barras",
    "pH": "Líneas",
    "Conductividad [mS]": "Líneas",
    "Conductividad": "Líneas",
    "Turbiedad [NTU]": "Líneas",
    "Turbidez": "Líneas",
}


PARAMETROS_ACUMULATIVOS = {
    "Ingresos [Ton]",
    "Consumo P. Catiónico [kg]",
    "Consumo P. Aniónico [kg]",
    "Consumo PAC [kg]",
    "Consumo Cal [kg]",
    "Energía eléctrica consumida",
    "Descarga a Reactor N°1",
    "Carga DBO5",
    "Carga de nitrógeno total",
    "Carga de fósforo total",
}


TIPO_TENDENCIA_RECOMENDADA = {
    "Ingresos [Ton]": "EWMA adaptativa",
    "Consumo P. Catiónico [kg]": "EWMA adaptativa",
    "Consumo P. Aniónico [kg]": "EWMA adaptativa",
    "Consumo PAC [kg]": "EWMA adaptativa",
    "Consumo Cal [kg]": "EWMA adaptativa",
    "Energía eléctrica consumida": "EWMA adaptativa",
    "% Humedad Lodo 1": "Theil–Sen",
    "% Humedad Lodo 2": "Theil–Sen",
    "Volumen TK3 [m3]": "EWMA adaptativa",
    "DQO TK3 [mg/l]": "Theil–Sen",
    "Conductividad [mS]": "Theil–Sen",
    "Turbiedad [NTU]": "Theil–Sen",
    "pH": "Theil–Sen",
}


def tipo_grafico_recomendado(parametro):
    """Usa barras para acumulados y líneas para mediciones de calidad."""
    if parametro in PARAMETROS_ACUMULATIVOS:
        return "Barras"
    return TIPO_GRAFICO_RECOMENDADO.get(parametro, "Líneas")


def metodo_tendencia_recomendado(parametro, unidad):
    unidades_ewma = {"kg", "kg/día", "ton", "m3", "m3/día", "m³", "m³/día"}
    if parametro in TIPO_TENDENCIA_RECOMENDADA:
        return TIPO_TENDENCIA_RECOMENDADA[parametro]
    return "EWMA adaptativa" if unidad in unidades_ewma else "Theil–Sen"


def calcular_tendencia(datos, parametro, unidad=""):
    """Calcula la tendencia recomendada usando solo valores válidos del filtro."""
    validos = (
        datos.loc[
            datos["Valor"].notna() & datos["Valor"].ne(0),
            ["Fecha", "Valor"],
        ]
        .sort_values("Fecha")
        .copy()
    )
    if len(validos) < 2:
        return None, metodo_tendencia_recomendado(parametro, unidad)

    metodo = metodo_tendencia_recomendado(parametro, unidad)

    if metodo == "EWMA adaptativa":
        cantidad = len(validos)
        if cantidad <= 7:
            ventana = 3
        elif cantidad <= 31:
            ventana = 7
        elif cantidad <= 90:
            ventana = 14
        else:
            ventana = 30

        tendencia = validos.copy()
        tendencia["Tendencia"] = (
            tendencia["Valor"]
            .ewm(span=min(ventana, cantidad), adjust=False)
            .mean()
        )
        return tendencia[["Fecha", "Tendencia"]], metodo

    origen = validos["Fecha"].iloc[0]
    x = (validos["Fecha"] - origen).dt.total_seconds().to_numpy() / 86400
    y = validos["Valor"].to_numpy(dtype=float)
    pendientes = [
        (y[j] - y[i]) / (x[j] - x[i])
        for i in range(len(x) - 1)
        for j in range(i + 1, len(x))
        if x[j] != x[i]
    ]
    if not pendientes:
        return None, metodo

    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y - pendiente * x))
    tendencia = validos[["Fecha"]].copy()
    tendencia["Tendencia"] = intercepto + pendiente * x
    return tendencia, metodo


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

