import plotly.express as px
import streamlit as st

from funciones.cargar_datos import cargar_datos_energia
from funciones.filtros import filtrar_por_fecha


def mostrar_energia():
    st.header("⚡ Energía")

    datos = cargar_datos_energia()
    datos_filtrados = filtrar_por_fecha(datos)

    if datos_filtrados.empty:
        st.warning("No hay datos para el período seleccionado.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("m³ tratados", round(datos_filtrados["M3"].sum(), 0))

    with col2:
        st.metric("kWh consumidos", round(datos_filtrados["KWH"].sum(), 0))

    with col3:
        st.metric(
            "kWh/m³",
            round(datos_filtrados["KWH_por_M3"].mean(), 2)
        )

    tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Gráficos", "📊 Resumen", "⚠️ Anomalías", "📋 Datos"]
)

    with tab1:

        st.subheader("m³ tratados")

        fig_m3 = px.line(
            datos_filtrados,
            x="Fecha",
            y="M3",
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_m3, width="stretch")

        st.subheader("Consumo eléctrico")

        fig_kwh = px.line(
            datos_filtrados,
            x="Fecha",
            y="KWH",
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_kwh, width="stretch")

        st.subheader("Eficiencia energética")

        fig_ratio = px.line(
            datos_filtrados,
            x="Fecha",
            y="KWH_por_M3",
            markers=True,
            template="plotly_white"
        )

        st.plotly_chart(fig_ratio, width="stretch")

    with tab2:

        resumen = datos_filtrados[
            ["M3", "KWH", "KWH_por_M3"]
        ].agg(
            ["sum", "mean", "max", "min"]
        ).T.reset_index()

        resumen.columns = [
            "Indicador",
            "Total",
            "Promedio",
            "Máximo",
            "Mínimo"
        ]

        st.dataframe(resumen, width="stretch")
    
    with tab3:

        st.subheader("Anomalías detectadas")

        anomalias = datos_filtrados[
            (datos_filtrados["M3"] <= 0)
            |
            (datos_filtrados["KWH"] <= 0)
            |
            (datos_filtrados["KWH_por_M3"] > 10)
        ].copy()

        if anomalias.empty:
            st.success("No se detectaron anomalías en el período seleccionado.")
        else:
            st.warning(f"Se detectaron {len(anomalias)} registros anómalos.")
            st.dataframe(anomalias, width="stretch")

    with tab4:

        st.dataframe(datos_filtrados, width="stretch")