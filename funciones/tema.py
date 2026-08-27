import streamlit as st


TEMAS = {
    "light": {
        "fondo": "#F4F0E9",
        "panel": "#FFFDF8",
        "sidebar": "#ECE4DA",
        "texto": "#171514",
        "muted": "#756E67",
        "linea": "#D8CEC2",
        "sombra": "0 16px 42px rgba(72,18,26,0.08)",
        "control": "#FFFDF8",
    },
    "dark": {
        "fondo": "#151311",
        "panel": "#1F1B19",
        "sidebar": "#191614",
        "texto": "#F4F0E9",
        "muted": "#B9AFA5",
        "linea": "#3B342F",
        "sombra": "0 18px 48px rgba(0,0,0,0.28)",
        "control": "#292320",
    },
}


def tema_oscuro() -> bool:
    return st.session_state.get("tema_visual", 0) == 1


def aplicar_tema(modo: str) -> None:
    tema = TEMAS[modo]
    st.markdown(
        f"""
        <style>
        :root {{
          color-scheme: {modo};
        }}

        [data-testid="stAppViewContainer"],
        .stApp {{
          background:
            radial-gradient(circle at 88% 4%, rgba(179,111,61,0.08), transparent 28rem),
            {tema["fondo"]};
          color: {tema["texto"]};
        }}

        [data-testid="stHeader"] {{
          background: transparent;
        }}

        [data-testid="stSidebar"] {{
          background:
            linear-gradient(180deg, rgba(109,31,43,0.06), transparent 16rem),
            {tema["sidebar"]};
          border-right: 1px solid {tema["linea"]};
        }}

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"] {{
          color: {tema["texto"]};
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stMetricLabel"] {{
          color: {tema["muted"]};
        }}

        [data-testid="stMetric"] {{
          background: {tema["panel"]};
          border: 1px solid {tema["linea"]};
          border-radius: 16px;
          padding: 1rem 1.1rem;
          box-shadow: {tema["sombra"]};
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
          background: {tema["panel"]};
          border-color: {tema["linea"]};
          border-radius: 18px;
          box-shadow: {tema["sombra"]};
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stDateInput"] > div > div {{
          background-color: {tema["control"]};
          border-color: {tema["linea"]};
          color: {tema["texto"]};
        }}

        div[data-baseweb="select"] *,
        div[data-baseweb="input"] input {{
          color: {tema["texto"]};
        }}

        hr {{
          border-color: {tema["linea"]};
        }}

        .theme-labels {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin: 0.25rem 0 0.1rem;
          color: {tema["muted"]};
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }}

        [class*="st-key-tema_visual"] [data-testid="stSlider"] {{
          padding-top: 0;
        }}

        [class*="st-key-tema_visual"] [role="slider"] {{
          background: #B36F3D;
          border-color: #FFF8EC;
          box-shadow: 0 0 0 3px rgba(179,111,61,0.18);
        }}

        .stButton > button[kind="primary"] {{
          background: linear-gradient(135deg, #6D1F2B, #48121A);
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: 11px;
          box-shadow: 0 8px 22px rgba(72,18,26,0.24);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def configurar_tema() -> str:
    if "tema_visual" not in st.session_state:
        try:
            st.session_state.tema_visual = (
                1 if st.context.theme.type == "dark" else 0
            )
        except (AttributeError, RuntimeError):
            st.session_state.tema_visual = 0

    st.sidebar.markdown(
        """
        <div class="theme-labels">
          <span>☀️ Light</span>
          <span>Dark 🌙</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    valor = st.sidebar.slider(
        "Tema visual",
        min_value=0,
        max_value=1,
        step=1,
        key="tema_visual",
        label_visibility="collapsed",
    )
    modo = "dark" if valor == 1 else "light"
    aplicar_tema(modo)
    return modo
