import os
import unittest
from unittest.mock import patch

from funciones.configuracion import (
    limpiar_cache_configuracion,
    obtener_configuracion,
)


class ConfiguracionTest(unittest.TestCase):
    def tearDown(self):
        limpiar_cache_configuracion()

    def test_modo_local_es_predeterminado(self):
        with patch.dict(os.environ, {}, clear=True):
            limpiar_cache_configuracion()
            configuracion = obtener_configuracion()

        self.assertEqual(configuracion.entorno, "local")
        self.assertFalse(configuracion.es_nube)
        self.assertFalse(configuracion.usa_postgres)

    def test_modo_nube_normaliza_postgres(self):
        with patch.dict(
            os.environ,
            {
                "RILSA_APP_ENV": "cloud",
                "DATABASE_URL": "postgresql://usuario:clave@host/rilsa",
            },
            clear=True,
        ):
            limpiar_cache_configuracion()
            configuracion = obtener_configuracion()

        self.assertTrue(configuracion.es_nube)
        self.assertEqual(
            configuracion.database_url,
            "postgresql+psycopg://usuario:clave@host/rilsa",
        )

    def test_configuracion_no_expone_secret_en_faltantes(self):
        with patch.dict(
            os.environ,
            {
                "RILSA_APP_ENV": "cloud",
                "DATABASE_URL": "postgresql://host/rilsa",
                "AZURE_CLIENT_SECRET": "secreto",
            },
            clear=True,
        ):
            limpiar_cache_configuracion()
            configuracion = obtener_configuracion()

        self.assertNotIn("secreto", configuracion.faltantes_sharepoint())
        self.assertNotIn("AZURE_CLIENT_SECRET", configuracion.faltantes_sharepoint())


if __name__ == "__main__":
    unittest.main()
