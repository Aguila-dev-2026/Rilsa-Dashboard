import pandas as pd
import streamlit as st

from funciones.cargar_datos import cargar_datos_contenedores
from funciones.filtros import filtrar_por_fecha


def mostrar_contenedores():
    st.header("🚛 Contenedores")

    datos = cargar_datos_contenedores()
    datos_filtrados = filtrar_por_fecha(datos)

    if datos_filtrados.empty:
        st.warning("No hay datos de contenedores para el período seleccionado.")
        return

    basura_si = (datos_filtrados["Basura_Retiro"] == "Sí").sum()
    basura_no = (datos_filtrados["Basura_Retiro"] == "No").sum()
    lodos_si = (datos_filtrados["Lodos_Retiro"] == "Sí").sum()
    lodos_no = (datos_filtrados["Lodos_Retiro"] == "No").sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Retiros basura", basura_si)

    with col2:
        st.metric("Días sin retiro basura", basura_no)

    with col3:
        st.metric("Retiros lodos", lodos_si)

    with col4:
        st.metric("Días sin retiro lodos", lodos_no)

    tab1, tab2, tab3 = st.tabs(["📊 Resumen", "⚠️ Alertas", "📋 Datos"])

    with tab1:
        st.subheader("Resumen de retiros")

        resumen = pd.DataFrame({
            "Tipo": ["Basura", "Lodos"],
            "Retiros": [basura_si, lodos_si],
            "Días sin retiro": [basura_no, lodos_no],
        })

        st.dataframe(resumen, width="stretch")

    with tab2:
        st.subheader("Días sin retiro registrado")

        alertas = datos_filtrados[
            (
                (datos_filtrados["Basura_Retiro"].isna())
                &
                (datos_filtrados["Lodos_Retiro"].isna())
            )
        ].copy()

        if alertas.empty:
            st.success("No hay días completamente sin registro.")
        else:
            st.warning(f"Hay {len(alertas)} días sin registro de retiro.")
            st.dataframe(alertas, width="stretch")

    with tab3:
        st.subheader("Datos de contenedores")
        st.dataframe(datos_filtrados, width="stretch")