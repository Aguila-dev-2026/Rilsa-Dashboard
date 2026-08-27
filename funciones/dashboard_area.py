import plotly.express as px
import streamlit as st

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro


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

    fig.update_layout(
        hovermode="x unified",
        dragmode="pan",
        margin=dict(l=10, r=10, t=55, b=10),
    )
    # El eje Y queda bloqueado: tanto el zoom como Pan actúan sobre el eje\n    # temporal (X), sin alterar la escala de los valores.
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    configuracion_grafico = {
        "displayModeBar": True,
        "scrollZoom": True,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "select2d",
            "lasso2d",
            "autoScale2d",
        ],
    }
    st.plotly_chart(fig, width="stretch", config=configuracion_grafico)
    st.subheader("Registros mostrados")
    st.dataframe(
        datos_filtrados.sort_values("Fecha", ascending=False),
        width="stretch",
        hide_index=True,
    )
