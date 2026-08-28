from datetime import date, timedelta

import streamlit as st


FECHA_MINIMA_CONSULTA = date(2020, 1, 1)


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
    """Muestra el calendario y conserva el rango entre contextos de la sesión."""
    fecha_min = fecha_min.date() if hasattr(fecha_min, "date") else fecha_min
    fecha_max = fecha_max.date() if hasattr(fecha_max, "date") else fecha_max
    fecha_inicio_predeterminada = max(
        fecha_min,
        fecha_max - timedelta(days=29),
    )
    clave_inicio = f"fecha_inicio_30_dias_{clave}"
    clave_fin = f"fecha_fin_30_dias_{clave}"

    clave_global_inicio = "rango_fecha_inicio_persistente"
    clave_global_fin = "rango_fecha_fin_persistente"
    clave_contexto_activo = "rango_fecha_contexto_activo"

    # El primer acceso propone los últimos 30 días. Luego el rango elegido se
    # comparte entre áreas, puntos y parámetros durante toda la sesión.
    if clave_global_inicio not in st.session_state:
        st.session_state[clave_global_inicio] = fecha_inicio_predeterminada
    if clave_global_fin not in st.session_state:
        st.session_state[clave_global_fin] = fecha_max

    mismo_contexto = st.session_state.get(clave_contexto_activo) == clave
    if mismo_contexto:
        # En el mismo contexto, los valores de los widgets reflejan el último
        # cambio realizado por el usuario y pasan a ser la fuente persistente.
        if clave_inicio in st.session_state:
            st.session_state[clave_global_inicio] = st.session_state[clave_inicio]
        if clave_fin in st.session_state:
            st.session_state[clave_global_fin] = st.session_state[clave_fin]

    st.session_state[clave_contexto_activo] = clave
    st.session_state[clave_inicio] = st.session_state[clave_global_inicio]
    st.session_state[clave_fin] = st.session_state[clave_global_fin]

    fecha_inicio = st.sidebar.date_input(
        "Fecha inicial",
        min_value=FECHA_MINIMA_CONSULTA,
        max_value=date.today(),
        key=clave_inicio,
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha final",
        min_value=FECHA_MINIMA_CONSULTA,
        max_value=date.today(),
        key=clave_fin,
    )

    st.session_state[clave_global_inicio] = fecha_inicio
    st.session_state[clave_global_fin] = fecha_fin

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

def filtrar_por_turno(datos, clave="general"):
    """Permite visualizar Mañana, Tarde o ambas series sin perder el turno."""
    if "Turno" not in datos.columns:
        return datos, "Ambas"

    datos = datos.copy()
    datos["Turno"] = datos["Turno"].fillna("").astype(str).str.strip()
    datos["Turno"] = datos["Turno"].map(
        lambda valor: {
            "manana": "Mañana",
            "mañana": "Mañana",
            "tarde": "Tarde",
        }.get(valor.casefold(), valor)
    )
    # Algunas fuentes exportan el nulo como texto literal "nan"/"none".
    datos.loc[
        datos["Turno"].str.casefold().isin({"nan", "none", "null"}),
        "Turno",
    ] = ""
    disponibles = [turno for turno in ("Mañana", "Tarde") if turno in set(datos["Turno"])]
    if not disponibles:
        return datos, "Ambas"

    opciones = ["Mañana", "Tarde", "Ambas"]
    seleccion = st.sidebar.segmented_control(
        "Turno",
        opciones,
        default="Ambas",
        key=f"selector_turno_{clave}",
    ) or "Ambas"
    datos.loc[datos["Turno"].eq(""), "Turno"] = "Sin turno"
    if seleccion != "Ambas":
        categorias = [seleccion]
        # Por criterio operativo, los registros sin turno se consideran parte
        # de la vista Mañana, pero mantienen la categoría/color "Sin turno".
        if seleccion == "Mañana":
            categorias.append("Sin turno")
        datos = datos[datos["Turno"].isin(categorias)].copy()
    return datos, seleccion


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
