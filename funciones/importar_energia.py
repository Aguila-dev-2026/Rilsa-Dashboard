import os
import pandas as pd


CARPETA_DATOS = "datos"
CARPETA_SALIDA = "datos_generados"

ARCHIVO_PLANTA_ALTA = os.path.join(CARPETA_DATOS, "PLANTA ALTA.xlsx")

MESES = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def limpiar_valor(valor):
    if valor in ["−", "-", "", " "]:
        return None
    return valor


def importar_bloque_energia(df, columna_dia, columna_m3, columna_kwh, fila_mes, columna_mes, anio):
    mes_nombre = str(df.iloc[fila_mes, columna_mes]).strip().upper()
    mes_numero = MESES.get(mes_nombre)

    if mes_numero is None:
        return pd.DataFrame()

    registros = []

    for fila in range(10, 41):
        dia = df.iloc[fila, columna_dia]

        if pd.isna(dia):
            continue

        try:
            dia = int(dia)
            fecha = pd.Timestamp(year=anio, month=mes_numero, day=dia)
        except Exception:
            continue

        m3 = limpiar_valor(df.iloc[fila, columna_m3])
        kwh = limpiar_valor(df.iloc[fila, columna_kwh])

        registros.append({
            "Fecha": fecha,
            "Mes": mes_nombre.title(),
            "Dia": dia,
            "M3": m3,
            "KWH": kwh,
        })

    datos = pd.DataFrame(registros)

    if datos.empty:
        return datos

    datos["M3"] = pd.to_numeric(datos["M3"], errors="coerce")
    datos["KWH"] = pd.to_numeric(datos["KWH"], errors="coerce")

    datos = datos.dropna(subset=["M3", "KWH"], how="all")
    datos = datos[
    (datos["M3"] >= 0)
    &
    (datos["KWH"] >= 0)
].copy()
    datos["KWH_por_M3"] = datos["KWH"] / datos["M3"]
    datos["KWH_por_M3"] = datos["KWH_por_M3"].replace([float("inf"), -float("inf")], pd.NA)

    return datos


def importar_energia():
    df = pd.read_excel(
        ARCHIVO_PLANTA_ALTA,
        sheet_name="M3- KWH",
        header=None
    )

    anio = int(df.iloc[1, 7])

    bloques = [
        importar_bloque_energia(
            df=df,
            columna_dia=2,
            columna_m3=3,
            columna_kwh=6,
            fila_mes=7,
            columna_mes=4,
            anio=anio
        ),
        importar_bloque_energia(
            df=df,
            columna_dia=10,
            columna_m3=11,
            columna_kwh=14,
            fila_mes=7,
            columna_mes=12,
            anio=anio
        ),
    ]

    datos = pd.concat(bloques, ignore_index=True)
    datos = datos.sort_values("Fecha").reset_index(drop=True)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_salida = os.path.join(CARPETA_SALIDA, "energia.xlsx")
    datos.to_excel(ruta_salida, index=False)

    print(f"OK: {ruta_salida} -> {len(datos)} registros")


if __name__ == "__main__":
    importar_energia()