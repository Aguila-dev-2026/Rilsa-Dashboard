import unittest

import pandas as pd

from funciones.dominio.tendencias import calcular_tendencia


class TendenciasTest(unittest.TestCase):
    def test_valor_cero_se_conserva_como_medicion_valida(self):
        datos = pd.DataFrame(
            {
                "Fecha": pd.to_datetime(["2026-08-24", "2026-08-25"]),
                "Valor": [0.0, 2.0],
            }
        )

        tendencia, _metodo = calcular_tendencia(datos, "pH")

        self.assertIsNotNone(tendencia)
        self.assertEqual(len(tendencia), 2)
        self.assertEqual(tendencia["Fecha"].tolist(), datos["Fecha"].tolist())


if __name__ == "__main__":
    unittest.main()
