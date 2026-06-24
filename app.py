import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================
# CONFIGURACIÓN DE LA PÁGINA
# ======================================

st.set_page_config(
    page_title="Planta RILES",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Dashboard Planta RILES")
st.markdown("---")

# ======================================
# CARGA DE DATOS
# ======================================

@st.cache_data(show_spinner="Cargando base histórica...")
def cargar_datos_laboratorio():

    ruta_lab = "datos/Historial_laboratorio.xlsx"

    if not os.path.exists(ruta_lab):
        st.error(
            f"No se encontró el archivo:\n{ruta_lab}"
        )
        st.stop()

    df = pd.read_excel(
        ruta_lab,
        header=8
    )

    # Eliminar columnas vacías tipo Unnamed
    df = df.loc[
        :,
        ~df.columns.str.contains("^Unnamed")
    ]

    # Validar columnas obligatorias
    columnas_requeridas = [
        "Fecha",
        "Lugar",
        "Análisis",
        "Resultado"
    ]

    faltantes = [
        c for c in columnas_requeridas
        if c not in df.columns
    ]

    if faltantes:
        st.error(
            f"Faltan columnas obligatorias: {faltantes}"
        )
        st.stop()

    # Conversión de tipos
    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    df["Resultado"] = pd.to_numeric(
        df["Resultado"],
        errors="coerce"
    )

    # Eliminar filas inválidas
    df = df.dropna(
        subset=["Fecha", "Resultado"]
    )

    return df


lab = cargar_datos_laboratorio()

# ======================================
# FILTROS
# ======================================

st.sidebar.header("🛠️ Filtros")

fecha_min = lab["Fecha"].min().date()
fecha_max = lab["Fecha"].max().date()

col_f1, col_f2 = st.sidebar.columns(2)

with col_f1:
    fecha_inicio = st.date_input(
        "Fecha inicio",
        value=fecha_min,
        min_value=fecha_min,
        max_value=fecha_max
    )

with col_f2:
    fecha_fin = st.date_input(
        "Fecha fin",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max
    )

# Parámetros

parametros = sorted(
    lab["Análisis"]
    .dropna()
    .astype(str)
    .unique()
)

parametros_sel = st.sidebar.multiselect(
    "Parámetros",
    parametros,
    default=[]
)

# Puntos

lugares = sorted(
    lab["Lugar"]
    .dropna()
    .astype(str)
    .unique()
)

lugares_sel = st.sidebar.multiselect(
    "Puntos de Muestreo",
    lugares,
    default=[]
)

# Escala temporal

escala = st.sidebar.selectbox(
    "Agrupación Temporal",
    [
        "Diaria",
        "Semanal",
        "Mensual",
        "Anual"
    ]
)

# ======================================
# FILTRADO
# ======================================

filtro = (
    (lab["Fecha"].dt.date >= fecha_inicio)
    &
    (lab["Fecha"].dt.date <= fecha_fin)
)

if parametros_sel:
    filtro &= lab["Análisis"].isin(
        parametros_sel
    )

if lugares_sel:
    filtro &= lab["Lugar"].isin(
        lugares_sel
    )

datos = lab[filtro].copy()

# ======================================
# AGRUPACIÓN TEMPORAL
# ======================================

mapeo_escalas = {
    "Semanal": "W",
    "Mensual": "M",
    "Anual": "Y"
}

if escala in mapeo_escalas:

    datos["Periodo"] = (
        datos["Fecha"]
        .dt.to_period(
            mapeo_escalas[escala]
        )
        .dt.to_timestamp()
    )

else:

    datos["Periodo"] = datos["Fecha"]

# ======================================
# MÉTRICAS
# ======================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Registros",
        f"{len(datos):,}"
    )

with col2:
    st.metric(
        "Parámetros",
        datos["Análisis"].nunique()
    )

with col3:
    st.metric(
        "Puntos",
        datos["Lugar"].nunique()
    )

with col4:

    if not datos.empty:
        st.metric(
            "Promedio",
            round(
                datos["Resultado"].mean(),
                2
            )
        )

with col5:

    if not datos.empty:
        st.metric(
            "Máximo",
            round(
                datos["Resultado"].max(),
                2
            )
        )

st.markdown("---")

# ======================================
# VALIDACIÓN DE FILTROS
# ======================================

if not parametros_sel or not lugares_sel:

    st.info(
        "Seleccione al menos un parámetro y un punto de muestreo."
    )

    st.stop()

# ======================================
# PESTAÑAS
# ======================================

tab1, tab2 = st.tabs(
    [
        "📊 Tendencia Temporal",
        "📋 Tabla de Datos"
    ]
)

# ======================================
# TABLA
# ======================================

with tab2:

    st.subheader(
        "Datos Filtrados"
    )

    tabla = datos.drop(
        columns=["Periodo"],
        errors="ignore"
    )

    st.dataframe(
        tabla,
        width="stretch"
    )

# ======================================
# GRÁFICO
# ======================================

with tab1:

    st.subheader(
        "Evolución Temporal"
    )

    if not datos.empty:

        datos_graf = (
            datos
            .groupby(
                [
                    "Periodo",
                    "Lugar",
                    "Análisis"
                ],
                as_index=False
            )["Resultado"]
            .mean()
        )

        fig = px.line(
            datos_graf,
            x="Periodo",
            y="Resultado",
            color="Lugar",
            facet_row="Análisis",
            markers=True,
            template="plotly_white",
            labels={
                "Periodo": "Fecha",
                "Resultado": "Resultado"
            }
        )

        fig.update_layout(
            height=max(
                600,
                datos_graf["Análisis"].nunique() * 300
            ),
            legend_title="Punto de Muestreo"
        )

        fig.update_yaxes(
            matches=None
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    else:

        st.warning(
            "No existen datos para los filtros seleccionados."
        )