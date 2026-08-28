# Plan temporal de refactorización

Este documento registra las mejoras estructurales que se aplicarán por etapas.
No reemplaza el `README.md` principal y se eliminará cuando el plan haya sido
completado o trasladado a la documentación definitiva.

## Objetivo

Mantener el dashboard funcional mientras se mejora la separación de
responsabilidades, la reutilización de código y la facilidad de pruebas.

Cada etapa importante debe terminar con:

- código funcionando;
- pruebas existentes pasando, o una explicación documentada si falta una dependencia;
- revisión de imports y referencias;
- `git diff --check` limpio;
- un commit independiente con un mensaje descriptivo.

## Etapa 1 — Centralizar tema y estilos

Crear un módulo común para colores, fuentes, estilos de Plotly y detección del
tema claro/oscuro.

Ubicación prevista:

```text
funciones/ui/tema.py
```

Extraer:

- paletas clara y oscura;
- colores corporativos;
- configuración común de gráficos;
- estilos reutilizables para tablas, botones y mensajes;
- estilos de impresión cuando sea posible.

Resultado esperado: ningún módulo nuevo debe definir nuevamente colores o
fuentes globales que ya existan en el tema común.

Commit sugerido: `Centralizar tema y estilos visuales`.

## Etapa 2 — Dividir `dashboard_area.py`

Reducir el tamaño de `funciones/dashboard_area.py`, que actualmente concentra
reglas de negocio, gráficos, tablas y componentes de Streamlit.

Separar inicialmente:

```text
funciones/graficos/
├── bandas.py
├── tendencias.py
├── estilos.py
└── render.py
```

La función pública `mostrar_dashboard_area()` debe conservar su comportamiento
para no romper las páginas existentes.

Commits sugeridos:

- `Separar cálculo de tendencias y bandas`.
- `Separar renderizado y estilos de gráficos`.

## Etapa 3 — Separar interfaz y lógica de dominio

Mover cálculos puros y validaciones a módulos que no importen Streamlit.

Ubicación prevista:

```text
funciones/dominio/
├── parametros.py
├── tendencias.py
└── validaciones.py
```

La capa de dominio debe recibir datos y devolver valores, estructuras o errores.
La capa `ui/` decidirá si los muestra mediante `st.info`, `st.error`, tablas o
gráficos.

Resultado esperado: las funciones de dominio podrán probarse sin ejecutar una
aplicación Streamlit.

Commit sugerido: `Separar lógica de dominio de la interfaz`.

## Etapa 4 — Extraer componentes reutilizables de Streamlit

Crear componentes compartidos para evitar repetir la construcción de controles
y secciones visuales.

Ubicación prevista:

```text
funciones/ui/
├── componentes.py
├── filtros.py
├── tablas.py
└── tema.py
```

Reutilizar especialmente:

- selección de fechas;
- selección de área, punto y parámetro;
- tablas con columnas visibles;
- contenedores de gráficos desplazables;
- mensajes de estado y actualización.

Commit sugerido: `Extraer componentes reutilizables de Streamlit`.

## Etapa 5 — Separar páginas del dashboard

Mantener `app.py` como coordinador y mover cada página a su propio módulo.

Estructura prevista:

```text
paginas/
├── fisico_quimico.py
├── planta_alta.py
├── planta_aerobica.py
└── efluente.py
```

`app.py` debería limitarse a configurar Streamlit, mostrar el menú, comprobar
la disponibilidad de datos y delegar en la página seleccionada.

Commit sugerido: `Separar páginas del dashboard`.

## Etapa 6 — Reorganizar la ingesta de datos

Agrupar los importadores y extraer utilidades comunes sin forzar una única
implementación para planillas con formatos diferentes.

Estructura prevista:

```text
ingesta/
├── comun.py
├── fisico_quimico.py
├── aerobico.py
└── validaciones.py
```

Reutilizar:

- normalización de nombres;
- conversión de valores;
- validación de columnas;
- generación de huellas y metadatos;
- mensajes y resultados de importación.

Commit sugerido: `Organizar importadores y utilidades de ingesta`.

## Etapa 7 — Mejorar la estructura de paquetes

Solo después de estabilizar las etapas anteriores, evaluar migrar a una
estructura de paquete explícita:

```text
src/
└── rilsa_dashboard/
    ├── config/
    ├── datos/
    ├── dominio/
    ├── ingesta/
    ├── paginas/
    ├── reportes/
    └── ui/
```

Esta etapa requiere actualizar imports, comandos de desarrollo y despliegue,
por lo que no debe hacerse antes de tener pruebas suficientes.

Commit sugerido: `Convertir el proyecto en un paquete explícito`.

## Reglas para cada etapa

1. No mezclar cambios visuales o funcionales no relacionados.
2. Mantener compatibilidad con los modos local y nube.
3. Extraer primero; eliminar funciones antiguas solo cuando no queden referencias.
4. Añadir o adaptar pruebas junto con cada extracción.
5. Revisar que los imports dinámicos de Streamlit, SharePoint y PostgreSQL sigan funcionando.
6. Hacer un commit por etapa importante y verificar el estado del árbol antes de continuar.

## Estado

- [x] Etapa 1 — Centralizar tema y estilos
- [ ] Etapa 2 — Dividir `dashboard_area.py`
- [ ] Etapa 3 — Separar interfaz y lógica de dominio
- [ ] Etapa 4 — Extraer componentes reutilizables
- [ ] Etapa 5 — Separar páginas
- [ ] Etapa 6 — Reorganizar ingesta
- [ ] Etapa 7 — Evaluar paquete `src/`
