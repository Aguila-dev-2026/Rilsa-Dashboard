"""Estilos para imprimir la vista actual del dashboard, no un informe alternativo."""


def estilos_impresion_dashboard() -> str:
    """Oculta controles y detalle tabular; conserva métricas y gráfico filtrado."""
    return """
    <style>
      @media print {
        @page { size: auto; margin: 14mm; }
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
        [data-testid='stAppViewContainer'] {
          display: grid !important;
          grid-template-columns: 220px minmax(0, 1fr) !important;
          column-gap: 12mm !important;
          align-items: start !important;
        }
        [data-testid='stSidebar'] {
          display: block !important;
          visibility: visible !important;
          position: relative !important;
          grid-column: 1 !important;
          width: 220px !important;
          min-width: 220px !important;
          height: auto !important;
          transform: none !important;
          background: #ece4da !important;
          color: #171514 !important;
          border-right: 1px solid #c9bdb0 !important;
        }
        [data-testid='stMain'],
        [data-testid='stAppViewContainer'] .main {
          grid-column: 2 !important;
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
      }
    </style>
    """
