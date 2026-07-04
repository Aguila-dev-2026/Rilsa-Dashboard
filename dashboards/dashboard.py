import plotly.express as px
import streamlit as st

from funciones.cargar_datos import cargar_datos_operacionales
from funciones.filtros import filtrar_por_fecha, filtrar_por_parametro


def filtrar_por_area(datos):
    areas = sorted(datos["Area"].dropna().unique())

    areas_sel = st.sidebar.multiselect(
        "Área",
        areas,
        default=areas
    )

    if not areas_sel:
        st.info("Selecciona al menos un área.")
        return datos.iloc[0:0].copy()

    return datos[
        datos["Area"].isin(areas_sel)
    ].copy()


def mostrar_dashboard():
    datos = cargar_datos_operacionales()

    st.sidebar.header("Filtros")

    datos = filtrar_por_fecha(datos)
    datos = filtrar_por_area(datos)
    datos_filtrados = filtrar_por_parametro(datos)

    if datos_filtrados.empty:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Registros", len(datos_filtrados))

    with col2:
        st.metric("Áreas", datos_filtrados["Area"].nunique())

    with col3:
        st.metric("Parámetros", datos_filtrados["Parametro"].nunique())

    with col4:
        st.metric("Promedio", round(datos_filtrados["Valor"].mean(), 2))

    tab1, tab2 = st.tabs(["📈 Gráfico", "📋 Datos"])

    with tab1:
        st.subheader("Tendencia operacional")

        fig = px.line(
            datos_filtrados,
            x="Fecha",
            y="Valor",
            color="Parametro",
            facet_row="Area",
            markers=True,
            template="plotly_white",
            labels={
                "Fecha": "Fecha",
                "Valor": "Valor",
                "Parametro": "Parámetro"
            }
        )

        fig.update_layout(
            height=max(600, datos_filtrados["Area"].nunique() * 300)
        )

        fig.update_yaxes(matches=None)

        st.plotly_chart(fig, width="stretch")

    with tab2:
        st.subheader("Datos filtrados")

        columnas_visibles = [
            "Fecha",
            "Area",
            "Parametro",
            "Valor",
            "Unidad"
        ]

        tabla = datos_filtrados[
            [c for c in columnas_visibles if c in datos_filtrados.columns]
        ]

        st.dataframe(tabla, width="stretch")

        csv = tabla.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="⬇️ Descargar datos filtrados",
            data=csv,
            file_name="datos_filtrados_planta_riles.csv",
            mime="text/csv"
        )