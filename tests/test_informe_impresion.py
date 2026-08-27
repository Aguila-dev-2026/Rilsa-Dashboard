import unittest

from funciones.informe_impresion import estilos_impresion_dashboard


class InformeImpresionTests(unittest.TestCase):
    def test_conserva_grafico_y_oculta_tabla_en_impresion(self):
        estilos = estilos_impresion_dashboard()
        self.assertIn("color-scheme: light", estilos)
        self.assertIn("stDataFrame", estilos)
        self.assertIn("stPlotlyChart", estilos)
        self.assertIn("grid-template-columns: 220px", estilos)
        self.assertIn("stSidebar", estilos)
