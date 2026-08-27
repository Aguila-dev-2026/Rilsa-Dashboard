import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro
from funciones.tema import tema_oscuro


CONFIGURACION_GRAFICO = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}

VINO = "#6D1F2B"
VINO_OSCURO = "#48121A"
COBRE = "#B36F3D"
TINTA = "#282422"
LINEA_SUAVE = "rgba(117,110,103,0.16)"


def aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad):
    oscuro = tema_oscuro()
    tinta = "#F4F0E9" if oscuro else "#282422"
    texto_eje = "#C8BDB3" if oscuro else "#5F5852"
    texto_secundario = "#B9AFA5" if oscuro else "#756E67"
    linea_eje = "rgba(244,240,233,0.22)" if oscuro else "rgba(117,110,103,0.28)"
    cuadricula = "rgba(244,240,233,0.10)" if oscuro else LINEA_SUAVE
    vino = "#C65C6B" if oscuro else VINO
    vino_oscuro = "#7A2634" if oscuro else VINO_OSCURO
    cobre = "#D99A68" if oscuro else COBRE
    borde_marcador = "#1F1B19" if oscuro else "#FFFDF8"
    relleno = "rgba(198,92,107,0.11)" if oscuro else "rgba(109,31,43,0.07)"

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
                color=vino,
                line=dict(color=vino_oscuro, width=0.7),
            ),
            opacity=0.94,
        )
    else:
        fig.update_traces(
            line=dict(color=vino, width=3),
            marker=dict(
                color=cobre,
                size=7,
                line=dict(color=borde_marcador, width=1.5),
            ),
            fill="tozeroy",
            fillcolor=relleno,
        )

    fig.update_layout(
        template="plotly_dark" if oscuro else "plotly_white",
        title=dict(
            text=f"<b>{parametro}</b><br><sup>Evolución del período seleccionado</sup>",
            x=0.015,
            xanchor="left",
            font=dict(size=21, color=tinta),
        ),
        font=dict(
            family='"Source Sans Pro", sans-serif',
            color=tinta,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=vino_oscuro,
            bordercolor=vino_oscuro,
            font=dict(color="#FFFFFF", size=13),
        ),
        hovermode="x unified",
        bargap=0.28,
        barcornerradius=6,
        margin=dict(l=82, r=18, t=78, b=92),
    )
    fig.update_xaxes(
        title=None,
        showgrid=False,
        showline=True,
        linecolor=linea_eje,
        linewidth=1,
        tickfont=dict(size=12, color=texto_eje),
    )
    fig.update_yaxes(
        title=f"Valor ({unidad})" if unidad else "Valor",
        showgrid=True,
        gridcolor=cuadricula,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=12, color=texto_eje),
        title_font=dict(size=12, color=texto_secundario),
        title_standoff=22,
        automargin=True,
    )

