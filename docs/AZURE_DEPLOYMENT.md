# Despliegue híbrido de Planta RILES

El proyecto tiene dos modos aislados:

- `local`: planillas en `datos/`, SQLite en `datos_generados/` y ejecución con
  `python tasks.py dev`.
- `cloud`: SharePoint como origen, PostgreSQL como base central y Azure App
  Service como servidor multiusuario.

El modo local es el predeterminado. Ninguna variable de Azure es necesaria
para desarrollar o probar el dashboard en un computador.

## 1. Recursos de Azure

Crear estos recursos en la misma región:

1. Azure Database for PostgreSQL Flexible Server.
2. Azure App Service Linux con Python 3.12 o superior.
3. Una App Registration en Microsoft Entra ID para acceso de solo lectura a
   los archivos de SharePoint.

Para reducir el alcance, se recomienda el permiso de aplicación
`Sites.Selected` y conceder acceso únicamente al sitio RILSA. El administrador
de Microsoft 365 debe aprobar ese permiso. No guardar el secreto en GitHub.

## 2. Identificadores de SharePoint

La sincronización usa Microsoft Graph y necesita:

- ID de la biblioteca de documentos (`drive-id`).
- ID del archivo `Planilla Procesos RILES.xlsx`.
- ID del archivo `Análisis Planta Aeróbica.xlsx`.

Se utilizan identificadores y no rutas para que mover o renombrar carpetas no
rompa la conexión.

## 3. Variables de App Service

Copiar las variables de `.env.example` en **Settings > Environment variables**
de Azure App Service:

```text
RILSA_APP_ENV=cloud
DATABASE_URL=postgresql+psycopg://...
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
SHAREPOINT_DRIVE_ID=...
SHAREPOINT_FISICO_ITEM_ID=...
SHAREPOINT_AEROBICO_ITEM_ID=...
RILSA_ENABLE_MANUAL_SYNC=false
WEBSITE_SKIP_RUNNING_KUDUAGENT=false
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

Activar **Always On** para que el WebJob programado funcione de forma fiable.

## 4. Inicio de Streamlit

Configurar el comando de inicio de App Service:

```bash
bash startup.sh
```

La aplicación escucha en `0.0.0.0` y usa el puerto entregado por Azure.

## 5. Sincronización

El WebJob incluido en `App_Data/jobs/triggered/sincronizar-rilsa/` ejecuta una
sincronización cada hora. Descarga las dos planillas en un directorio temporal,
valida los datos y reemplaza PostgreSQL dentro de una transacción.

Para ejecutar la primera sincronización desde la consola de App Service:

```bash
python tasks.py sincronizar-nube
```

También puede habilitarse temporalmente el botón del dashboard con
`RILSA_ENABLE_MANUAL_SYNC=true`. En producción conviene mantenerlo desactivado.

## 6. Acceso de usuarios

En **Authentication** de App Service, agregar Microsoft como proveedor de
identidad y exigir autenticación. Azure bloqueará el acceso antes de que la
solicitud llegue a Streamlit. Cada navegador mantendrá su propia sesión y sus
propios filtros, mientras todos consultan la misma base PostgreSQL.

## 7. Pruebas locales

El flujo local no cambia:

```bash
python tasks.py instalar
python tasks.py actualizar
python tasks.py dev
```

Para comprobar únicamente la configuración de nube desde un computador:

```bash
python tasks.py validar-config
python tasks.py dev-nube
```

No subir `.env`, credenciales, planillas ni bases de datos al repositorio.
