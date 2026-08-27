from pathlib import Path

import pandas as pd
import streamlit as st


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
CARPETA_GENERADOS = RAIZ_PROYECTO / "datos_generados"

ARCHIVOS_OPERACIONALES = (
    "fisico_quimico.xlsx",
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


def cargar_datos_operacionales():
    dataframes = []

    for nombre in ARCHIVOS_OPERACIONALES:
        ruta = CARPETA_GENERADOS / nombre

        if not ruta.exists():
            continue

        datos = _leer_excel(ruta)
        _validar_columnas(datos, COLUMNAS_LARGAS, ruta)
        dataframes.append(datos)

    if not dataframes:
        st.error("No existen archivos generados. Actualiza los datos desde Excel.")
        st.stop()

    return _normalizar_datos_largos(
        pd.concat(dataframes, ignore_index=True, sort=False)
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
