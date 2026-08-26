"""Brand palette and typography. See business-rules.md BR-P1, BR-P2."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from bwace.engine.models import Category, RiskBand


@dataclass(frozen=True)
class PaletteRole:
    role: str
    hex: str
    permitted_uses: tuple[str, ...]


@dataclass(frozen=True)
class CategoryStyle:
    category: Category
    label: str
    colour: str
    text_colour_on_fill: str
    icon: str


# Every hex here is contrast-verified in tests/app/test_theme_contrast.py, which
# recomputes the ratios rather than trusting a table (BR-P1.4c).
PALETTE: dict[str, PaletteRole] = {
    "app_background": PaletteRole("app_background", "#f4f6fa", ("fill",)),
    "card": PaletteRole("card", "#ffffff", ("fill",)),
    "card_border": PaletteRole("card_border", "#d0d7e6", ("border",)),
    "gridline": PaletteRole("gridline", "#e3e8f0", ("border",)),
    "sidebar_background": PaletteRole("sidebar_background", "#eef4ff", ("fill",)),
    "sidebar_hover": PaletteRole("sidebar_hover", "#dce7ff", ("fill",)),
    "ink": PaletteRole("ink", "#001d6c", ("text_on_light",)),
    "ink_muted": PaletteRole("ink_muted", "#4c5a72", ("text_on_light",)),
    "accent": PaletteRole("accent", "#0050e6", ("fill", "border", "text_on_light")),
    "text_on_accent": PaletteRole("text_on_accent", "#ffffff", ("text_on_dark",)),
    "warm_neutral": PaletteRole("warm_neutral", "#f9ecd9", ("fill",)),
    "category_rebuild": PaletteRole("category_rebuild", "#02462f", ("fill", "border", "text_on_light")),
    "category_replicate": PaletteRole("category_replicate", "#82ce71", ("fill", "border")),
    "category_decommission": PaletteRole("category_decommission", "#9c4f1f", ("fill", "border", "text_on_light")),
}

_CATEGORY_STYLES: dict[Category, CategoryStyle] = {
    Category.REBUILD_AS_DATA_PRODUCT: CategoryStyle(
        category=Category.REBUILD_AS_DATA_PRODUCT, label="Rebuild as Data Product",
        colour=PALETTE["category_rebuild"].hex,
        text_colour_on_fill=PALETTE["text_on_accent"].hex, icon="\U0001F527",
    ),
    Category.REPLICATE_AS_IS: CategoryStyle(
        category=Category.REPLICATE_AS_IS, label="Replicate As-Is",
        colour=PALETTE["category_replicate"].hex,
        text_colour_on_fill=PALETTE["category_rebuild"].hex, icon="\U0001F4E6",
    ),
    Category.DECOMMISSION: CategoryStyle(
        category=Category.DECOMMISSION, label="Decommission",
        colour=PALETTE["category_decommission"].hex,
        text_colour_on_fill=PALETTE["text_on_accent"].hex, icon="\U0001F5D1",
    ),
}

_RISK_STYLES: dict[RiskBand, tuple[str, str]] = {
    RiskBand.LOW: (PALETTE["category_replicate"].hex, "Low"),
    RiskBand.MEDIUM: (PALETTE["category_decommission"].hex, "Medium"),
    RiskBand.HIGH: (PALETTE["category_rebuild"].hex, "High"),
}

FONT_STACK = "'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

CARD_RADIUS = "8px"


def palette() -> dict[str, PaletteRole]:
    return PALETTE


def category_style(category: Category) -> CategoryStyle:
    return _CATEGORY_STYLES[category]


def risk_style(band: RiskBand) -> tuple[str, str]:
    return _RISK_STYLES[band]


def _css() -> str:
    p = PALETTE
    app_bg, card, border = p["app_background"].hex, p["card"].hex, p["card_border"].hex
    ink, ink_muted, accent = p["ink"].hex, p["ink_muted"].hex, p["accent"].hex
    hover, on_accent = p["sidebar_hover"].hex, p["text_on_accent"].hex
    return f"""
        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
        }}
        .stApp {{
            background-color: {app_bg};
        }}
        h1, h2, h3 {{
            color: {ink};
            letter-spacing: -0.01em;
        }}
        /* Cards. Metrics, tables and charts all read as deliberate surfaces
           rather than bare white rectangles on the page background. */
        div[data-testid="stMetric"] {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: {CARD_RADIUS};
            padding: 14px 16px;
        }}
        div[data-testid="stMetric"] label {{
            color: {ink_muted};
        }}
        div[data-testid="stPlotlyChart"],
        div[data-testid^="stDataFrame"] {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: {CARD_RADIUS};
            padding: 8px;
        }}
        /* Sidebar navigation styled as a menu. The control is still st.radio, so
           active_view and every existing test key are unchanged; only the
           presentation differs. The radio circle is hidden and the row itself
           carries hover and selected state. */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {{
            gap: 2px;
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
            width: 100%;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid transparent;
            cursor: pointer;
            transition: background-color 120ms ease;
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
            background-color: {hover};
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:has(input[type="radio"]) {{
            display: none;
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {{
            background-color: {accent};
            border-left: 3px solid {ink};
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) * {{
            color: {on_accent} !important;
            font-weight: 600;
        }}
        /* Sidebar buttons get an explicit accessible pairing rather than relying
           on Streamlit's native white button blending into the light sidebar. */
        section[data-testid="stSidebar"] [data-testid^="stBaseButton"] {{
            background-color: {card};
            border: 1px solid {accent};
        }}
        section[data-testid="stSidebar"] [data-testid^="stBaseButton"] * {{
            color: {ink} !important;
        }}
        section[data-testid="stSidebar"] [data-testid^="stBaseButton"]:hover {{
            background-color: {accent};
        }}
        section[data-testid="stSidebar"] [data-testid^="stBaseButton"]:hover * {{
            color: {on_accent} !important;
        }}
        /* An expanded st.expander tints its header row; pin it to the sidebar
           colours so it stays legible. */
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
            background-color: {card} !important;
            color: {ink} !important;
        }}
        /* Section captions in the sidebar act as group labels for the nav,
           scoring and data blocks. */
        section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] {{
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }}
        /* Brand logo via st.logo(). It renders in the stSidebarHeader area
           (top-left of the full app frame) so it stays visible when the
           sidebar is collapsed. Override the React-applied inline max-height
           by targeting the img directly with higher specificity. */
        [data-testid="stSidebarHeader"] img,
        [data-testid="stSidebarCollapsedControl"] img {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 4px 10px;
            max-height: 48px !important;
            height: 48px !important;
            width: auto !important;
            object-fit: contain;
        }}
        [data-testid="stSidebarCollapsedControl"] img {{
            height: 32px !important;
            max-height: 32px !important;
            width: 32px !important;
            padding: 4px;
        }}
    """


def apply() -> None:
    # Native widget accents (nav radio, sliders, focus rings) come from the
    # [theme] block in .streamlit/config.toml, which injected CSS cannot reach.
    # This CSS covers only what config does not express. See BR-P1.7.
    st.set_page_config(page_title="BW-ACE", layout="wide")
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>{_css()}</style>
        """,
        unsafe_allow_html=True,
    )
