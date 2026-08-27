import streamlit as st

from dashboards.fisico_quimico import mostrar_fisico_quimico

st.set_page_config(
    page_title="Planta RILES",
    layout="wide"
)

st.title("📊 Dashboard Operacional Planta RILES")

st.sidebar.title("Menú Planta RILES")
st.sidebar.caption("Importadores en reconstrucción: actualización deshabilitada.")

pagina = st.sidebar.radio(
    "Selecciona una sección",
    ["⚗️ Físico-químico"]
)

mostrar_fisico_quimico()
