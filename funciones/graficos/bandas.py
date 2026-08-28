from funciones.dominio.bandas import (
    obtener_banda_normativa,
    obtener_limites_activos,
    resaltar_valores_fuera_de_rango,
)

"""Bandas normativas e internas para gráficos operacionales."""

import streamlit as st










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

