import unittest
from pathlib import Path

import pandas as pd

from ingesta.comun import convertir_a_numero, huella_archivo, normalizar_nombre
from ingesta.validaciones import validar_datos


class IngestaTest(unittest.TestCase):
    def test_normaliza_nombres_y_numeros(self):
        self.assertEqual(normalizar_nombre("  Energía   Eléctrica "), "energia electrica")
        resultado = convertir_a_numero(pd.Series(["1.234,5", "-", 2]))
        self.assertEqual(resultado.iloc[0], 1234.5)
        self.assertTrue(pd.isna(resultado.iloc[1]))
        self.assertEqual(resultado.iloc[2], 2.0)

    def test_huella_incluye_identidad_y_tamano(self):
        ruta = Path(__file__)
        huella = huella_archivo(ruta)
        self.assertEqual(huella["Nombre"], ruta.name)
        self.assertGreater(huella["Tamano"], 0)
        self.assertEqual(len(huella["SHA256"]), 64)

    def test_validacion_rechaza_duplicados(self):
        datos = pd.DataFrame(
            [
                {
                    "Fecha": pd.Timestamp("2024-01-01"),
                    "Area": "Físico-químico",
                    "Punto": "Físico-químico",
                    "Turno": "",
                    "Parametro": "pH",
                    "Valor": 7.0,
                },
            ]
            * 2
        )
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            validar_datos(
                datos,
                {},
                columnas_mediciones=["Fecha", "Area", "Punto", "Turno", "Parametro", "Valor"],
                areas_esperadas={"Físico-químico"},
            )


if __name__ == "__main__":
    unittest.main()
