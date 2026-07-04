import streamlit as st


def filtrar_por_fecha(datos, columna_fecha="Fecha"):
    fecha_min = datos[columna_fecha].min().date()
    fecha_max = datos[columna_fecha].max().date()

    fecha_inicio = st.sidebar.date_input(
        "Fecha inicio",
        value=fecha_min,
        min_value=fecha_min,
        max_value=fecha_max
    )

    fecha_fin = st.sidebar.date_input(
        "Fecha fin",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max
    )

    filtro = (
        (datos[columna_fecha].dt.date >= fecha_inicio)
        &
        (datos[columna_fecha].dt.date <= fecha_fin)
    )

    return datos[filtro].copy()


def filtrar_por_parametro(datos, columna_parametro="Parametro"):
    parametros = sorted(datos[columna_parametro].dropna().unique())

    
    parametros_sel = st.sidebar.multiselect(
        "Parámetros",
        parametros,
        default=parametros[:3]
    )

    if not parametros_sel:
        st.info("Selecciona al menos un parámetro.")
        return datos.iloc[0:0].copy()

    return datos[
        datos[columna_parametro].isin(parametros_sel)
    ].copy()


def filtrar_por_quimicos(datos, columnas_quimicos):
    quimicos_sel = st.sidebar.multiselect(
        "Seleccionar químicos",
        columnas_quimicos,
        default=columnas_quimicos,
        key="selector_quimicos"
    )

    if not quimicos_sel:
        st.info("Selecciona al menos un químico.")
        return []

    return quimicos_sel