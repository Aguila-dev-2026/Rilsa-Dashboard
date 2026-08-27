from datetime import timedelta

import streamlit as st


# Orden operativo: parámetros físico-químicos actuales y luego variables de
# laboratorio/proceso del nuevo historial.
ORDEN_PARAMETROS_PROCESO = [
    "Ingresos [Ton]",
    "Volumen TK3 [m3]",
    "DQO TK3 [mg/l]",
    "pH",
    "Conductividad [mS]",
    "Turbiedad [NTU]",
    "Consumo Cal [kg]",
    "Consumo PAC [kg]",
    "Consumo P. Aniónico [kg]",
    "Consumo P. Catiónico [kg]",
    "% Humedad Lodo 1",
    "% Humedad Lodo 2",
    "Energía eléctrica consumida",
    "DQO",
    "DBO estimada",
    "DQO TK2",
    "DQO clarificado",
    "Remoción DQO",
    "Temperatura",
    "Conductividad",
    "Color aparente",
    "Turbidez",
    "Sulfato",
    "Boro total",
    "Cloruro",
    "Cloro libre",
    "Nitrógeno total",
    "NH3",
    "NO3-",
    "Nitrógeno",
    "Fósforo total",
    "PO4-3",
    "P2O5",
    "SST",
    "SSV",
    "SSF",
    "Sólidos disueltos",
    "Sólidos sedimentables 30 min",
    "Sólidos sedimentables 60 min",
    "IVL",
    "Relación SSF/SSV",
    "Relación C:P",
    "Relación N:P",
    "Relación F/M",
    "Edad del lodo",
    "Volumen de alimentación",
    "Descarga a Reactor N°1",
    "Máxima descarga diaria",
    "Carga DBO5",
    "Carga de nitrógeno total",
    "Carga de fósforo total",
    "Descarga a riego",
    "Descarga a infiltración",
]

ORDEN_PUNTOS = [
    "Afluente",
    "Reactor N°1",
    "Clarificado Reactor N°1",
    "Reactor N°2",
    "Reactor N°3",
    "Reactor N°4",
    "Reactor N°5",
    "Digestor",
    "Recirculación",
    "Clarificador Biológico",
    "Efluente",
]


def seleccionar_rango_fecha(fecha_min, fecha_max, clave="general"):
    """Muestra y conserva el calendario durante la sesión actual."""
    fecha_min = fecha_min.date() if hasattr(fecha_min, "date") else fecha_min
    fecha_max = fecha_max.date() if hasattr(fecha_max, "date") else fecha_max
    fecha_inicio_predeterminada = max(
        fecha_min,
        fecha_max - timedelta(days=29),
    )
    clave_inicio = f"fecha_inicio_30_dias_{clave}"
    clave_fin = f"fecha_fin_30_dias_{clave}"

    # Los valores predeterminados se asignan una única vez por sesión.
    # Streamlit elimina session_state cuando el usuario cierra la app.
    if clave_inicio not in st.session_state:
        st.session_state[clave_inicio] = fecha_inicio_predeterminada
    if clave_fin not in st.session_state:
        st.session_state[clave_fin] = fecha_max

    st.sidebar.subheader("Período de consulta")
    fecha_inicio = st.sidebar.date_input(
        "Fecha inicial",
        min_value=fecha_min,
        max_value=fecha_max,
        key=clave_inicio,
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha final",
        min_value=fecha_min,
        max_value=fecha_max,
        key=clave_fin,
    )

    if fecha_inicio > fecha_fin:
        st.sidebar.error("La fecha inicial no puede ser posterior a la final.")
        return None, None

    return fecha_inicio, fecha_fin


def filtrar_por_fecha(datos, columna_fecha="Fecha", clave="general"):
    fecha_inicio, fecha_fin = seleccionar_rango_fecha(
        datos[columna_fecha].min(),
        datos[columna_fecha].max(),
        clave,
    )
    if fecha_inicio is None:
        return datos.iloc[0:0].copy()

    filtro = (
        (datos[columna_fecha].dt.date >= fecha_inicio)
        & (datos[columna_fecha].dt.date <= fecha_fin)
    )
    return datos[filtro].copy()


def filtrar_dimension(
    datos,
    *,
    columna,
    etiqueta,
    clave,
    orden_preferido,
    nombre_vacio=None,
    opcion_todos=None,
):
    if columna not in datos.columns:
        return datos

    serie = datos[columna].fillna("").astype(str).str.strip()
    disponibles = set(serie[serie.ne("")].unique())
    if nombre_vacio and serie.eq("").any():
        disponibles.add(nombre_vacio)

    if len(disponibles) <= 1:
        return datos

    opciones = [valor for valor in orden_preferido if valor in disponibles]
    opciones.extend(sorted(disponibles.difference(opciones)))
    if opcion_todos:
        opciones.insert(0, opcion_todos)

    seleccionado = st.sidebar.selectbox(
        etiqueta,
        opciones,
        key=f"selector_{columna.lower()}_{clave}",
    )
    if opcion_todos and seleccionado == opcion_todos:
        return datos
    if nombre_vacio and seleccionado == nombre_vacio:
        return datos[serie.eq("")].copy()

    return datos[serie.eq(seleccionado)].copy()


def filtrar_contexto_operacional(datos, clave):
    return filtrar_dimension(
        datos,
        columna="Punto",
        etiqueta="Punto de proceso",
        clave=clave,
        orden_preferido=ORDEN_PUNTOS,
    )


def filtrar_por_parametro(datos, columna_parametro="Parametro", clave="general"):
    disponibles = set(datos[columna_parametro].dropna().unique())
    parametros = [
        parametro
        for parametro in ORDEN_PARAMETROS_PROCESO
        if parametro in disponibles
    ]
    parametros.extend(sorted(disponibles.difference(parametros)))

    parametro_seleccionado = st.sidebar.selectbox(
        "Parámetro a visualizar",
        parametros,
        key=f"selector_parametro_{clave}",
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
