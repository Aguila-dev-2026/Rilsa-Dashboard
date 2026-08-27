from pathlib import Path

import streamlit as st

from funciones.configuracion import obtener_configuracion

RAIZ_PROYECTO = Path(__file__).resolve().parent
CARPETA_DATOS = RAIZ_PROYECTO / "datos"
ENTRADA_FISICO_QUIMICO = CARPETA_DATOS / "Planilla Procesos RILES.xlsx"
ENTRADA_ANALISIS_AEROBICO = CARPETA_DATOS / "Análisis Planta Aeróbica.xlsx"

SECCIONES = {
    "⚗️ Físico-químico": ("Físico-químico", "⚗️ Físico-químico"),
    "🏭 Planta Alta": ("Planta Alta", "🏭 Planta Alta · Afluente"),
    "🧫 Planta Aeróbica": ("Planta Aeróbica", "🧫 Planta Aeróbica"),
    "💧 Efluente": ("Efluente", "💧 Efluente"),
}


st.set_page_config(page_title="Planta RILES", layout="wide")

from funciones.cargar_datos import hay_datos_operacionales

CONFIGURACION = obtener_configuracion()
if CONFIGURACION.es_nube and CONFIGURACION.faltantes_base_datos():
    st.error("El modo nube requiere configurar DATABASE_URL en Azure App Service.")
    st.stop()

st.title("📊 Dashboard Operacional Planta RILES")

st.sidebar.title("Menú Planta RILES")
pagina = st.sidebar.radio(
    "Selecciona una sección",
    list(SECCIONES),
)

st.sidebar.divider()
st.sidebar.subheader("Datos operacionales")
st.sidebar.caption(
    "Entorno: nube · PostgreSQL"
    if CONFIGURACION.es_nube
    else "Entorno: local · SQLite"
)

mensaje_actualizacion = st.session_state.pop("mensaje_actualizacion", None)
if mensaje_actualizacion:
    tipo_mensaje, texto_mensaje = mensaje_actualizacion
    getattr(st.sidebar, tipo_mensaje)(texto_mensaje)

mostrar_actualizacion = (
    not CONFIGURACION.es_nube or CONFIGURACION.sincronizacion_manual
)
if mostrar_actualizacion and st.sidebar.button(
    "Sincronizar SharePoint"
    if CONFIGURACION.es_nube
    else "Actualizar desde planillas",
    type="primary",
    use_container_width=True,
):
    try:
        with st.spinner("Validando y actualizando los datos..."):
            if CONFIGURACION.es_nube:
                from sincronizar_nube import sincronizar_datos_nube

                resultado = sincronizar_datos_nube()
            else:
                # OpenPyXL y los importadores se cargan solo cuando se solicitan.
                from actualizar_datos import actualizar_datos

                resultado = actualizar_datos()
    except Exception as error:
        st.sidebar.error(f"No fue posible actualizar los datos: {error}")
    else:
        st.cache_data.clear()
        if resultado["estado"] == "sin_cambios":
            mensaje = (
                "info",
                f"Las planillas no cambiaron. Se conservan "
                f"{resultado['registros']:,} registros.",
            )
        else:
            mensaje = (
                "success",
                f"Datos actualizados: {resultado['registros']:,} registros.",
            )
        st.session_state["mensaje_actualizacion"] = mensaje
        st.rerun()
elif CONFIGURACION.es_nube:
    st.sidebar.info("Datos centralizados y sincronizados desde SharePoint.")

def mostrar_ruta_origen(ruta):
    ruta = Path(ruta)
    return ruta.relative_to(Path.cwd()) if ruta.is_relative_to(Path.cwd()) else ruta


if CONFIGURACION.es_nube:
    st.sidebar.caption("Origen: SharePoint · almacenamiento: PostgreSQL")
else:
    st.sidebar.caption(
        "Orígenes:\n"
        f"- {mostrar_ruta_origen(ENTRADA_FISICO_QUIMICO)}\n"
        f"- {mostrar_ruta_origen(ENTRADA_ANALISIS_AEROBICO)}"
    )

try:
    datos_disponibles = hay_datos_operacionales()
except Exception as error:
    st.error(f"No fue posible comprobar la fuente de datos: {error}")
    st.stop()

# Se reemplaza en cada ejecución por la selección vigente del dashboard.
st.session_state.pop("datos_para_impresion", None)

if pagina == "⚗️ Físico-químico":
    if not datos_disponibles:
        st.header("⚗️ Físico-químico")
        st.info(
            "Aún no hay datos sincronizados en la fuente activa."
        )
    else:
        from dashboards.fisico_quimico import mostrar_fisico_quimico

        mostrar_fisico_quimico()
else:
    nombre_area, titulo = SECCIONES[pagina]
    if not datos_disponibles:
        st.header(titulo)
        st.info(
            "Aún no hay datos sincronizados para esta sección."
        )
    else:
        from funciones.dashboard_area import mostrar_dashboard_area

        mostrar_dashboard_area(nombre_area=nombre_area, titulo=titulo)

datos_para_impresion = st.session_state.get("datos_para_impresion")
if datos_para_impresion is not None:
    from funciones.informe_impresion import generar_informe_impresion

    st.html(generar_informe_impresion(datos_para_impresion))
