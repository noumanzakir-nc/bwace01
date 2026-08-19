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


PALETTE: dict[str, PaletteRole] = {
    "app_background": PaletteRole("app_background", "#f2f7f1", ("fill",)),
    "card": PaletteRole("card", "#ffffff", ("fill",)),
    "header": PaletteRole("header", "#02462f", ("fill", "text_on_light")),
    "header_text": PaletteRole("header_text", "#ffffff", ("text_on_dark",)),
    "heading": PaletteRole("heading", "#0d6a4b", ("text_on_light",)),
    "accent": PaletteRole("accent", "#82ce71", ("fill", "border", "text_on_dark")),
    "warm_neutral": PaletteRole("warm_neutral", "#f6eeee", ("fill",)),
    "category_rebuild": PaletteRole("category_rebuild", "#02462f", ("fill", "border", "text_on_light")),
    "category_replicate": PaletteRole("category_replicate", "#82ce71", ("fill", "border")),
    "category_decommission": PaletteRole("category_decommission", "#9c4f1f", ("fill", "border", "text_on_light")),
}

_CATEGORY_STYLES: dict[Category, CategoryStyle] = {
    Category.REBUILD_AS_DATA_PRODUCT: CategoryStyle(
        category=Category.REBUILD_AS_DATA_PRODUCT, label="Rebuild as Data Product",
        colour=PALETTE["category_rebuild"].hex, text_colour_on_fill="#ffffff", icon="\U0001F527",
    ),
    Category.REPLICATE_AS_IS: CategoryStyle(
        category=Category.REPLICATE_AS_IS, label="Replicate As-Is",
        colour=PALETTE["category_replicate"].hex, text_colour_on_fill="#02462f", icon="\U0001F4E6",
    ),
    Category.DECOMMISSION: CategoryStyle(
        category=Category.DECOMMISSION, label="Decommission",
        colour=PALETTE["category_decommission"].hex, text_colour_on_fill="#ffffff", icon="\U0001F5D1",
    ),
}

_RISK_STYLES: dict[RiskBand, tuple[str, str]] = {
    RiskBand.LOW: (PALETTE["category_replicate"].hex, "Low"),
    RiskBand.MEDIUM: (PALETTE["category_decommission"].hex, "Medium"),
    RiskBand.HIGH: (PALETTE["category_rebuild"].hex, "High"),
}

FONT_STACK = "'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def palette() -> dict[str, PaletteRole]:
    return PALETTE


def category_style(category: Category) -> CategoryStyle:
    return _CATEGORY_STYLES[category]


def risk_style(band: RiskBand) -> tuple[str, str]:
    return _RISK_STYLES[band]


def apply() -> None:
    st.set_page_config(page_title="BW-ACE", layout="wide")
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
        }}
        .stApp {{
            background-color: {PALETTE['app_background'].hex};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {PALETTE['header'].hex};
            color: {PALETTE['header_text'].hex};
        }}
        section[data-testid="stSidebar"] * {{
            color: {PALETTE['header_text'].hex};
        }}
        h1, h2, h3 {{
            color: {PALETTE['heading'].hex};
        }}
        div[data-testid="stMetric"], div[data-testid="stDataFrame"] {{
            background-color: {PALETTE['card'].hex};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
