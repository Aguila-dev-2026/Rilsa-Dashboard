from pathlib import Path
import unittest

import pandas as pd
import plotly.express as px

from funciones.dashboard_area import aplicar_estilo_premium, paleta_grafico


class TemaTests(unittest.TestCase):
    def test_interfaz_deja_el_tema_global_en_manos_de_streamlit(self):
        raiz = Path(__file__).resolve().parents[1]
        app = (raiz / "app.py").read_text(encoding="utf-8")

        self.assertFalse((raiz / ".streamlit" / "config.toml").exists())
        self.assertNotIn('data-testid="stAppViewContainer"', app)
        self.assertNotIn('data-testid="stSidebar"', app)
        self.assertNotIn('data-testid="stMetric"', app)

    def test_paleta_del_iframe_cambia_entre_light_y_dark(self):
        clara = paleta_grafico(False)
        oscura = paleta_grafico(True)

        self.assertEqual("plotly_white", clara["template"])
        self.assertEqual("plotly_dark", oscura["template"])
        self.assertNotEqual(clara["texto"], oscura["texto"])
        self.assertNotEqual(clara["cuadricula"], oscura["cuadricula"])

    def test_grafico_normal_no_fija_colores_de_texto_light(self):
        datos = pd.DataFrame({"Fecha": ["2026-08-27"], "Valor": [1.0]})
        figura = px.line(datos, x="Fecha", y="Valor", markers=True)

        aplicar_estilo_premium(figura, "Líneas", "pH", "")

        self.assertIsNone(figura.layout.font.color)
        self.assertIsNone(figura.layout.title.font.color)
        self.assertIsNone(figura.layout.xaxis.tickfont.color)
        self.assertIsNone(figura.layout.yaxis.tickfont.color)
        self.assertIsNone(figura.layout.yaxis.gridcolor)


if __name__ == "__main__":
    unittest.main()
