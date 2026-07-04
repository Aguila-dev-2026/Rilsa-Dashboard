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


def valor_si_no(valor_si, valor_no):
    if pd.notna(valor_si):
        return "Sí"

    if pd.notna(valor_no):
        return "No"

    return None


def importar_contenedores():
    df = pd.read_excel(
        ARCHIVO_PLANTA_ALTA,
        sheet_name="Contenedores",
        header=None
    )

    anio = 2026
    mes_nombre = str(df.iloc[6, 3]).strip().upper()
    mes_numero = MESES.get(mes_nombre)

    registros = []

    for fila in range(11, 42):
        dia = df.iloc[fila, 2]

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
            "Basura_Retiro": valor_si_no(df.iloc[fila, 3], df.iloc[fila, 4]),
            "Basura_Destino": df.iloc[fila, 5],
            "Lodos_Retiro": valor_si_no(df.iloc[fila, 7], df.iloc[fila, 8]),
            "Lodos_Destino": df.iloc[fila, 9],
        }

        registros.append(registro)

    datos = pd.DataFrame(registros)
    datos = datos.sort_values("Fecha").reset_index(drop=True)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_salida = os.path.join(CARPETA_SALIDA, "contenedores.xlsx")
    datos.to_excel(ruta_salida, index=False)

    print(f"OK: {ruta_salida} -> {len(datos)} registros")


if __name__ == "__main__":
    importar_contenedores()