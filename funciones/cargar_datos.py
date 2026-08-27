from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

from funciones.configuracion import obtener_configuracion


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
CARPETA_GENERADOS = RAIZ_PROYECTO / "datos_generados"
BASE_DATOS = CARPETA_GENERADOS / "riles.db"

ARCHIVOS_OPERACIONALES = (
    "fisico_quimico.xlsx",
    "analisis_planta_aerobica.xlsx",
    "aerobico.xlsx",
    "planta_baja.xlsx",
    "laboratorio.xlsx",
)

COLUMNAS_LARGAS = {"Fecha", "Area", "Parametro", "Valor", "Unidad"}
COLUMNAS_CATALOGO = {
    "Area",
    "Punto",
    "Parametro",
    "Unidad",
    "FechaMin",
    "FechaMax",
    "Registros",
}


@st.cache_data(show_spinner=False, max_entries=32)
def _leer_excel_cacheado(ruta, mtime_ns, tamano):
    """Cachea cada versión física del archivo, no solo el nombre de la función."""
    del mtime_ns, tamano
    return pd.read_excel(ruta)


def _leer_excel(ruta):
    estado = ruta.stat()
    return _leer_excel_cacheado(str(ruta), estado.st_mtime_ns, estado.st_size)


@st.cache_data(show_spinner=False, max_entries=64)
def _consultar_sqlite_cacheado(
    ruta,
    mtime_ns,
    tamano,
    nombre_area,
    punto,
    parametro,
    fecha_inicio,
    fecha_fin,
):
    """Consulta únicamente las mediciones necesarias para el gráfico actual."""
    del mtime_ns, tamano
    condiciones = []
    parametros = []

    if nombre_area is not None:
        condiciones.append("Area = ?")
        parametros.append(nombre_area)
    if punto is not None:
        condiciones.append("Punto = ?")
        parametros.append(punto)
    if parametro is not None:
        condiciones.append("Parametro = ?")
        parametros.append(parametro)
    if fecha_inicio is not None:
        condiciones.append("Fecha >= ?")
        parametros.append(fecha_inicio)
    if fecha_fin is not None:
        condiciones.append("Fecha <= ?")
        parametros.append(fecha_fin)

    consulta = "SELECT * FROM mediciones"
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY Fecha"

    with sqlite3.connect(ruta) as conexion:
        return pd.read_sql_query(
            consulta,
            conexion,
            params=tuple(parametros),
            parse_dates=["Fecha"],
        )


@st.cache_data(show_spinner=False, max_entries=16)
def _consultar_catalogo_sqlite_cacheado(
    ruta,
    mtime_ns,
    tamano,
    nombre_area,
):
    """Carga solo opciones y límites de fecha, sin traer todas las mediciones."""
    del mtime_ns, tamano
    consulta = """
        SELECT
            Area,
            Punto,
            Parametro,
            COALESCE(Unidad, '') AS Unidad,
            MIN(Fecha) AS FechaMin,
            MAX(Fecha) AS FechaMax,
            COUNT(*) AS Registros
        FROM mediciones
    """
    parametros = ()
    if nombre_area is not None:
        consulta += " WHERE Area = ?"
        parametros = (nombre_area,)
    consulta += """
        GROUP BY Area, Punto, Parametro, COALESCE(Unidad, '')
        ORDER BY Area, Punto, Parametro
    """

    with sqlite3.connect(ruta) as conexion:
        return pd.read_sql_query(
            consulta,
            conexion,
            params=parametros,
            parse_dates=["FechaMin", "FechaMax"],
        )


def _fecha_para_sql(valor):
    if valor is None:
        return None
    return pd.Timestamp(valor).strftime("%Y-%m-%d")


def _consultar_sqlite(
    nombre_area=None,
    punto=None,
    parametro=None,
    fecha_inicio=None,
    fecha_fin=None,
):
    estado = BASE_DATOS.stat()
    return _consultar_sqlite_cacheado(
        str(BASE_DATOS),
        estado.st_mtime_ns,
        estado.st_size,
        nombre_area,
        punto,
        parametro,
        _fecha_para_sql(fecha_inicio),
        _fecha_para_sql(fecha_fin),
    )


def _consultar_catalogo_sqlite(nombre_area=None):
    estado = BASE_DATOS.stat()
    return _consultar_catalogo_sqlite_cacheado(
        str(BASE_DATOS),
        estado.st_mtime_ns,
        estado.st_size,
        nombre_area,
    )


