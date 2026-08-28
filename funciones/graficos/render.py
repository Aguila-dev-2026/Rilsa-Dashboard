"""Renderizado y estilos comunes de gráficos y tablas."""

import streamlit.components.v1 as components

from funciones.tablas import preparar_columnas_visibles
from funciones.ui.tema import (
    AZUL_BORDE,
    AZUL_CIELO,
    AZUL_CORPORATIVO,
    CONFIGURACION_GRAFICO,
    paleta_grafico,
    tema_nativo_oscuro,
)


def aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad):
    """Aplica el estilo visual compartido a un gráfico Plotly."""
    borde_marcador = paleta_grafico(tema_nativo_oscuro())["borde_marcador"]
    etiqueta_valor = f"%{{y:,.2f}} {unidad}".strip()
    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d/%m/%Y}</b><br>"
            f"{parametro}: {etiqueta_valor}<extra></extra>"
        )
    )
    if tipo_grafico == "Barras":
        fig.update_traces(
            marker=dict(
                color=AZUL_CORPORATIVO,
                line=dict(color=AZUL_BORDE, width=0.7),
            ),
            opacity=0.94,
        )
    else:
        fig.update_traces(
            line=dict(color=AZUL_CORPORATIVO, width=3.2),
            marker=dict(
                color=AZUL_CIELO,
                size=7,
                line=dict(color=borde_marcador, width=1.4),
            ),
            fill="tozeroy",
            fillcolor="rgba(20,126,175,0.10)",
        )
    fig.update_layout(
        title=dict(
            text=f"<b>{parametro}</b>",
            x=0.015,
            xanchor="left",
            font=dict(size=21),
        ),
        font=dict(family='"Source Sans Pro", sans-serif'),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#40566C",
            bordercolor="#172C50",
            font=dict(color="#FFFFFF", size=13),
            align="left",
            namelength=-1,
        ),
        hovermode="x unified",
        bargap=0.28,
        barcornerradius=6,
        margin=dict(l=82, r=18, t=78, b=92),
    )
    fig.update_xaxes(
        title=None,
        # Plotly restablece el encabezado automático si recibe una cadena vacía.
        # El espacio de ancho cero lo oculta sin perder el hover unificado.
        unifiedhovertitle_text="\u200b",
        showgrid=False,
        showline=True,
        linewidth=1,
        tickfont=dict(size=12),
    )
    fig.update_yaxes(
        title=f"Valor ({unidad})" if unidad else "Valor",
        showgrid=True,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=12),
        title_font=dict(size=12),
        title_standoff=22,
        automargin=True,
    )


def mostrar_grafico_desplazable(fig, cantidad_periodos):
    """Renderiza un gráfico con scroll horizontal y tema nativo."""
    ancho_grafico = cantidad_periodos * 24
    oscuro = tema_nativo_oscuro()
    paleta = paleta_grafico(oscuro)
    fig.update_layout(
        template=paleta["template"],
        font=dict(
            family='"Source Sans Pro", sans-serif',
            color=paleta["texto"],
        ),
        width=ancho_grafico,
        height=480,
        autosize=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickfont=dict(size=12, color=paleta["texto_eje"]))
    fig.update_yaxes(
        tickfont=dict(size=12, color=paleta["texto_eje"]),
        title_font=dict(size=12, color=paleta["texto_eje"]),
        gridcolor=paleta["cuadricula"],
    )
    grafico_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={**CONFIGURACION_GRAFICO, "responsive": False},
    )
    ancho_contenido = f"{ancho_grafico}px"
    html = f"""
    <!doctype html>
    <html>
    <head>
      <style>
        html, body {{
          width: 100%;
          margin: 0;
          padding: 0;
          background: transparent;
          color-scheme: {{"dark" if oscuro else "light"}};
          overflow: hidden;
        }}
        .contenedor-grafico {{
          width: 100%;
          overflow-x: auto;
          overflow-y: hidden;
          padding-bottom: 8px;
          scrollbar-gutter: stable;
        }}
        .contenido-grafico {{
          width: {ancho_contenido};
          min-width: {ancho_contenido};
        }}
        .contenido-grafico .plotly-graph-div {{
          width: {ancho_contenido} !important;
          min-width: {ancho_contenido} !important;
        }}
        .js-plotly-plot .hoverlayer .axistext {{
          display: none !important;
        }}
      </style>
    </head>
    <body>
      <div class="contenedor-grafico">
        <div class="contenido-grafico">{grafico_html}</div>
      </div>
    </body>
    </html>
    """
    components.html(html, height=530, scrolling=False)


def preparar_tabla_premium(datos):
    """Prepara la tabla visible con orden y formato comunes."""
    tabla = (
        preparar_columnas_visibles(datos)
        .sort_values("Fecha", ascending=False)
        .rename(columns={"Area": "Área", "Parametro": "Parámetro"})
        .reset_index(drop=True)
    )
    return (
        tabla.style
        .set_properties(subset=["Valor"], **{"font-weight": "700"})
        .format({"Valor": "{:,.2f}"}, na_rep="—")
    )
