import streamlit as st

from dashboards.dashboard import mostrar_dashboard
from dashboards.fisico_quimico import mostrar_fisico_quimico
from dashboards.aerobico import mostrar_aerobico
from dashboards.quimicos import mostrar_quimicos
from dashboards.energia import mostrar_energia
from dashboards.contenedores import mostrar_contenedores
from dashboards.indicadores import mostrar_indicadores
from dashboards.prediccion import mostrar_prediccion

st.set_page_config(
    page_title="Planta RILES",
    layout="wide"
)

st.title("📊 Dashboard Operacional Planta RILES")

if st.button("🔄 Actualizar datos desde Excel"):
    import importar
    importar.main()
    st.cache_data.clear()
    st.success("Datos actualizados correctamente.")
    st.rerun()

st.sidebar.title("Menú Planta RILES")

pagina = st.sidebar.radio(
    "Selecciona una sección",
    [
        "📊 Dashboard",
        "⚗️ Físico-químico",
        "🦠 Aeróbico",
        "🧪 Químicos",
        "⚡ Energía",
        "🚛 Contenedores",
        "📈 Indicadores",
        "🤖 Predicción",
    ]
)

if pagina == "📊 Dashboard":
    mostrar_dashboard()
elif pagina == "⚗️ Físico-químico":
    mostrar_fisico_quimico()
elif pagina == "🦠 Aeróbico":
    mostrar_aerobico()
elif pagina == "🧪 Químicos":
    mostrar_quimicos()
elif pagina == "⚡ Energía":
    mostrar_energia()
elif pagina == "📈 Indicadores":
    mostrar_indicadores()

else:
    st.info(f"Sección en desarrollo: {pagina}")

    