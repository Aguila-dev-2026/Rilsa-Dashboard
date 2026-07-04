import plotly.express as px
import streamlit as st

from funciones.cargar_datos import cargar_datos_energia
from funciones.filtros import filtrar_por_fecha


def mostrar_prediccion():
    st.header("🤖 Predicción operacional")

    datos = cargar_datos_energia()
    datos_filtrados = filtrar_por_fecha(datos)

    if datos_filtrados.empty:
        st.warning("No hay datos disponibles para predicción.")
        return

    datos_filtrados = datos_filtrados.sort_values("Fecha").copy()

    datos_filtrados["M3_promedio_7d"] = (
        datos_filtrados["M3"].rolling(window=7, min_periods=1).mean()
    )

    datos_filtrados["KWH_promedio_7d"] = (
        datos_filtrados["KWH"].rolling(window=7, min_periods=1).mean()
    )

    datos_filtrados["KWH_M3_promedio_7d"] = (
        datos_filtrados["KWH_por_M3"].rolling(window=7, min_periods=1).mean()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("M3 promedio 7d", round(datos_filtrados["M3_promedio_7d"].iloc[-1], 2))

    with col2:
        st.metric("KWH promedio 7d", round(datos_filtrados["KWH_promedio_7d"].iloc[-1], 2))

    with col3:
        st.metric("KWH/m3 promedio 7d", round(datos_filtrados["KWH_M3_promedio_7d"].iloc[-1], 2))

    tab1, tab2 = st.tabs(["📈 Tendencias", "📋 Datos"])

    with tab1:
        st.subheader("Tendencia M3")

        fig_m3 = px.line(
            datos_filtrados,
            x="Fecha",
            y=["M3", "M3_promedio_7d"],
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_m3, width="stretch")

        st.subheader("Tendencia KWH")

        fig_kwh = px.line(
            datos_filtrados,
            x="Fecha",
            y=["KWH", "KWH_promedio_7d"],
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_kwh, width="stretch")

        st.subheader("Tendencia KWH/m3")

        fig_ratio = px.line(
            datos_filtrados,
            x="Fecha",
            y=["KWH_por_M3", "KWH_M3_promedio_7d"],
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_ratio, width="stretch")

    with tab2:
        st.dataframe(datos_filtrados, width="stretch")