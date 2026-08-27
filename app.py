from pathlib import Path

import streamlit as st

from funciones.configuracion import obtener_configuracion

RAIZ_PROYECTO = Path(__file__).resolve().parent
CARPETA_DATOS = RAIZ_PROYECTO / "datos"
ENTRADA_FISICO_QUIMICO = CARPETA_DATOS / "Planilla Procesos RILES.xlsx"
ENTRADA_ANALISIS_AEROBICO = CARPETA_DATOS / "Análisis Planta Aeróbica.xlsx"

SECCIONES = {
    "⚗️ Físico-químico": ("Físico-químico", "⚗️ Físico-químico"),
    "🚛 Planta Alta": ("Planta Alta", "🚛 Planta Alta · Afluente"),
    "🦠 Planta Aeróbica": ("Planta Aeróbica", "🦠 Planta Aeróbica"),
    "💧 Efluente": ("Efluente", "💧 Efluente"),
}


st.set_page_config(page_title="Planta RILES", layout="wide")


def aplicar_identidad_volta(tema):
    """Aplica una paleta aislada para no mezclar los estilos claro y oscuro."""
    oscuro = tema == "Oscuro"
    variables = (
        {
            "fondo": "#111A24", "panel": "#1B2A38", "panel_sec": "#233646",
            "texto": "#F1F6FA", "muted": "#B7C8D6", "linea": "#385064",
            "sidebar": "#0C1420", "sidebar_panel": "#172333", "azul": "#3FA9D5",
            "celeste": "#7DD8F3", "azul_hover": "#2C8FBC",
        }
        if oscuro else {
            "fondo": "#F7F9FC", "panel": "#FFFFFF", "panel_sec": "#FFFFFF",
            "texto": "#263B70", "muted": "#52627C", "linea": "#DCE5EF",
            "sidebar": "#263B70", "sidebar_panel": "#1F315D", "azul": "#147EAF",
            "celeste": "#67C5E8", "azul_hover": "#0C638D",
        }
    )
    st.html(
        """<style>:root { --fondo:""" + variables["fondo"] + "; --panel:" + variables["panel"]
        + "; --panel-sec:" + variables["panel_sec"] + "; --texto:" + variables["texto"]
        + "; --muted:" + variables["muted"] + "; --linea:" + variables["linea"]
        + "; --sidebar:" + variables["sidebar"] + "; --sidebar-panel:" + variables["sidebar_panel"]
        + "; --azul:" + variables["azul"] + "; --celeste:" + variables["celeste"]
        + "; --azul-hover:" + variables["azul_hover"] + "; }</style>"""
        + """
        <style>
          [data-testid="stAppViewContainer"] { background: var(--fondo); }
          [data-testid="stSidebar"] { background: var(--sidebar); }
          [data-testid="stSidebar"] h1,
          [data-testid="stSidebar"] h2,
          [data-testid="stSidebar"] h3,
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] label { color: #FFFFFF !important; }
          [data-testid="stSidebar"] [data-baseweb="radio"] > div {
            border-color: rgba(255,255,255,.28);
          }
          [data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="false"] {
            color: #FFFFFF !important;
          }
          [data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="false"] svg {
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
          }
          [data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] {
            color: var(--celeste) !important;
            font-weight: 700;
          }
          [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.22); }
          h1, h2, h3 { color: var(--texto) !important; letter-spacing: -.02em; }
          [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--linea);
            border-top: 3px solid var(--azul);
            border-radius: 4px;
            padding: 14px 16px;
            box-shadow: 0 2px 10px rgba(31,42,68,.06);
          }
          [data-testid="stMetricLabel"] { color: var(--muted); }
          [data-testid="stMetricValue"] { color: var(--texto); }
          .stButton > button, [data-testid="stDownloadButton"] > button {
            background: var(--azul);
            border-color: var(--azul);
            border-radius: 3px;
            color: #FFFFFF;
            font-weight: 700;
          }
          .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
            background: var(--azul-hover);
            border-color: var(--azul-hover);
            color: #FFFFFF;
          }
          [data-testid="stDataFrame"] { border: 1px solid var(--linea); }
          .js-plotly-plot .hoverlayer .bg {
            stroke-width: 3px !important;
            rx: 7px;
            ry: 7px;
          }
          .js-plotly-plot .hoverlayer .axistext {
            display: none !important;
          }
        </style>
        """
    )


from funciones.cargar_datos import hay_datos_operacionales

CONFIGURACION = obtener_configuracion()
if CONFIGURACION.es_nube and CONFIGURACION.faltantes_base_datos():
    st.error("El modo nube requiere configurar DATABASE_URL en Azure App Service.")
    st.stop()

st.title("📊 Dashboard Operacional Planta RILES")

st.sidebar.title("Menú Planta RILES")
tema = st.sidebar.selectbox(
    "Apariencia",
    ["Claro", "Oscuro"],
    key="tema_apariencia",
)
aplicar_identidad_volta(tema)
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
    from funciones.informe_impresion import estilos_impresion_dashboard

    st.html(estilos_impresion_dashboard())
