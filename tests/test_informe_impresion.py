import unittest

import pandas as pd

from funciones.informe_impresion import generar_informe_impresion


class InformeImpresionTests(unittest.TestCase):
    def test_contiene_todas_las_areas_y_clase_de_impresion(self):
        datos = pd.DataFrame([
            {"Fecha": "2026-01-01", "Area": "Físico-químico", "Punto": "TK3", "Parametro": "DQO", "Valor": 20, "Unidad": "mg/L"},
            {"Fecha": "2026-01-02", "Area": "Planta Aeróbica", "Punto": "R1", "Parametro": "pH", "Valor": 7.1, "Unidad": "pH"},
        ])
        html = generar_informe_impresion(datos)
        self.assertIn("riles-print-root", html)
        self.assertIn("riles-print-report", html)
        self.assertIn("color-scheme:light", html)
        self.assertIn("Físico-químico", html)
        self.assertIn("Planta Aeróbica", html)
        self.assertIn("Informe operacional completo", html)
