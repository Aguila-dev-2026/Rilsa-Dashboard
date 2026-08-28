"""Estilos para imprimir la vista actual del dashboard, no un informe alternativo."""


def estilos_impresion_dashboard() -> str:
    """Oculta controles y detalle tabular; conserva métricas y gráfico filtrado."""
    return """
    <style>
      @media print {
        @page { size: auto; margin: 14mm; }
        :root {
          --fondo: #FFFFFF !important;
          --panel: #FFFFFF !important;
          --panel-sec: #FFFFFF !important;
          --texto: #171514 !important;
          --muted: #52627C !important;
          --linea: #DCE5EF !important;
        }
        html, body {
          background: #fff !important;
          color: #171514 !important;
          color-scheme: light !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
        header, footer, [data-testid='stToolbar'] {
          display: none !important;
        }
        [data-testid='stSidebar'] {
          display: none !important;
        }
        [data-testid='stMain'],
        [data-testid='stAppViewContainer'] .main {
          width: 100% !important;
          min-width: 0 !important;
          margin-left: 0 !important;
        }
        .riles-tabla-titulo,
        [data-testid='stElementContainer']:has([data-testid='stDataFrame']),
        .stElementContainer:has([data-testid='stDataFrame']) {
          display: none !important;
        }
        [data-testid='stPlotlyChart'],
        [data-testid='stPlotlyChart'] > div,
        iframe[title='components.html'] {
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
        }
        [data-testid='stAppViewContainer'],
        [data-testid='stAppViewContainer'] .main,
        [data-testid='stAppViewContainer'] .block-container {
          background: #fff !important;
          color: #171514 !important;
        }
        [data-testid='stMetric'],
        [data-testid='stVerticalBlockBorderWrapper'],
        [data-testid='stPlotlyChart'] {
          background: #fff !important;
          border-color: #DCE5EF !important;
          box-shadow: none !important;
        }
        .js-plotly-plot .xtick text,
        .js-plotly-plot .ytick text,
        .js-plotly-plot .gtitle,
        .js-plotly-plot .legendtext,
        .js-plotly-plot .ytitle {
          fill: #332E2A !important;
        }
      }
    </style>
    """
