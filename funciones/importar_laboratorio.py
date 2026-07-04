import os
import pandas as pd


CARPETA_DATOS = "datos"
CARPETA_SALIDA = "datos_generados"

ARCHIVO_PLANTA_ALTA = os.path.join(CARPETA_DATOS, "PLANTA ALTA.xlsx")


def limpiar_valor(valor):
    if valor in ["−", "-", "", " "]:
        return None
    return valor


def importar_laboratorio():
    df = pd.read_excel(
        ARCHIVO_PLANTA_ALTA,
        sheet_name="Laboratorio",
        header=2
    )

    df = df.dropna(axis=1, how="all")

    columna_fecha = "Dia"

    df[columna_fecha] = pd.to_datetime(
        df[columna_fecha],
        errors="coerce"
    )

    df_largo = df.melt(
        id_vars=[columna_fecha],
        var_name="Parametro",
        value_name="Valor"
    )

    df_largo = df_largo.rename(columns={columna_fecha: "Fecha"})

    df_largo["Area"] = "Laboratorio"
    df_largo["Valor"] = df_largo["Valor"].apply(limpiar_valor)
    df_largo["Valor"] = pd.to_numeric(df_largo["Valor"], errors="coerce")

    df_largo = df_largo.dropna(subset=["Fecha", "Valor"])

    df_largo["Unidad"] = ""

    df_largo = df_largo[
        ["Fecha", "Area", "Parametro", "Valor", "Unidad"]
    ]

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_salida = os.path.join(CARPETA_SALIDA, "laboratorio.xlsx")
    df_largo.to_excel(ruta_salida, index=False)

    print(f"OK: {ruta_salida} -> {len(df_largo)} registros")


if __name__ == "__main__":
    importar_laboratorio()