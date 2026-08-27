import streamlit as st


def filtrar_por_fecha(datos, columna_fecha="Fecha"):
    fecha_min = datos[columna_fecha].min().date()
    fecha_max = datos[columna_fecha].max().date()

    st.sidebar.subheader("Período de consulta")
    fecha_inicio = st.sidebar.date_input(
        "Fecha inicial",
        value=fecha_min,
        min_value=fecha_min,
        max_value=fecha_max,
        key="fecha_inicio",
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha final",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max,
        key="fecha_fin",
    )

    if fecha_inicio > fecha_fin:
        st.sidebar.error("La fecha inicial no puede ser posterior a la final.")
        return datos.iloc[0:0].copy()

    filtro = (
        (datos[columna_fecha].dt.date >= fecha_inicio)
        &
        (datos[columna_fecha].dt.date <= fecha_fin)
    )

    return datos[filtro].copy()


def filtrar_por_parametro(datos, columna_parametro="Parametro"):
    parametros = sorted(datos[columna_parametro].dropna().unique())

    parametro_seleccionado = st.sidebar.selectbox(
        "Parámetro a visualizar",
        parametros,
        key="selector_parametro",
    )

    return datos[
        datos[columna_parametro] == parametro_seleccionado
    ].copy()


def filtrar_por_quimicos(datos, columnas_quimicos):
    quimicos_sel = st.sidebar.multiselect(
        "Seleccionar químicos",
        columnas_quimicos,
        default=columnas_quimicos,
        key="selector_quimicos",
    )

    if not quimicos_sel:
        st.info("Selecciona al menos un químico.")
        return []

    return quimicos_sel
