"""Renderizado y estilos comunes de gráficos y tablas."""

import json
import math

import pandas as pd
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

SEPARACION_MINIMA_FECHAS_PX = 24
MARGEN_HORIZONTAL_GRAFICO_PX = 100
ANCHO_MINIMO_GRAFICO_PX = 320

_SCRIPT_TEMA_CLIENTE = r"""
<script>
(() => {
  const paletas = __PALETAS__;
  let temaOscuroAnterior = null;
  let temporizador = null;

  function leerColorFondo() {
    const documentoPadre = window.parent.document;
    const candidatos = [
      documentoPadre.querySelector('[data-testid="stAppViewContainer"]'),
      documentoPadre.querySelector('.stApp'),
      documentoPadre.body,
      documentoPadre.documentElement,
    ];

    for (const elemento of candidatos) {
      if (!elemento) continue;
      const color = window.parent.getComputedStyle(elemento).backgroundColor;
      const componentes = color.match(/[\d.]+/g);
      if (!componentes || componentes.length < 3) continue;
      const [rojo, verde, azul, alfa = 1] = componentes.map(Number);
      if (alfa === 0) continue;
      return [rojo, verde, azul];
    }
    return null;
  }

  function detectarTemaOscuro() {
    try {
      const color = leerColorFondo();
      if (color) {
        const [rojo, verde, azul] = color;
        const luminancia = 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul;
        return luminancia < 128;
      }
    } catch (_error) {
      // Algunos navegadores aíslan el iframe; se usa la preferencia del sistema.
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function aplicarTema(forzar = false) {
    const grafico = document.querySelector('.plotly-graph-div');
    if (!grafico || !window.Plotly || !grafico._fullLayout) return false;

    const oscuro = detectarTemaOscuro();
    if (!forzar && oscuro === temaOscuroAnterior) return true;
    temaOscuroAnterior = oscuro;
    const paleta = oscuro ? paletas.oscura : paletas.clara;
    const esquema = oscuro ? 'dark' : 'light';
    document.documentElement.style.colorScheme = esquema;
    document.body.style.colorScheme = esquema;

    window.Plotly.relayout(grafico, {
      'font.color': paleta.texto,
      'title.font.color': paleta.texto,
      'legend.font.color': paleta.texto,
      'xaxis.tickfont.color': paleta.texto_eje,
      'xaxis.linecolor': paleta.texto_eje,
      'xaxis.tickcolor': paleta.texto_eje,
      'yaxis.tickfont.color': paleta.texto_eje,
      'yaxis.title.font.color': paleta.texto_eje,
      'yaxis.gridcolor': paleta.cuadricula,
    });
    return true;
  }

  function iniciar(intentos = 0) {
    if (!aplicarTema(true)) {
      if (intentos < 120) {
        window.requestAnimationFrame(() => iniciar(intentos + 1));
      }
      return;
    }
    temporizador = window.setInterval(() => aplicarTema(false), 500);
  }

  window.addEventListener('beforeunload', () => {
    if (temporizador !== null) window.clearInterval(temporizador);
  });
  iniciar();
})();
</script>
"""


def _script_tema_cliente():
    """Genera el detector de tema del navegador con la paleta centralizada."""
    paletas = {
        "clara": paleta_grafico(False),
        "oscura": paleta_grafico(True),
    }
    return _SCRIPT_TEMA_CLIENTE.replace(
        "__PALETAS__",
        json.dumps(paletas, ensure_ascii=False),
    )


def calcular_ancho_minimo_grafico(cantidad_periodos):
    """Reserva al menos 24 px entre fechas, además de los márgenes del gráfico."""
    intervalos = max(int(cantidad_periodos) - 1, 0)
    return max(
        ANCHO_MINIMO_GRAFICO_PX,
        intervalos * SEPARACION_MINIMA_FECHAS_PX + MARGEN_HORIZONTAL_GRAFICO_PX,
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


def aplicar_margen_superior_eje_y(
    fig,
    datos,
    tipo_grafico,
    limites_activos=(None, None),
    columna_medicion=None,
):
    """Añade un intervalo de eje sobre el mayor valor visible o normativo."""
    if datos is None or "Valor" not in datos.columns:
        return

    serie = pd.to_numeric(datos["Valor"], errors="coerce")
    if columna_medicion and columna_medicion in datos.columns:
        serie = serie[datos[columna_medicion].astype(bool).to_numpy()]
    serie = serie.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if serie.empty:
        return

    minimo_dato = float(serie.min())
    maximo_dato = float(serie.max())
    limite_inferior_banda, limite_superior_banda = limites_activos
    maximo_referencia = maximo_dato
    if limite_superior_banda is not None:
        maximo_referencia = max(maximo_referencia, float(limite_superior_banda))

    minimo_referencia = minimo_dato
    if limite_inferior_banda is not None:
        minimo_referencia = min(minimo_referencia, float(limite_inferior_banda))
    if tipo_grafico == "Barras":
        minimo_referencia = min(0.0, minimo_referencia)

    amplitud = max(maximo_referencia - minimo_referencia, 0.0)
    paso_aproximado = max(amplitud / 5, abs(maximo_referencia) / 10, 0.01)
    magnitud = 10 ** math.floor(math.log10(paso_aproximado))
    factor = paso_aproximado / magnitud
    if factor <= 1:
        factor_nice = 1
    elif factor <= 2:
        factor_nice = 2
    elif factor <= 5:
        factor_nice = 5
    else:
        factor_nice = 10
    intervalo = factor_nice * magnitud
    limite_superior = maximo_referencia + intervalo

    fig.update_yaxes(
        range=[minimo_referencia, limite_superior],
        dtick=intervalo,
    )

def mostrar_grafico_desplazable(fig, cantidad_periodos):
    """Renderiza un gráfico fluido con al menos 24 px entre fechas."""
    ancho_minimo = calcular_ancho_minimo_grafico(cantidad_periodos)
    oscuro = tema_nativo_oscuro()
    paleta = paleta_grafico(oscuro)
    fig.update_layout(
        template=paleta["template"],
        font=dict(
            family='"Source Sans Pro", sans-serif',
            color=paleta["texto"],
        ),
        height=480,
        autosize=True,
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
        config=CONFIGURACION_GRAFICO,
    )
    ancho_minimo_css = f"{ancho_minimo}px"
    script_tema = _script_tema_cliente()
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
          touch-action: pan-x pan-y;
          -webkit-overflow-scrolling: touch;
          padding-bottom: 8px;
          scrollbar-gutter: stable;
        }}
        .contenido-grafico {{
          width: max(100%, {ancho_minimo_css});
          min-width: {ancho_minimo_css};
        }}
        .contenido-grafico .plotly-graph-div {{
          width: 100% !important;
          min-width: {ancho_minimo_css} !important;
        }}
        .js-plotly-plot .hoverlayer .axistext {{
          display: none !important;
        }}
        .js-plotly-plot .modebar-container,
        .js-plotly-plot .modebar {{
          opacity: 1 !important;
          visibility: visible !important;
        }}
        /* La barra queda fija al viewport del iframe, no al lienzo ancho que
           se desplaza horizontalmente para conservar las fechas legibles. */
        .js-plotly-plot .modebar-container {{
          position: fixed !important;
          top: 8px !important;
          right: 10px !important;
          z-index: 20 !important;
        }}
      </style>
    </head>
    <body>
      <div class="contenedor-grafico">
        <div class="contenido-grafico">{grafico_html}</div>
      </div>
      {script_tema}
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
