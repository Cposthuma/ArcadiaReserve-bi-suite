"""Core local data loading + normalization for ArcadiaReserve BI dashboard."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

DATA_DIR_ENV = os.getenv("DATA_DIR")

CSV_EXTENSIONS = (".csv",)
TABULAR_EXTENSIONS = (".csv", ".xlsx", ".xls", ".ods")


# -----------------------------
# Generic helpers
# -----------------------------
def resolve_data_dir() -> Path:
    """Resolve where local data files are loaded from."""
    module_root = Path(__file__).resolve().parent

    if DATA_DIR_ENV:
        configured = Path(DATA_DIR_ENV).expanduser()
        if configured.is_absolute():
            return configured
        for candidate in (Path.cwd() / configured, module_root / configured):
            if candidate.exists():
                return candidate.resolve()
        return (Path.cwd() / configured).resolve()

    for candidate in (Path.cwd() / "data", module_root / "data"):
        if candidate.exists():
            return candidate.resolve()
    return (Path.cwd() / "data").resolve()


DATA_DIR = resolve_data_dir()


def iter_files(root: Path, exts: tuple[str, ...]) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def clean_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    return (
        series.astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(r"\.(?=\d{3}(\D|$))", "", regex=True)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def normalize_colname(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def pick_column(columns: Iterable[str], aliases: list[str]) -> str | None:
    normalized = {normalize_colname(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def read_flexible_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        attempts: list[tuple[str | None, str]] = [
            (None, "utf-8"),
            (";", "utf-8"),
            (",", "utf-8"),
            (None, "latin-1"),
            (";", "latin-1"),
            (",", "latin-1"),
        ]
        for sep, enc in attempts:
            try:
                if sep is None:
                    return pd.read_csv(path, sep=None, engine="python", encoding=enc)
                return pd.read_csv(path, sep=sep, encoding=enc)
            except Exception:
                continue
        raise ValueError(f"CSV could not be parsed: {path}")

    if path.suffix.lower() == ".ods":
        return pd.read_excel(path, engine="odf")
    return pd.read_excel(path)


def discover_files(kind: str) -> list[Path]:
    root = DATA_DIR
    scoped = root / kind
    files: list[Path] = []
    if scoped.exists():
        files.extend(iter_files(scoped, TABULAR_EXTENSIONS))
    files.extend(iter_files(root, TABULAR_EXTENSIONS))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for item in files:
        key = str(item.resolve())
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


# -----------------------------
# Domain loaders
# -----------------------------
@st.cache_data(ttl=3600)
def load_orders_data() -> pd.DataFrame:
    files = discover_files("orders")
    candidates = [p for p in files if p.suffix.lower() in CSV_EXTENSIONS and "expense" not in p.name.lower()]
    preferred = [
        p for p in candidates
        if any(tag in p.name.lower() for tag in ("purchased", "purchase", "order"))
        and "sold" not in p.name.lower()
    ]
    if preferred:
        candidates = preferred
    if not candidates:
        return pd.DataFrame()

    df = read_flexible_table(candidates[0])

    date_col = pick_column(df.columns, ["date_of_purchase", "purchase_date", "date", "order_date"])
    gross_col = pick_column(df.columns, ["total_value", "gross", "total", "order_total"])
    commission_col = pick_column(df.columns, ["commission", "fees", "fee"])
    shipping_col = pick_column(df.columns, ["shipment_costs", "shipping_costs", "shipping", "postage"])
    country_col = pick_column(df.columns, ["country", "buyer_country", "destination_country"])

    if not date_col or not gross_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    out["gross_value"] = clean_numeric(df[gross_col])
    out["commission"] = clean_numeric(df[commission_col]) if commission_col else 0.0
    out["shipping_cost"] = clean_numeric(df[shipping_col]) if shipping_col else 0.0
    out["country"] = df[country_col].astype(str) if country_col else "Unknown"
    out["net_value"] = out["gross_value"].fillna(0) - out["commission"].fillna(0)
    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    return out


@st.cache_data(ttl=3600)
def load_articles_data() -> pd.DataFrame:
    files = discover_files("articles")
    candidates = [p for p in files if p.suffix.lower() in CSV_EXTENSIONS and "expense" not in p.name.lower()]
    preferred = [
        p for p in candidates
        if any(tag in p.name.lower() for tag in ("sold", "article", "card"))
    ]
    if preferred:
        candidates = preferred
    if not candidates:
        return pd.DataFrame()

    df = read_flexible_table(candidates[0])
    price_col = pick_column(df.columns, ["card_prices", "price", "sold_price", "value"])
    name_col = pick_column(df.columns, ["name", "card_name", "article", "product"])
    set_col = pick_column(df.columns, ["set_names", "set_name", "set"])
    rarity_col = pick_column(df.columns, ["card_rarities", "rarity"])
    sold_date_col = pick_column(df.columns, ["sold_date", "date", "sale_date"])

    if not price_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["price"] = clean_numeric(df[price_col])
    out["name"] = df[name_col].astype(str) if name_col else "Unknown"
    out["set_name"] = df[set_col].astype(str) if set_col else "Unknown"
    out["rarity"] = df[rarity_col].astype(str) if rarity_col else "Unknown"
    out["sold_date"] = pd.to_datetime(df[sold_date_col], errors="coerce", dayfirst=True) if sold_date_col else pd.NaT
    out = out.dropna(subset=["price"]).reset_index(drop=True)
    return out


@st.cache_data(ttl=3600)
def load_expenses_data() -> pd.DataFrame:
    files = discover_files("expenses")
    if not files:
        return pd.DataFrame()

    df = read_flexible_table(files[0])
    date_col = pick_column(df.columns, ["order_date", "date", "purchase_date"])
    price_col = pick_column(df.columns, ["item_price", "price", "amount", "cost"])
    category_col = pick_column(df.columns, ["cost_category", "category", "expense_type"])
    country_col = pick_column(df.columns, ["store_country", "country", "vendor_country"])

    if not date_col or not price_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["order_date"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    out["item_price"] = clean_numeric(df[price_col])
    out["cost_category"] = df[category_col].astype(str) if category_col else "Uncategorized"
    out["store_country"] = df[country_col].astype(str) if country_col else "Unknown"
    out = out.dropna(subset=["order_date", "item_price"]).sort_values("order_date").reset_index(drop=True)
    out["month"] = out["order_date"].dt.to_period("M").dt.to_timestamp()
    return out


def get_data_diagnostics() -> dict[str, object]:
    files = [p.relative_to(DATA_DIR).as_posix() for p in iter_files(DATA_DIR, TABULAR_EXTENSIONS)]
    return {
        "data_dir_env": DATA_DIR_ENV,
        "data_dir": str(DATA_DIR),
        "exists": DATA_DIR.exists(),
        "files": files,
    }


def refresh_data() -> None:
    st.cache_data.clear()


def render_data_reload_button(*, key: str) -> None:
    with st.sidebar:
        if st.button("🔄 Data opnieuw laden", key=key, use_container_width=True):
            refresh_data()
            st.rerun()
