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
    datos_filtrados = filtrar_por_parametro(datos)

    if datos_filtrados.empty:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Registros", len(datos_filtrados))

    with col2:
        st.metric("Parámetros", datos_filtrados["Parametro"].nunique())

    with col3:
        st.metric("Promedio general", round(datos_filtrados["Valor"].mean(), 2))

    fig = px.line(
        datos_filtrados,
        x="Fecha",
        y="Valor",
        color="Parametro",
        markers=True,
        template="plotly_white",
        labels={
            "Fecha": "Fecha",
            "Valor": "Valor",
            "Parametro": "Parámetro"
        }
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Datos filtrados")
    st.dataframe(datos_filtrados, width="stretch")