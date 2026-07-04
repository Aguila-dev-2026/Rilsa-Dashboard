import pandas as pd
import streamlit as st

from funciones.cargar_datos import (
    cargar_datos_energia,
    cargar_datos_quimicos
)
from funciones.filtros import filtrar_por_fecha


def mostrar_indicadores():
    st.header("📈 Indicadores Operacionales")

    energia = cargar_datos_energia()
    quimicos = cargar_datos_quimicos()

    energia = filtrar_por_fecha(energia)

    if energia.empty:
        st.warning("No hay datos de energía para el período seleccionado.")
        return

    fecha_inicio = energia["Fecha"].min()
    fecha_fin = energia["Fecha"].max()

    quimicos = quimicos[
        (quimicos["Fecha"] >= fecha_inicio)
        &
        (quimicos["Fecha"] <= fecha_fin)
    ].copy()

    if quimicos.empty:
        st.warning("No hay datos de químicos para el período seleccionado.")
        return

    energia_diaria = energia.groupby("Fecha", as_index=False).agg({
        "M3": "sum",
        "KWH": "sum"
    })

    quimicos_diarios = quimicos.groupby("Fecha", as_index=False).agg({
        "Catiónico": "sum",
        "Aniónico": "sum",
        "PAC": "sum",
        "Cal": "sum"
    })

    datos = pd.merge(
        energia_diaria,
        quimicos_diarios,
        on="Fecha",
        how="inner"
    )

    if datos.empty:
        st.warning("No hay fechas comunes entre energía y químicos.")
        return

    datos["KWH_por_M3"] = datos["KWH"] / datos["M3"]
    datos["PAC_por_M3"] = datos["PAC"] / datos["M3"]
    datos["Cationico_por_M3"] = datos["Catiónico"] / datos["M3"]
    datos["Anionico_por_M3"] = datos["Aniónico"] / datos["M3"]
    datos["Cal_por_M3"] = datos["Cal"] / datos["M3"]

    indicadores = [
        "KWH_por_M3",
        "PAC_por_M3",
        "Cationico_por_M3",
        "Anionico_por_M3",
        "Cal_por_M3",
    ]

    datos[indicadores] = datos[indicadores].replace(
        [float("inf"), -float("inf")],
        pd.NA
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("kWh/m³", round(datos["KWH_por_M3"].mean(), 2))

    with col2:
        st.metric("PAC/m³", round(datos["PAC_por_M3"].mean(), 2))

    with col3:
        st.metric("Catiónico/m³", round(datos["Cationico_por_M3"].mean(), 3))

    with col4:
        st.metric("Aniónico/m³", round(datos["Anionico_por_M3"].mean(), 3))

    with col5:
        st.metric("Cal/m³", round(datos["Cal_por_M3"].mean(), 2))

    tab1, tab2 = st.tabs(["📊 Indicadores", "📋 Datos"])

    with tab1:
        st.subheader("Indicadores diarios")
        st.line_chart(datos.set_index("Fecha")[indicadores])

    with tab2:
        st.subheader("Datos consolidados")
        st.dataframe(datos, width="stretch")