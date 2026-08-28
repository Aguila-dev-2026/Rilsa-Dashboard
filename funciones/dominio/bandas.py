"""Lógica pura de bandas normativas y alertas."""

import pandas as pd

from funciones.ui.tema import AZUL_CORPORATIVO, ROJO_ALERTA

BANDAS_NCH1333_RIEGO = {
    "pH": {"inferior": 5.5, "superior": 9.0, "etiqueta": "Límite NCh 1333 · pH 5,5–9,0"},
    "Conductividad": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · CE ≤ 0,75 mS/cm"},
    "Conductividad [mS]": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · CE ≤ 0,75 mS/cm"},
    "Sulfato": {"superior": 250.0, "etiqueta": "Límite NCh 1333 · Sulfato ≤ 250 mg/L"},
    "Boro total": {"superior": 0.75, "etiqueta": "Límite NCh 1333 · Boro ≤ 0,75 mg/L"},
    "Sólidos disueltos": {"superior": 500.0, "etiqueta": "Límite NCh 1333 · Sólidos disueltos ≤ 500 mg/L"},
    "Cloruro": {"superior": 200.0, "etiqueta": "Límite NCh 1333 · Cloruro ≤ 200 mg/L"},
}


def obtener_banda_normativa(parametro):
    return BANDAS_NCH1333_RIEGO.get(parametro)


def obtener_limites_activos(parametro, limites_internos=None):
    """Devuelve el rango más restrictivo de las bandas actualmente visibles."""
    inferiores = []
    superiores = []
    mostrar_normativa = (
        limites_internos is None
        or limites_internos.get("normativa", True)
    )
    normativa = obtener_banda_normativa(parametro)
    if normativa and mostrar_normativa:
        if normativa.get("inferior") is not None:
            inferiores.append(float(normativa["inferior"]))
        if normativa.get("superior") is not None:
            superiores.append(float(normativa["superior"]))

    if limites_internos is not None:
        if limites_internos.get("inferior") is not None:
            inferiores.append(float(limites_internos["inferior"]))
        if limites_internos.get("superior") is not None:
            superiores.append(float(limites_internos["superior"]))

    return (
        max(inferiores) if inferiores else None,
        min(superiores) if superiores else None,
    )


def resaltar_valores_fuera_de_rango(
    fig,
    tipo_grafico,
    datos,
    limites_activos,
    columna_medicion=None,
):
    """Destaca en rojo las mediciones reales que exceden una banda activa."""
    limite_inferior, limite_superior = limites_activos
    if limite_inferior is None and limite_superior is None:
        return

    serie = datos[["Fecha", "Valor"]].copy().reset_index(drop=True)
    valores = pd.to_numeric(serie["Valor"], errors="coerce")
    fuera_de_rango = pd.Series(False, index=serie.index)
    if limite_inferior is not None:
        fuera_de_rango |= valores.lt(limite_inferior)
    if limite_superior is not None:
        fuera_de_rango |= valores.gt(limite_superior)
    fuera_de_rango &= valores.notna()
    if columna_medicion is not None:
        fuera_de_rango &= datos[columna_medicion].reset_index(drop=True).astype(bool)

    if tipo_grafico == "Barras":
        colores = [
            ROJO_ALERTA if alerta else AZUL_CORPORATIVO
            for alerta in fuera_de_rango
        ]
        fig.update_traces(marker_color=colores)
        return

    # La línea azul permanece como contexto; solo los tramos y puntos fuera de
    # rango se superponen en rojo para no sugerir que los datos faltantes alertan.
    serie["FueraDeRango"] = fuera_de_rango
    serie["Tramo"] = serie["FueraDeRango"].ne(
        serie["FueraDeRango"].shift()
    ).cumsum()
    primer_tramo = True
    for _, tramo in serie[serie["FueraDeRango"]].groupby("Tramo"):
        fig.add_scatter(
            x=tramo["Fecha"],
            y=tramo["Valor"],
            mode="lines+markers",
            name="Fuera de rango" if primer_tramo else None,
            showlegend=primer_tramo,
            line=dict(color=ROJO_ALERTA, width=3.8),
            marker=dict(
                color=ROJO_ALERTA,
                size=8,
                line=dict(color="#FFFFFF", width=1.4),
            ),
            hovertemplate="Valor fuera de rango: %{y:,.2f}<extra></extra>",
        )
        primer_tramo = False
