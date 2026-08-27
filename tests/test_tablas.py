import unittest

import pandas as pd

from funciones.tablas import preparar_columnas_visibles


class TablasTests(unittest.TestCase):
    def test_oculta_columnas_vacias_y_marcadores_none(self):
        datos = pd.DataFrame(
            {
                "Fecha": ["2026-01-01", "2026-01-02"],
                "Valor": [10, 12],
                "Turno": [None, "none"],
                "Calificador": ["", "NULL"],
                None: [None, None],
                "Fuente": ["archivo.xlsx", "none"],
            }
        )

        resultado = preparar_columnas_visibles(datos)

        self.assertEqual(list(resultado.columns), ["Fecha", "Valor", "Fuente"])
        self.assertEqual(resultado.loc[1, "Fuente"], "")