def mostrar_grafico_desplazable(fig, cantidad_dias):
    """Replica el tema nativo y añade scroll únicamente desde el día 32."""
    ancho_grafico = cantidad_dias * 48

    fig.update_layout(
        width=ancho_grafico,
        height=480,
        autosize=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    grafico_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config=CONFIGURACION_GRAFICO,
    )
    ancho_contenido = f"{ancho_grafico}px"
    desbordamiento = "auto"

    html = f"""
    <!doctype html>
    <html>
    <head>
      <style>
        html, body {{
          width: 100%;
          margin: 0;
          padding: 0;
          overflow: hidden;
        }}
        .contenedor-grafico {{
          width: 100%;
          overflow-x: {desbordamiento};
          overflow-y: hidden;
          padding-bottom: 8px;
          scrollbar-gutter: stable;
        }}
        .contenido-grafico {{
          width: {ancho_contenido};
          min-width: {ancho_contenido};
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
    tabla = (
        datos.sort_values("Fecha", ascending=False)
        .rename(
            columns={
                "Area": "Área",
                "Parametro": "Parámetro",
            }
        )
        .reset_index(drop=True)
    )

    modo_oscuro = tema_oscuro()

    if modo_oscuro:
        fondo_par = "#171514"
        fondo_impar = "#211D1B"
        texto = "#F4F0E9"
        encabezado = "#48121A"
        borde = "#3A3430"
        valor = "#D99A68"
    else:
        fondo_par = "#FFFDF8"
        fondo_impar = "#F7F2EC"
        texto = "#282422"
        encabezado = VINO_OSCURO
        borde = "#E5DED5"
        valor = VINO

    def alternar_filas(fila):
        fondo = fondo_par if fila.name % 2 == 0 else fondo_impar
        return [f"background-color: {fondo}; color: {texto}"] * len(fila)

    return (
        tabla.style
        .apply(alternar_filas, axis=1)
        .set_properties(
            subset=["Valor"],
            **{
                "color": valor,
                "font-weight": "700",
            },
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", encabezado),
                        ("color", "#FFFFFF"),
                        ("font-weight", "700"),
                        ("border", "none"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("border-color", borde),
                        ("padding", "0.65rem"),
                    ],
                },
            ]
        )
        .format({"Valor": "{:,.2f}"}, na_rep="—")
    )


def mostrar_dashboard_area(nombre_area, titulo):
    st.header(titulo)

    datos = cargar_datos_operacionales()
    datos = datos[datos["Area"] == nombre_area].copy()

    if datos.empty:
        st.warning(f"No hay datos disponibles para {nombre_area}.")
        return

    datos = filtrar_por_fecha(datos)
    if datos.empty:
        st.info("No hay datos para el rango de fechas seleccionado.")
        return

    datos_filtrados = filtrar_por_parametro(datos)
    if datos_filtrados.empty:
        st.info("No hay datos para el parámetro seleccionado.")
        return

    tipo_grafico = st.sidebar.selectbox(
        "Tipo de gráfico",
        ["Líneas", "Barras"],
        key="tipo_grafico",
    )

    datos_filtrados = datos_filtrados.sort_values("Fecha")
    parametro = datos_filtrados["Parametro"].iat[0]
    unidad = (
        datos_filtrados["Unidad"].dropna().iloc[0]
        if datos_filtrados["Unidad"].notna().any()
        else ""
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros", len(datos_filtrados))
    col2.metric("Promedio", f"{datos_filtrados['Valor'].mean():.2f} {unidad}".strip())
    col3.metric(
        "Último valor",
        f"{datos_filtrados['Valor'].iloc[-1]:.2f} {unidad}".strip(),
    )

    opciones = {
        "x": "Fecha",
        "y": "Valor",
        "template": "plotly_dark" if tema_oscuro() else "plotly_white",
        "title": f"{parametro} — evolución en el período seleccionado",
        "labels": {
            "Fecha": "Fecha",
            "Valor": f"Valor ({unidad})" if unidad else "Valor",
        },
    }

    if tipo_grafico == "Barras":
        fig = px.bar(datos_filtrados, **opciones)
    else:
        datos_linea = datos_filtrados[
            datos_filtrados["Valor"].notna()
            & datos_filtrados["Valor"].ne(0)
        ].copy()

        if datos_linea.empty:
            st.info("No hay valores distintos de cero para mostrar en el gráfico lineal.")
            return

        fig = px.line(datos_linea, markers=True, **opciones)

    aplicar_estilo_premium(fig, tipo_grafico, parametro, unidad)

    fecha_inicio = datos_filtrados["Fecha"].min().normalize()
    fecha_fin = datos_filtrados["Fecha"].max().normalize()
    dias = pd.date_range(fecha_inicio, fecha_fin, freq="D")
    margen_lateral = pd.Timedelta(hours=12)
    dias_semana = ("L", "M", "M", "J", "V", "S", "D")
    azul_fin_semana = "#72B7E3" if tema_oscuro() else "#2F6F9F"
    etiquetas_dias = [
        (
            f"<span style='color:{azul_fin_semana}'><b>{dia.day}<br>"
            f"{dias_semana[dia.weekday()]}</b></span>"
            if dia.weekday() >= 5
            else f"{dia.day}<br>{dias_semana[dia.weekday()]}"
        )
        for dia in dias
    ]

    fig.update_xaxes(
        range=[
            fecha_inicio - margen_lateral,
            fecha_fin + margen_lateral,
        ],
        tickmode="array",
        tickvals=dias,
        ticktext=etiquetas_dias,
        tickangle=0,
        fixedrange=True,
        automargin=True,
    )
    fig.update_yaxes(fixedrange=True)

    with st.container(border=True):
        st.caption("VISTA TEMPORAL · TODOS LOS DÍAS DEL PERÍODO")
        if len(dias) > 31:
            mostrar_grafico_desplazable(fig, len(dias))
        else:
            st.plotly_chart(
                fig,
                width="stretch",
                config=CONFIGURACION_GRAFICO,
                theme=None,
            )

    st.subheader("Registros mostrados")
    with st.container(border=True):
        st.caption("DETALLE DE MEDICIONES · ORDEN CRONOLÓGICO DESCENDENTE")
        st.dataframe(
            preparar_tabla_premium(datos_filtrados),
            width="stretch",
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha",
                    format="DD/MM/YYYY",
                ),
                "Valor": st.column_config.NumberColumn(
                    "Valor",
                    format="%.2f",
                ),
            },
        )
