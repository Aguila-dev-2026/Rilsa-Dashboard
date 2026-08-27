from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


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


@st.cache_data(show_spinner=False, max_entries=32)
def _leer_excel_cacheado(ruta, mtime_ns, tamano):
    """Cachea cada versión física del archivo, no solo el nombre de la función."""
    del mtime_ns, tamano
    return pd.read_excel(ruta)


def _leer_excel(ruta):
    estado = ruta.stat()
    return _leer_excel_cacheado(str(ruta), estado.st_mtime_ns, estado.st_size)


@st.cache_data(show_spinner=False, max_entries=16)
def _consultar_sqlite_cacheado(ruta, mtime_ns, tamano, nombre_area):
    """Consulta una versión física concreta de SQLite y solo el área solicitada."""
    del mtime_ns, tamano
    consulta = "SELECT * FROM mediciones"
    parametros = ()
    if nombre_area:
        consulta += " WHERE Area = ?"
        parametros = (nombre_area,)

    with sqlite3.connect(ruta) as conexion:
        return pd.read_sql_query(
            consulta,
            conexion,
            params=parametros,
            parse_dates=["Fecha"],
        )


def _consultar_sqlite(nombre_area=None):
    estado = BASE_DATOS.stat()
    return _consultar_sqlite_cacheado(
        str(BASE_DATOS),
        estado.st_mtime_ns,
        estado.st_size,
        nombre_area,
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


def cargar_datos_operacionales(nombre_area=None):
    if BASE_DATOS.exists():
        try:
            datos = _consultar_sqlite(nombre_area)
            _validar_columnas(datos, COLUMNAS_LARGAS, BASE_DATOS)
            return _normalizar_datos_largos(datos)
        except (sqlite3.DatabaseError, OSError, ValueError) as error:
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
    if nombre_area:
        combinados = combinados[combinados["Area"] == nombre_area]

    return _normalizar_datos_largos(combinados)

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
