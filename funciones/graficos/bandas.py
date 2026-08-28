"""Bandas normativas e internas para gráficos operacionales."""

import pandas as pd
import streamlit as st

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
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>"
            "Valor fuera de rango: %{y:,.2f}<extra></extra>",
        )
        primer_tramo = False


def agregar_bandas(fig, parametro, limites_internos=None):
    """Añade bandas normativas e internas sin depender de la tendencia."""
    mostrar_normativa = (
        limites_internos is None
        or limites_internos.get("normativa", True)
    )
    normativa = obtener_banda_normativa(parametro)
    if normativa and mostrar_normativa:
        limite_inferior_norma = normativa.get("inferior")
        limite_superior_norma = normativa.get("superior")
        if limite_inferior_norma is not None and limite_superior_norma is not None:
            fig.add_hrect(
                y0=limite_inferior_norma,
                y1=limite_superior_norma,
                fillcolor="rgba(46,106,77,0.14)",
                line_width=0,
                layer="below",
                annotation_text=normativa["etiqueta"],
                annotation_position="top left",
                annotation_font=dict(color="#4F9A75", size=12),
            )
        for limite in (limite_inferior_norma, limite_superior_norma):
            if limite is None:
                continue
            opciones_linea = {
                "y": limite,
                "line": dict(
                    color="rgba(79,154,117,0.78)",
                    width=1.2,
                    dash="dash",
                ),
            }
            if limite_inferior_norma is None:
                opciones_linea.update(
                    annotation_text=normativa["etiqueta"],
                    annotation_position="bottom left",
                    annotation_font=dict(color="#4F9A75", size=12),
                    annotation_bgcolor="rgba(247,249,252,0.94)",
                    annotation_bordercolor="rgba(79,154,117,0.45)",
                    annotation_borderpad=4,
                )
            fig.add_hline(**opciones_linea)

    if limites_internos is None:
        return

    limite_inferior = limites_internos.get("inferior")
    limite_superior = limites_internos.get("superior")
    if limite_inferior is not None and limite_superior is not None:
        fig.add_hrect(
            y0=limite_inferior,
            y1=limite_superior,
            fillcolor="rgba(161,44,50,0.075)",
            line_width=0,
            layer="below",
            annotation_text=(
                "Bandas internas · "
                f"{limite_inferior:,.2f}–{limite_superior:,.2f}"
            ),
            annotation_position="bottom right",
            annotation_font=dict(color=ROJO_ALERTA, size=12),
        )

    bandas_activas = (
        ("Banda inferior", limite_inferior),
        ("Banda superior", limite_superior),
    )
    for nombre, limite in bandas_activas:
        if limite is None:
            continue
        fig.add_hline(
            y=limite,
            line=dict(color=ROJO_ALERTA, width=2.4),
            annotation_text=(f"{nombre} · {limite:,.2f}")
            if limite_inferior is None or limite_superior is None
            else None,
            annotation_position="bottom right",
            annotation_font=dict(color=ROJO_ALERTA, size=12),
        )


def configurar_bandas(datos, clave, tiene_bandas_normativas=False):
    """Recoge bandas independientes y las conserva durante la sesión."""
    valores = datos["Valor"].dropna().astype(float)
    if valores.empty:
        return None

    minimo_observado = float(valores.min())
    maximo_observado = float(valores.max())
    amplitud = max(maximo_observado - minimo_observado, abs(valores.mean()) * 0.1, 1)
    paso = max(amplitud / 100, 0.01)
    superior_inicial = max(maximo_observado, minimo_observado + paso)

    with st.sidebar.expander("Bandas", expanded=False):
        st.caption("Referencias normativas e internas para control operacional.")
        mostrar_normativa = True
        if tiene_bandas_normativas:
            mostrar_normativa = st.toggle(
                "Mostrar bandas normativas",
                value=True,
                key=f"mostrar_bandas_normativas_{clave}",
            )
        mostrar_inferior = st.toggle(
            "Añadir banda inferior",
            value=False,
            key=f"mostrar_banda_inferior_{clave}",
        )
        limite_inferior = None
        if mostrar_inferior:
            limite_inferior = st.number_input(
                "Límite inferior",
                value=minimo_observado,
                step=paso,
                format="%.3f",
                key=f"limite_interno_inferior_{clave}",
            )

        mostrar_superior = st.toggle(
            "Añadir banda superior",
            value=False,
            key=f"mostrar_banda_superior_{clave}",
        )
        limite_superior = None
        if mostrar_superior:
            limite_superior = st.number_input(
                "Límite superior",
                value=superior_inicial,
                step=paso,
                format="%.3f",
                key=f"limite_interno_superior_{clave}",
            )

        if (
            limite_inferior is None
            and limite_superior is None
            and not tiene_bandas_normativas
        ):
            return None
        if (
            limite_inferior is not None
            and limite_superior is not None
            and limite_inferior >= limite_superior
        ):
            st.warning("El límite inferior debe ser menor que el superior.")
            return None
        return {
            "normativa": mostrar_normativa,
            "inferior": float(limite_inferior)
            if limite_inferior is not None
            else None,
            "superior": float(limite_superior)
            if limite_superior is not None
            else None,
        }

