import plotly.express as px
import streamlit as st

from funciones.cargar_datos import cargar_datos_quimicos
from funciones.filtros import (
    filtrar_por_fecha,
    filtrar_por_quimicos
)


def mostrar_quimicos():
    st.header("🧪 Químicos")

    datos = cargar_datos_quimicos()
    datos_filtrados = filtrar_por_fecha(datos)

    if datos_filtrados.empty:
        st.warning("No hay datos de químicos para el período seleccionado.")
        return

    quimicos = ["Catiónico", "Aniónico", "PAC", "Cal"]

    quimicos_sel = filtrar_por_quimicos(
        datos_filtrados,
        quimicos
    )

    if not quimicos_sel:
        return

    totales = datos_filtrados[quimicos_sel].sum()

    columnas = st.columns(len(quimicos_sel))

    for columna, quimico in zip(columnas, quimicos_sel):
        with columna:
            st.metric(quimico, round(totales[quimico], 2))

    tab1, tab2, tab3 = st.tabs(["📈 Gráficos", "📊 Resumen", "📋 Datos"])

    with tab1:
        st.subheader("Consumo diario de químicos")

        datos_largos = datos_filtrados.melt(
            id_vars=["Fecha", "Mes", "Dia"],
            value_vars=quimicos_sel,
            var_name="Químico",
            value_name="Consumo"
        )

        fig_diario = px.line(
            datos_largos,
            x="Fecha",
            y="Consumo",
            color="Químico",
            markers=True,
            template="plotly_white",
            labels={
                "Fecha": "Fecha",
                "Consumo": "Consumo",
                "Químico": "Químico"
            }
        )

        st.plotly_chart(fig_diario, width="stretch")

        st.subheader("Consumo acumulado")

        datos_acumulados = datos_filtrados.copy()

        for quimico in quimicos:
            datos_acumulados[quimico] = (
                datos_acumulados[quimico].fillna(0).cumsum()
            )

        datos_acumulados_largos = datos_acumulados.melt(
            id_vars=["Fecha", "Mes", "Dia"],
            value_vars=quimicos_sel,
            var_name="Químico",
            value_name="Consumo acumulado"
        )

        fig_acumulado = px.line(
            datos_acumulados_largos,
            x="Fecha",
            y="Consumo acumulado",
            color="Químico",
            markers=True,
            template="plotly_white",
            labels={
                "Fecha": "Fecha",
                "Consumo acumulado": "Consumo acumulado",
                "Químico": "Químico"
            }
        )

        st.plotly_chart(fig_acumulado, width="stretch")

    with tab2:
        st.subheader("Resumen por químico")

        resumen = datos_filtrados[quimicos_sel].agg(
            ["sum", "mean", "max", "min"]
        ).T.reset_index()

        resumen.columns = [
            "Químico",
            "Total",
            "Promedio diario",
            "Máximo diario",
            "Mínimo diario"
        ]

        st.dataframe(resumen, width="stretch")

    with tab3:
        st.subheader("Datos de químicos")
        st.dataframe(datos_filtrados, width="stretch")