@st.cache_data(show_spinner=False, ttl=60, max_entries=64)
def _consultar_postgres_cacheado(
    database_url,
    nombre_area,
    punto,
    parametro,
    fecha_inicio,
    fecha_fin,
):
    """Comparte consultas durante un minuto entre sesiones del servidor."""
    from funciones.postgres import consultar_mediciones

    return consultar_mediciones(
        database_url,
        nombre_area=nombre_area,
        punto=punto,
        parametro=parametro,
        fecha_inicio=_fecha_para_sql(fecha_inicio),
        fecha_fin=_fecha_para_sql(fecha_fin),
    )


@st.cache_data(show_spinner=False, ttl=60, max_entries=16)
def _consultar_catalogo_postgres_cacheado(database_url, nombre_area):
    from funciones.postgres import consultar_catalogo

    return consultar_catalogo(database_url, nombre_area)


@st.cache_data(show_spinner=False, ttl=30, max_entries=4)
def _hay_mediciones_postgres_cacheado(database_url):
    from funciones.postgres import hay_mediciones

    return hay_mediciones(database_url)


def hay_datos_operacionales():
    """Indica si la fuente activa contiene al menos una medición."""
    configuracion = obtener_configuracion()
    if configuracion.es_nube:
        if not configuracion.database_url:
            return False
        return _hay_mediciones_postgres_cacheado(configuracion.database_url)
    return BASE_DATOS.exists() or any(
        (CARPETA_GENERADOS / nombre).exists()
        for nombre in ARCHIVOS_OPERACIONALES
    )


def _detener_por_archivo(ruta):
    st.error(f"No existe {ruta.relative_to(RAIZ_PROYECTO)}. Actualiza los datos desde Excel.")
    st.stop()


def _validar_columnas(datos, columnas, ruta):
    faltantes = set(columnas).difference(datos.columns)

    if faltantes:
        nombres = ", ".join(sorted(faltantes))
        st.error(
            f"{ruta.name} no tiene las columnas requeridas: {nombres}. "
            "Vuelve a actualizar los datos desde Excel."
        )
        st.stop()


def _normalizar_datos_largos(datos):
    datos = datos.copy()
    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
    datos["Valor"] = pd.to_numeric(datos["Valor"], errors="coerce")
    datos = datos.dropna(subset=["Fecha", "Valor", "Area", "Parametro"])
    return datos.sort_values(["Fecha", "Area", "Parametro"]).reset_index(drop=True)


def _cargar_archivo_largo(nombre):
    ruta = CARPETA_GENERADOS / nombre

    if not ruta.exists():
        _detener_por_archivo(ruta)

    datos = _leer_excel(ruta)
    _validar_columnas(datos, COLUMNAS_LARGAS, ruta)
    return _normalizar_datos_largos(datos)


def cargar_datos_operacionales(
    nombre_area=None,
    punto=None,
    parametro=None,
    fecha_inicio=None,
    fecha_fin=None,
):
    configuracion = obtener_configuracion()
    if configuracion.es_nube:
        if not configuracion.database_url:
            st.error("Falta configurar DATABASE_URL para el modo nube.")
            st.stop()
        try:
            datos = _consultar_postgres_cacheado(
                configuracion.database_url,
                nombre_area,
                punto,
                parametro,
                fecha_inicio,
                fecha_fin,
            )
            _validar_columnas(datos, COLUMNAS_LARGAS, Path("PostgreSQL"))
            return _normalizar_datos_largos(datos)
        except Exception as error:
            st.error(
                "No fue posible consultar PostgreSQL. "
                f"Revisa la conexión del servicio. Detalle: {error}"
            )
            st.stop()

    if BASE_DATOS.exists():
        try:
            datos = _consultar_sqlite(
                nombre_area=nombre_area,
                punto=punto,
                parametro=parametro,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
            )
            _validar_columnas(datos, COLUMNAS_LARGAS, BASE_DATOS)
            return _normalizar_datos_largos(datos)
        except (
            sqlite3.DatabaseError,
            pd.errors.DatabaseError,
            OSError,
            ValueError,
        ) as error:
            st.warning(
                "No fue posible consultar SQLite. "
                "Se utilizarán temporalmente los Excel generados. "
                f"Detalle: {error}"
            )

    dataframes = []

    for nombre in ARCHIVOS_OPERACIONALES:
        ruta = CARPETA_GENERADOS / nombre

        if not ruta.exists():
            continue

        datos = _leer_excel(ruta)
        _validar_columnas(datos, COLUMNAS_LARGAS, ruta)
        datos["_PrioridadFuente"] = (
            100 if nombre == "analisis_planta_aerobica.xlsx" else 0
        )
        dataframes.append(datos)

    if not dataframes:
        st.error("No existen archivos generados. Actualiza los datos desde Excel.")
        st.stop()

    combinados = pd.concat(dataframes, ignore_index=True, sort=False)
    claves = ["Fecha", "Area", "Parametro"]
    claves.extend(
        columna
        for columna in ("Punto", "Turno")
        if columna in combinados.columns
    )
    combinados = (
        combinados.sort_values("_PrioridadFuente")
        .drop_duplicates(subset=claves, keep="last")
        .drop(columns="_PrioridadFuente")
    )
    combinados = _normalizar_datos_largos(combinados)
    if nombre_area is not None:
        combinados = combinados[combinados["Area"].eq(nombre_area)]
    if punto is not None and "Punto" in combinados.columns:
        puntos = combinados["Punto"].fillna("").astype(str).str.strip()
        combinados = combinados[puntos.eq(punto)]
    if parametro is not None:
        combinados = combinados[combinados["Parametro"].eq(parametro)]
    if fecha_inicio is not None:
        combinados = combinados[
            combinados["Fecha"] >= pd.Timestamp(fecha_inicio)
        ]
    if fecha_fin is not None:
        combinados = combinados[
            combinados["Fecha"] <= pd.Timestamp(fecha_fin)
        ]

    return combinados.reset_index(drop=True)


