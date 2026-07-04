import os
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner="Cargando datos generados...")
def cargar_datos_operacionales():
    archivos = [
        "datos_generados/fisico_quimico.xlsx",
        "datos_generados/aerobico.xlsx"
    ]

    dataframes = []

    for archivo in archivos:
        if os.path.exists(archivo):
            df = pd.read_excel(archivo)
            dataframes.append(df)

    if not dataframes:
        st.error("No existen archivos generados. Ejecuta primero: python importar.py")
        st.stop()

    datos = pd.concat(dataframes, ignore_index=True)

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
    datos["Valor"] = pd.to_numeric(datos["Valor"], errors="coerce")

    datos = datos.dropna(subset=["Fecha", "Valor"])

    return datos


@st.cache_data(show_spinner="Cargando datos de químicos...")
def cargar_datos_quimicos():
    archivo = "datos_generados/quimicos.xlsx"

    if not os.path.exists(archivo):
        st.error("No existe quimicos.xlsx. Ejecuta primero: python importar.py")
        st.stop()

    datos = pd.read_excel(archivo)

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")

    for columna in ["Catiónico", "Aniónico", "PAC", "Cal"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    datos = datos.dropna(subset=["Fecha"])

    return datos

@st.cache_data(show_spinner="Cargando datos de energía...")
def cargar_datos_energia():
    archivo = "datos_generados/energia.xlsx"

    if not os.path.exists(archivo):
        st.error("No existe energia.xlsx. Ejecuta primero: python importar.py")
        st.stop()

    datos = pd.read_excel(archivo)

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")

    for columna in ["M3", "KWH", "KWH_por_M3"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    datos = datos.dropna(subset=["Fecha"])

    return datos

@st.cache_data(show_spinner="Cargando datos de contenedores...")
def cargar_datos_contenedores():
    archivo = "datos_generados/contenedores.xlsx"

    if not os.path.exists(archivo):
        st.error(
            "No existe contenedores.xlsx. Ejecuta primero: python importar.py"
        )
        st.stop()

    datos = pd.read_excel(archivo)

    datos["Fecha"] = pd.to_datetime(
        datos["Fecha"],
        errors="coerce"
    )

    return datos