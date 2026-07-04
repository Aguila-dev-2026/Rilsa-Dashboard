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


def obtener_anio(df):
    texto = str(df.iloc[0, 5])
    partes = texto.split()

    for parte in partes:
        if parte.isdigit():
            return int(parte)

    return 2026


def importar_bloque_quimicos(df, fila_mes, columna_inicio, anio):
    mes_nombre = str(df.iloc[fila_mes, columna_inicio + 1]).strip().upper()
    mes_numero = MESES.get(mes_nombre)

    if mes_numero is None:
        return pd.DataFrame()

    columnas = {
        "Dia": columna_inicio,
        "Catiónico": columna_inicio + 1,
        "Aniónico": columna_inicio + 2,
        "PAC": columna_inicio + 3,
        "Cal": columna_inicio + 4,
    }

    registros = []

    for fila in range(12, 43):
        dia = df.iloc[fila, columnas["Dia"]]

        if pd.isna(dia):
            continue

        try:
            dia = int(dia)
            fecha = pd.Timestamp(year=anio, month=mes_numero, day=dia)
        except Exception:
            continue

        registro = {
            "Fecha": fecha,
            "Mes": mes_nombre.title(),
            "Dia": dia,
            "Catiónico": limpiar_valor(df.iloc[fila, columnas["Catiónico"]]),
            "Aniónico": limpiar_valor(df.iloc[fila, columnas["Aniónico"]]),
            "PAC": limpiar_valor(df.iloc[fila, columnas["PAC"]]),
            "Cal": limpiar_valor(df.iloc[fila, columnas["Cal"]]),
        }

        registros.append(registro)

    bloque = pd.DataFrame(registros)

    if bloque.empty:
        return bloque

    for columna in ["Catiónico", "Aniónico", "PAC", "Cal"]:
        bloque[columna] = pd.to_numeric(bloque[columna], errors="coerce")

    bloque = bloque.dropna(
        subset=["Catiónico", "Aniónico", "PAC", "Cal"],
        how="all"
    )

    return bloque


def importar_quimicos():
    df = pd.read_excel(
        ARCHIVO_PLANTA_ALTA,
        sheet_name="Químicos",
        header=None
    )

    anio = obtener_anio(df)

    bloques = [
        importar_bloque_quimicos(df, fila_mes=8, columna_inicio=4, anio=anio),
        importar_bloque_quimicos(df, fila_mes=8, columna_inicio=11, anio=anio),
        importar_bloque_quimicos(df, fila_mes=8, columna_inicio=18, anio=anio),
    ]

    datos = pd.concat(bloques, ignore_index=True)
    datos = datos.sort_values("Fecha").reset_index(drop=True)
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_salida = os.path.join(CARPETA_SALIDA, "quimicos.xlsx")
    datos.to_excel(ruta_salida, index=False)

    print(f"OK: {ruta_salida} -> {len(datos)} registros")


if __name__ == "__main__":
    importar_quimicos()