def cargar_catalogo_operacional(nombre_area=None):
    configuracion = obtener_configuracion()
    if configuracion.es_nube:
        if not configuracion.database_url:
            st.error("Falta configurar DATABASE_URL para el modo nube.")
            st.stop()
        try:
            catalogo = _consultar_catalogo_postgres_cacheado(
                configuracion.database_url,
                nombre_area,
            )
            _validar_columnas(catalogo, COLUMNAS_CATALOGO, Path("PostgreSQL"))
            return catalogo
        except Exception as error:
            st.error(
                "No fue posible consultar el catálogo de PostgreSQL. "
                f"Detalle: {error}"
            )
            st.stop()

    if BASE_DATOS.exists():
        try:
            catalogo = _consultar_catalogo_sqlite(nombre_area)
            _validar_columnas(catalogo, COLUMNAS_CATALOGO, BASE_DATOS)
            return catalogo
        except (
            sqlite3.DatabaseError,
            pd.errors.DatabaseError,
            OSError,
            ValueError,
        ) as error:
            st.warning(
                "No fue posible consultar el catálogo de SQLite. "
                "Se reconstruirá temporalmente desde los datos generados. "
                f"Detalle: {error}"
            )

    datos = cargar_datos_operacionales(nombre_area=nombre_area)
    if "Punto" not in datos.columns:
        datos["Punto"] = ""
    datos["Punto"] = datos["Punto"].fillna("").astype(str).str.strip()
    datos["Unidad"] = datos["Unidad"].fillna("").astype(str).str.strip()

    return (
        datos.groupby(
            ["Area", "Punto", "Parametro", "Unidad"],
            as_index=False,
            dropna=False,
        )
        .agg(
            FechaMin=("Fecha", "min"),
            FechaMax=("Fecha", "max"),
            Registros=("Valor", "size"),
        )
        .sort_values(["Area", "Punto", "Parametro"])
        .reset_index(drop=True)
    )


def cargar_datos_laboratorio():
    return _cargar_archivo_largo("laboratorio.xlsx")


def cargar_datos_quimicos():
    ruta = CARPETA_GENERADOS / "quimicos.xlsx"

    if not ruta.exists():
        _detener_por_archivo(ruta)

    datos = _leer_excel(ruta)
    columnas = {"Fecha", "Mes", "Dia", "Catiónico", "Aniónico", "PAC", "Cal"}
    _validar_columnas(datos, columnas, ruta)

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")

    for columna in ["Catiónico", "Aniónico", "PAC", "Cal"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    return datos.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)


def cargar_datos_energia():
    ruta = CARPETA_GENERADOS / "energia.xlsx"

    if not ruta.exists():
        _detener_por_archivo(ruta)

    datos = _leer_excel(ruta)
    columnas = {"Fecha", "Mes", "Dia", "M3", "KWH", "KWH_por_M3"}
    _validar_columnas(datos, columnas, ruta)

    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")

    for columna in ["M3", "KWH", "KWH_por_M3"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    return datos.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)


def cargar_datos_contenedores():
    ruta = CARPETA_GENERADOS / "contenedores.xlsx"

    if not ruta.exists():
        _detener_por_archivo(ruta)

    datos = _leer_excel(ruta)
    columnas = {
        "Fecha",
        "Mes",
        "Dia",
        "Basura_Retiro",
        "Basura_Destino",
        "Lodos_Retiro",
        "Lodos_Destino",
    }
    _validar_columnas(datos, columnas, ruta)
    datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
    return datos.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)
