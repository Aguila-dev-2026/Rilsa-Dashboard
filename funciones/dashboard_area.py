import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro


CONFIGURACION_GRAFICO = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}


def mostrar_grafico_desplazable(fig, cantidad_dias):
    """Mantiene un ancho legible por día y añade scroll desde el día 32."""
    ancho_grafico = cantidad_dias * 48
    fig.update_layout(
        width=ancho_grafico,
        height=480,
        autosize=False,
    )

    grafico_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config=CONFIGURACION_GRAFICO,
    )
    html = f"""
    <!doctype html>
    <html>
    <head>
      <style>
        html, body {{
          margin: 0;
          padding: 0;
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
          width: {ancho_grafico}px;
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
        "template": "plotly_white",
        "title": f"{parametro} — evolución en el período seleccionado",
        "labels": {
            "Fecha": "Fecha",
            "Valor": f"Valor ({unidad})" if unidad else "Valor",
        },
    }

    if tipo_grafico == "Barras":
        fig = px.bar(datos_filtrados, **opciones)
        fig.update_traces(marker_color="#6d1f2b")
    else:
        fig = px.line(datos_filtrados, markers=True, **opciones)
        fig.update_traces(line_width=3, marker_size=7)

    fecha_inicio = datos_filtrados["Fecha"].min().normalize()
    fecha_fin = datos_filtrados["Fecha"].max().normalize()
    dias = pd.date_range(fecha_inicio, fecha_fin, freq="D")
    margen_lateral = pd.Timedelta(hours=12)
    dias_semana = ("L", "M", "M", "J", "V", "S", "D")
    etiquetas_dias = [
        (
            f"<span style='color:#2F6F9F'><b>{dia.day}<br>"
            f"{dias_semana[dia.weekday()]}</b></span>"
            if dia.weekday() >= 5
            else f"{dia.day}<br>{dias_semana[dia.weekday()]}"
        )
        for dia in dias
    ]

    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=10, r=10, t=55, b=90),
    )
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

    st.caption("El gráfico muestra todos los días del período seleccionado.")
    if len(dias) > 31:
        mostrar_grafico_desplazable(fig, len(dias))
    else:
        st.plotly_chart(
            fig,
            width="stretch",
            config=CONFIGURACION_GRAFICO,
        )

    st.subheader("Registros mostrados")
    st.dataframe(
        datos_filtrados.sort_values("Fecha", ascending=False),
        width="stretch",
        hide_index=True,
    )
