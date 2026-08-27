from pathlib import Path

import streamlit as st

from dashboards.fisico_quimico import mostrar_fisico_quimico
from funciones.cargar_datos import CARPETA_GENERADOS
from funciones.dashboard_area import mostrar_dashboard_area
from importar import (
    ENTRADA_PREDETERMINADA as ENTRADA_FISICO_QUIMICO,
    importar_fisico_quimico,
)
from importar_analisis_aerobico import (
    ENTRADA_PREDETERMINADA as ENTRADA_ANALISIS_AEROBICO,
    importar_analisis_aerobico,
)


ARCHIVO_FISICO_QUIMICO = CARPETA_GENERADOS / "fisico_quimico.xlsx"
ARCHIVO_ANALISIS_AEROBICO = CARPETA_GENERADOS / "analisis_planta_aerobica.xlsx"

SECCIONES = {
    "⚗️ Físico-químico": ("Físico-químico", "⚗️ Físico-químico"),
    "🏭 Planta Alta": ("Planta Alta", "🏭 Planta Alta · Afluente"),
    "🧫 Planta Aeróbica": ("Planta Aeróbica", "🧫 Planta Aeróbica"),
    "💧 Efluente": ("Efluente", "💧 Efluente"),
}


st.set_page_config(page_title="Planta RILES", layout="wide")

st.title("📊 Dashboard Operacional Planta RILES")

st.sidebar.title("Menú Planta RILES")
pagina = st.sidebar.radio(
    "Selecciona una sección",
    list(SECCIONES),
)

st.sidebar.divider()
st.sidebar.subheader("Datos operacionales")

if st.sidebar.button("Actualizar desde planillas", type="primary", use_container_width=True):
    try:
        importar_fisico_quimico()
        importar_analisis_aerobico()
    except (FileNotFoundError, ValueError, OSError) as error:
        st.sidebar.error(f"No fue posible importar los datos: {error}")
    else:
        st.sidebar.success("Datos actualizados correctamente.")
        st.rerun()

def mostrar_ruta_origen(ruta):
    ruta = Path(ruta)
    return ruta.relative_to(Path.cwd()) if ruta.is_relative_to(Path.cwd()) else ruta


st.sidebar.caption(
    "Orígenes:\n"
    f"- {mostrar_ruta_origen(ENTRADA_FISICO_QUIMICO)}\n"
    f"- {mostrar_ruta_origen(ENTRADA_ANALISIS_AEROBICO)}"
)

if pagina == "⚗️ Físico-químico":
    if not ARCHIVO_FISICO_QUIMICO.exists():
        st.header("⚗️ Físico-químico")
        st.info(
            "Aún no hay datos importados. Usa «Actualizar desde planillas» "
            "en la barra lateral."
        )
    else:
        mostrar_fisico_quimico()
else:
    nombre_area, titulo = SECCIONES[pagina]
    if not ARCHIVO_ANALISIS_AEROBICO.exists():
        st.header(titulo)
        st.info(
            "Aún no hay datos importados para esta sección. "
            "Usa «Actualizar desde planillas» en la barra lateral."
        )
    else:
        mostrar_dashboard_area(nombre_area=nombre_area, titulo=titulo)
