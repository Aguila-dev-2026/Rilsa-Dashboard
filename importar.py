import os
import pandas as pd

from funciones.importar_quimicos import importar_quimicos
from funciones.importar_energia import importar_energia
from funciones.importar_contenedores import importar_contenedores

CARPETA_DATOS = "datos"
CARPETA_SALIDA = "datos_generados"

ARCHIVO_PROCESOS = os.path.join(CARPETA_DATOS, "Planilla Procesos RILES.xlsx")


def limpiar_valor(valor):
    if valor in ["−", "-", "", " "]:
        return None
    return valor


def importar_hoja(nombre_hoja, nombre_area, archivo_salida):
    df = pd.read_excel(
        ARCHIVO_PROCESOS,
        sheet_name=nombre_hoja,
        header=1
    )

    df = df.dropna(axis=1, how="all")

    columna_fecha = "Dia" if "Dia" in df.columns else "Fecha"

    df[columna_fecha] = pd.to_datetime(df[columna_fecha], errors="coerce")

    df_largo = df.melt(
        id_vars=[columna_fecha],
        var_name="Parametro",
        value_name="Valor"
    )

    df_largo = df_largo.rename(columns={columna_fecha: "Fecha"})

    df_largo["Area"] = nombre_area
    df_largo["Valor"] = df_largo["Valor"].apply(limpiar_valor)
    df_largo["Valor"] = pd.to_numeric(df_largo["Valor"], errors="coerce")

    df_largo = df_largo.dropna(subset=["Fecha", "Valor"])

    df_largo["Unidad"] = ""

    df_largo = df_largo[
        ["Fecha", "Area", "Parametro", "Valor", "Unidad"]
    ]

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_salida = os.path.join(CARPETA_SALIDA, archivo_salida)
    df_largo.to_excel(ruta_salida, index=False)

    print(f"OK: {ruta_salida} -> {len(df_largo)} registros")


def main():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    importar_hoja(
        nombre_hoja="Físico-químico",
        nombre_area="Físico-químico",
        archivo_salida="fisico_quimico.xlsx"
    )

    importar_hoja(
        nombre_hoja="Proceso aeróbico",
        nombre_area="Proceso aeróbico",
        archivo_salida="aerobico.xlsx"
    )

    importar_quimicos()

    importar_energia()

    importar_contenedores()
    
    print("Importación terminada.")


if __name__ == "__main__":
    main()