import ast
from pathlib import Path
import unittest


class BandasTests(unittest.TestCase):
    def test_bandas_y_tendencia_tienen_funciones_independientes(self):
        raiz = Path(__file__).resolve().parents[1]
        ruta = raiz / "funciones" / "graficos" / "bandas.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        funciones = {
            nodo.name: ast.unparse(nodo)
            for nodo in arbol.body
            if isinstance(nodo, ast.FunctionDef)
        }

        self.assertIn("add_hrect", funciones["agregar_bandas"])
        self.assertIn("ROJO_ALERTA", funciones["agregar_bandas"])
        self.assertIn("number_input", funciones["configurar_bandas"])
        self.assertIn("Añadir banda inferior", funciones["configurar_bandas"])
        self.assertIn("Añadir banda superior", funciones["configurar_bandas"])
        self.assertIn("Mostrar bandas normativas", funciones["configurar_bandas"])
        self.assertIn("BANDAS_NCH1333_RIEGO", funciones["obtener_banda_normativa"])
        for parametro in (
            "Conductividad",
            "Sulfato",
            "Boro total",
            "Sólidos disueltos",
            "Cloruro",
        ):
            self.assertIn(parametro, ruta.read_text(encoding="utf-8"))
        tendencias = ast.parse(
            (raiz / "funciones" / "graficos" / "tendencias.py").read_text(
                encoding="utf-8"
            )
        )
        funciones_tendencias = {
            nodo.name: ast.unparse(nodo)
            for nodo in tendencias.body
            if isinstance(nodo, ast.FunctionDef)
        }
        self.assertNotIn("add_hrect", funciones_tendencias["agregar_tendencia"])
        self.assertIn("tipo_grafico_recomendado", funciones_tendencias)
        self.assertIn("Líneas", funciones_tendencias["tipo_grafico_recomendado"])
        self.assertIn("obtener_limites_activos", funciones)
        self.assertIn("resaltar_valores_fuera_de_rango", funciones)
        self.assertIn("ROJO_ALERTA", funciones["resaltar_valores_fuera_de_rango"])
        self.assertIn(
            "MedicionDisponible",
            (raiz / "funciones" / "dashboard_area.py").read_text(
                encoding="utf-8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
