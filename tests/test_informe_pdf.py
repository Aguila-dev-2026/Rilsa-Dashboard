from io import BytesIO
import unittest

import pandas as pd
from pypdf import PdfReader

from funciones.informe_pdf import generar_informe_pdf


class InformePdfTests(unittest.TestCase):
    def test_incluye_resumen_graficos_y_detalle_de_todas_las_areas(self):
        datos = pd.DataFrame(
            [
                {
                    "Fecha": "2026-01-10",
                    "Area": "Físico-químico",
                    "Punto": "TK3",
                    "Parametro": "DQO",
                    "Valor": 123.4,
                    "Unidad": "mg/L",
                    "Turno": "Mañana",
                    "TipoDato": "Medición",
                    "Calificador": "",
                    "Fuente": "fisico_quimico.xlsx",
                    "Hoja": "Datos",
                },
                {
                    "Fecha": "2026-01-11",
                    "Area": "Planta aeróbica",
                    "Punto": "Reactor 1",
                    "Parametro": "pH",
                    "Valor": 7.2,
                    "Unidad": "pH",
                    "Turno": "Tarde",
                    "TipoDato": "Medición",
                    "Calificador": "",
                    "Fuente": "aerobico.xlsx",
                    "Hoja": "Diario",
                },
            ]
        )

        resultado = generar_informe_pdf(
            datos,
            entorno="Local",
            origen="Prueba automatizada",
        )

        self.assertTrue(resultado.startswith(b"%PDF"))
        texto = "\n".join(
            pagina.extract_text() or ""
            for pagina in PdfReader(BytesIO(resultado)).pages
        )
        self.assertIn("Informe operacional completo", texto)
        self.assertIn("Físico-químico", texto)
        self.assertIn("Planta aeróbica", texto)
        self.assertIn("Detalle completo de mediciones", texto)

