"""Core local data loading + normalization for ArcadiaReserve BI dashboard."""
from __future__ import annotations

import os
import re
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
        key=lambda p: (p.parent.as_posix().lower(), p.name.lower()),
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


def parse_datetime(values):
    text_values = pd.Series([values]) if not isinstance(values, pd.Series) else values.astype(str)
    iso_mask = text_values.astype(str).str.match(r"^\d{4}-\d{2}-\d{2}")
    if bool(iso_mask.all()):
        return pd.to_datetime(values, errors="coerce", dayfirst=False)
    try:
        return pd.to_datetime(values, errors="coerce", format="mixed", dayfirst=True)
    except TypeError:
        return pd.to_datetime(values, errors="coerce", dayfirst=True)


def normalize_colname(name: str) -> str:
    return (
        str(name).strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
    )


def pick_column(columns: Iterable[str], aliases: list[str]) -> str | None:
    normalized = {normalize_colname(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def normalize_tcg(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text or text in {"nan", "none", "unknown"}:
        return "Unknown"
    if "one piece" in text or re.search(r"\b(op|eb|st)\d{2}\b", text):
        return "One Piece"
    if "pokemon" in text or "pok\u00e9mon" in text or "poke mon" in text:
        return "Pokemon"
    if "magic" in text or "mtg" in text:
        return "Magic"
    if "yu-gi-oh" in text or "yugioh" in text or "yu gi oh" in text:
        return "Yu-Gi-Oh!"
    if "lorcana" in text:
        return "Lorcana"
    return str(value).strip() or "Unknown"


def add_tcg_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    candidates = [
        col
        for col in ["category", "set_name", "localized_product_name", "name", "source_file"]
        if col in out.columns
    ]
    if not candidates:
        out["tcg"] = "Unknown"
        return out

    tcg = pd.Series(["Unknown"] * len(out), index=out.index, dtype="object")
    for col in candidates:
        inferred = out[col].map(normalize_tcg)
        tcg = tcg.where(tcg != "Unknown", inferred)
    out["tcg"] = tcg.fillna("Unknown")
    return out


def read_flexible_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        attempts: list[tuple[str | None, str]] = [
            (None, "utf-8"),
            (";", "utf-8"),
            (",", "utf-8"),
            (None, "utf-8-sig"),
            (";", "utf-8-sig"),
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


def read_many_tables(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        try:
            frame = read_flexible_table(path)
        except Exception:
            continue
        if frame.empty:
            continue
        frame["source_file"] = path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


RARITY_LABELS = {
    "common",
    "uncommon",
    "rare",
    "super rare",
    "secret rare",
    "mythic",
    "mythic rare",
    "promo",
    "double rare",
    "illustration rare",
    "ultra rare",
    "special illustration rare",
    "holo rare",
    "shiny rare",
    "leader",
    "land",
}


def _split_pipe_values(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _parse_article_description(description: str) -> list[dict[str, object]]:
    """Parse Cardmarket shipment description into one row per sold article."""
    if not isinstance(description, str) or not description.strip():
        return []

    rows: list[dict[str, object]] = []
    for item_index, raw_item in enumerate(re.split(r"\s+\|\s+", description.strip())):
        item = raw_item.strip()
        if not item:
            continue

        qty_match = re.match(r"^(\d+)x\s+", item)
        quantity = int(qty_match.group(1)) if qty_match else 1
        details = item[qty_match.end():].strip() if qty_match else item

        price_match = re.search(r"(\d+[\.,]\d+)\s*EUR\s*$", details, flags=re.IGNORECASE)
        if price_match:
            unit_price = float(price_match.group(1).replace(",", "."))
            details = details[:price_match.start()].rstrip(" -")
        else:
            unit_price = float("nan")

        parts = [p.strip() for p in details.split(" - ") if p.strip()]
        title = parts[0] if parts else details
        card_number = parts[1] if len(parts) > 1 else ""
        condition = parts[-2] if len(parts) >= 3 else ""
        language = parts[-1] if len(parts) >= 2 else ""

        rarity = "Unknown"
        for token in parts[1:]:
            if token.lower() in RARITY_LABELS:
                rarity = token
                break

        parens = re.findall(r"\(([^()]*)\)", title)
        set_name = parens[-1].strip() if parens else "Unknown"
        name = re.sub(r"\s*\([^()]*\)", "", title).strip() or title.strip()

        for _ in range(max(quantity, 1)):
            rows.append({
                "price": unit_price,
                "name": name,
                "set_name": set_name,
                "rarity": rarity,
                "card_number": card_number,
                "condition": condition,
                "language": language,
                "item_index": item_index,
            })
    return rows


def _articles_from_shipments_export(df: pd.DataFrame, transaction_type: str = "sold") -> pd.DataFrame:
    description_col = pick_column(df.columns, ["description", "product_description", "items"])
    sold_date_col = pick_column(df.columns, ["date_of_purchase", "purchase_date", "date", "order_date"])
    order_id_col = pick_column(df.columns, ["orderid", "order_id", "shipment_nr"])
    product_id_col = pick_column(df.columns, ["product_id", "productid"])
    localized_name_col = pick_column(df.columns, ["localized_product_name", "product_name"])
    if not description_col:
        return pd.DataFrame()

    parsed_rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        sold_date = parse_datetime(row[sold_date_col]) if sold_date_col else pd.NaT
        product_ids = _split_pipe_values(row.get(product_id_col, "")) if product_id_col else []
        localized_names = _split_pipe_values(row.get(localized_name_col, "")) if localized_name_col else []

        for parsed in _parse_article_description(row.get(description_col, "")):
            item_index = int(parsed.pop("item_index", 0) or 0)
            parsed["sold_date"] = sold_date
            parsed["transaction_type"] = transaction_type
            parsed["order_id"] = str(row.get(order_id_col, "")) if order_id_col else ""
            parsed["product_id"] = product_ids[item_index] if item_index < len(product_ids) else ""
            if item_index < len(localized_names) and localized_names[item_index]:
                parsed["localized_product_name"] = localized_names[item_index]
            else:
                parsed["localized_product_name"] = parsed["name"]
            parsed_rows.append(parsed)

    if not parsed_rows:
        return pd.DataFrame()

    out = pd.DataFrame(parsed_rows)
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    return add_tcg_column(out.dropna(subset=["price"]).reset_index(drop=True))


def _metadata_from_shipments() -> pd.DataFrame:
    shipments = read_many_tables(select_source_files("orders"))
    parsed = _articles_from_shipments_export(shipments)
    if parsed.empty or "product_id" not in parsed.columns:
        return pd.DataFrame()
    cols = ["order_id", "product_id", "rarity", "condition", "language", "card_number"]
    return parsed[cols].drop_duplicates(subset=["order_id", "product_id"])


def _articles_from_articles_export(df: pd.DataFrame) -> pd.DataFrame:
    order_id_col = pick_column(df.columns, ["shipment_nr", "shipment_number", "orderid", "order_id"])
    sold_date_col = pick_column(df.columns, ["date_of_purchase", "purchase_date", "date", "sold_date"])
    article_col = pick_column(df.columns, ["article", "name", "card_name", "product"])
    product_id_col = pick_column(df.columns, ["product_id", "productid"])
    localized_col = pick_column(df.columns, ["localized_product_name", "product_name"])
    expansion_col = pick_column(df.columns, ["expansion", "set_name", "set"])
    category_col = pick_column(df.columns, ["category"])
    amount_col = pick_column(df.columns, ["amount", "quantity", "qty"])
    unit_price_col = pick_column(df.columns, ["article_value", "card_price", "price", "sold_price", "value"])
    total_col = pick_column(df.columns, ["total", "total_value", "line_total"])
    currency_col = pick_column(df.columns, ["currency"])
    comments_col = pick_column(df.columns, ["comments", "comment"])

    if not article_col or not unit_price_col:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    amounts = clean_numeric(df[amount_col]).fillna(1) if amount_col else pd.Series([1] * len(df))
    unit_prices = clean_numeric(df[unit_price_col])
    totals = clean_numeric(df[total_col]) if total_col else unit_prices * amounts
    sold_dates = parse_datetime(df[sold_date_col]) if sold_date_col else pd.Series([pd.NaT] * len(df))

    for idx, row in df.iterrows():
        quantity = int(amounts.iloc[idx]) if pd.notna(amounts.iloc[idx]) else 1
        quantity = max(quantity, 1)
        unit_price = unit_prices.iloc[idx]
        if pd.isna(unit_price):
            continue
        base = {
            "price": float(unit_price),
            "line_total": float(totals.iloc[idx]) if pd.notna(totals.iloc[idx]) else float(unit_price) * quantity,
            "quantity": quantity,
            "name": str(row.get(article_col, "Unknown")).strip() or "Unknown",
            "localized_product_name": str(row.get(localized_col, row.get(article_col, "Unknown"))).strip() if localized_col else str(row.get(article_col, "Unknown")).strip(),
            "set_name": str(row.get(expansion_col, "Unknown")).strip() if expansion_col else "Unknown",
            "category": str(row.get(category_col, "")).strip() if category_col else "",
            "rarity": "Unknown",
            "sold_date": sold_dates.iloc[idx],
            "transaction_type": "sold",
            "order_id": str(row.get(order_id_col, "")).strip() if order_id_col else "",
            "product_id": str(row.get(product_id_col, "")).strip() if product_id_col else "",
            "currency": str(row.get(currency_col, "EUR")).strip() if currency_col else "EUR",
            "comments": str(row.get(comments_col, "")).strip() if comments_col else "",
        }
        for _ in range(quantity):
            rows.append(base.copy())

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    metadata = _metadata_from_shipments()
    if not metadata.empty and {"order_id", "product_id"}.issubset(out.columns):
        out = out.merge(metadata, on=["order_id", "product_id"], how="left", suffixes=("", "_shipment"))
        for col in ("rarity", "condition", "language", "card_number"):
            shipment_col = f"{col}_shipment"
            if shipment_col in out.columns:
                out[col] = out[shipment_col].combine_first(out[col]) if col in out.columns else out[shipment_col]
                out = out.drop(columns=[shipment_col])
    out["rarity"] = out["rarity"].fillna("Unknown")
    return add_tcg_column(out.reset_index(drop=True))


def discover_files(kind: str) -> list[Path]:
    root = DATA_DIR
    scoped = root / kind

    scoped_files = iter_files(scoped, TABULAR_EXTENSIONS) if scoped.exists() else []
    if scoped_files:
        return scoped_files

    all_files = iter_files(root, TABULAR_EXTENSIONS)
    kind_tokens = {
        "orders": ("sold shipment", "sold_shipments", "sold-shipment", "sold order", "order", "shipment"),
        "articles": ("sold article", "sold_articles", "sold-article", "article", "card"),
        "expenses": ("expense", "cost", "purchased", "purchase"),
    }
    tokens = kind_tokens.get(kind, ())
    filtered = [p for p in all_files if any(token in p.as_posix().lower() for token in tokens)]
    return filtered or all_files


def _file_key(path: Path) -> str:
    """Filename key for matching export types without treating byPurchaseDate as purchases."""
    return path.name.lower().replace("purchasedate", "")


def select_source_files(kind: str) -> list[Path]:
    files = discover_files(kind)

    if kind == "orders":
        candidates = [
            p for p in files
            if p.suffix.lower() in CSV_EXTENSIONS
            and "expense" not in _file_key(p)
            and "purchased" not in _file_key(p)
            and "purchase order" not in _file_key(p)
            and "article" not in _file_key(p)
        ]
        shipments = [p for p in candidates if "sold" in _file_key(p) and "shipment" in _file_key(p)]
        orders = [p for p in candidates if "sold" in _file_key(p) and "order" in _file_key(p)]
        return shipments or orders or candidates

    if kind == "articles":
        candidates = [p for p in files if p.suffix.lower() in CSV_EXTENSIONS and "expense" not in _file_key(p)]
        articles = [p for p in candidates if "sold" in _file_key(p) and "article" in _file_key(p)]
        cards = [p for p in candidates if "card" in _file_key(p)]
        fallback = [p for p in candidates if "shipment" not in _file_key(p)]
        return articles or cards or fallback or candidates

    if kind == "expenses":
        scoped = DATA_DIR / "expenses"
        if scoped.exists():
            scoped_files = iter_files(scoped, TABULAR_EXTENSIONS)
            if scoped_files:
                return scoped_files
        return [
            p for p in files
            if p.suffix.lower() in TABULAR_EXTENSIONS
            and any(tag in _file_key(p) for tag in ("expense", "cost", "purchased", "purchase_order"))
        ]

    return files


# -----------------------------
# Domain loaders
# -----------------------------
@st.cache_data(ttl=3600)
def load_orders_data() -> pd.DataFrame:
    df = read_many_tables(select_source_files("orders"))
    if df.empty:
        return pd.DataFrame()

    date_col = pick_column(df.columns, ["date_of_purchase", "purchase_date", "date", "order_date"])
    merchandise_col = pick_column(df.columns, ["merchandise_value", "item_value", "items_value"])
    gross_col = pick_column(df.columns, ["total_value", "gross", "total", "order_total"])
    commission_col = pick_column(df.columns, ["commission", "fees", "fee"])
    shipping_col = pick_column(df.columns, ["shipment_costs", "shipping_costs", "shipping", "postage", "shipment"])
    country_col = pick_column(df.columns, ["country", "buyer_country", "destination_country"])
    order_id_col = pick_column(df.columns, ["orderid", "order_id", "shipment_nr"])
    article_count_col = pick_column(df.columns, ["article_count", "articles"])
    currency_col = pick_column(df.columns, ["currency"])

    value_col = merchandise_col or gross_col
    if not date_col or not value_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["date"] = parse_datetime(df[date_col])
    out["gross_value"] = clean_numeric(df[value_col])
    out["commission"] = clean_numeric(df[commission_col]) if commission_col else pd.NA
    out["shipping_cost"] = clean_numeric(df[shipping_col]) if shipping_col else pd.NA
    out["country"] = df[country_col].astype(str) if country_col else "Unknown"
    out["net_value"] = out["gross_value"] - out["commission"] if commission_col else pd.NA
    out["order_total"] = clean_numeric(df[gross_col]) if gross_col else pd.NA
    out["order_id"] = df[order_id_col].astype(str) if order_id_col else ""
    out["article_count"] = clean_numeric(df[article_count_col]) if article_count_col else pd.NA
    out["currency"] = df[currency_col].astype(str) if currency_col else "EUR"
    out["source_file"] = df["source_file"].astype(str) if "source_file" in df else ""
    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    return out


@st.cache_data(ttl=3600)
def load_articles_data() -> pd.DataFrame:
    df = read_many_tables(select_source_files("articles"))
    if df.empty:
        shipments = read_many_tables(select_source_files("orders"))
        return _articles_from_shipments_export(shipments, transaction_type="sold")

    if pick_column(df.columns, ["shipment_nr"]) and pick_column(df.columns, ["article_value"]):
        return _articles_from_articles_export(df)

    price_col = pick_column(df.columns, ["card_prices", "card_price", "price", "sold_price", "value"])
    name_col = pick_column(df.columns, ["name", "card_name", "article", "product", "localized_product_name"])
    set_col = pick_column(df.columns, ["set_names", "set_name", "set", "expansion"])
    rarity_col = pick_column(df.columns, ["card_rarities", "rarity"])
    sold_date_col = pick_column(df.columns, ["sold_date", "date_of_purchase", "date", "sale_date"])

    if not price_col:
        return _articles_from_shipments_export(df, transaction_type="sold")

    out = pd.DataFrame()
    out["price"] = clean_numeric(df[price_col])
    out["name"] = df[name_col].astype(str) if name_col else "Unknown"
    out["set_name"] = df[set_col].astype(str) if set_col else "Unknown"
    out["rarity"] = df[rarity_col].astype(str) if rarity_col else "Unknown"
    out["sold_date"] = parse_datetime(df[sold_date_col]) if sold_date_col else pd.NaT
    out["transaction_type"] = "sold"
    out["source_file"] = df["source_file"].astype(str) if "source_file" in df else ""
    out = out.dropna(subset=["price"]).reset_index(drop=True)
    return add_tcg_column(out)


@st.cache_data(ttl=3600)
def load_expenses_data() -> pd.DataFrame:
    expense_rows: list[dict[str, object]] = []

    purchase_df = read_many_tables(select_source_files("expenses"))
    if not purchase_df.empty:
        date_col = pick_column(purchase_df.columns, ["date_of_purchase", "order_date", "date", "purchase_date"])
        country_col = pick_column(purchase_df.columns, ["store_country", "country", "vendor_country"])
        order_id_col = pick_column(purchase_df.columns, ["orderid", "order_id", "shipment_nr"])
        merchandise_col = pick_column(purchase_df.columns, ["merchandise_value", "item_price", "price", "amount", "cost"])
        shipping_col = pick_column(purchase_df.columns, ["shipment_costs", "shipping_costs", "shipping", "postage", "shipment"])
        trustee_col = pick_column(purchase_df.columns, ["trustee_service_fee", "trustee_fee", "service_fee"])
        total_col = pick_column(purchase_df.columns, ["total_value", "order_total", "total"])
        category_col = pick_column(purchase_df.columns, ["cost_category", "category", "expense_type"])

        if date_col:
            order_dates = parse_datetime(purchase_df[date_col])
            countries = purchase_df[country_col].astype(str) if country_col else "Unknown"
            order_ids = purchase_df[order_id_col].astype(str) if order_id_col else ""
            totals = clean_numeric(purchase_df[total_col]) if total_col else pd.Series([pd.NA] * len(purchase_df))

            if category_col:
                price_col = merchandise_col or total_col
                values = clean_numeric(purchase_df[price_col]) if price_col else pd.Series([pd.NA] * len(purchase_df))
                categories = purchase_df[category_col].astype(str)
                components = [(None, None)]
            else:
                components = [
                    ("Inventory Purchase", merchandise_col),
                    ("Purchase Shipping", shipping_col),
                    ("Trustee Fee", trustee_col),
                ]

            for category, column in components:
                if category_col:
                    values_iter = values
                elif column:
                    values_iter = clean_numeric(purchase_df[column])
                else:
                    continue

                for idx in range(len(purchase_df)):
                    value = values_iter.iloc[idx]
                    order_date = order_dates.iloc[idx]
                    if pd.isna(order_date) or pd.isna(value) or float(value) == 0.0:
                        continue
                    expense_rows.append({
                        "order_date": order_date,
                        "item_price": float(value),
                        "cost_category": categories.iloc[idx] if category_col else category,
                        "store_country": countries.iloc[idx] if hasattr(countries, "iloc") else countries,
                        "source_type": "purchase",
                        "order_id": order_ids.iloc[idx] if hasattr(order_ids, "iloc") else order_ids,
                        "order_total": totals.iloc[idx] if hasattr(totals, "iloc") else totals,
                    })

    sales_df = read_many_tables(select_source_files("orders"))
    if not sales_df.empty:
        date_col = pick_column(sales_df.columns, ["date_of_purchase", "purchase_date", "date", "order_date"])
        commission_col = pick_column(sales_df.columns, ["commission", "fees", "fee"])
        country_col = pick_column(sales_df.columns, ["country", "buyer_country", "destination_country"])
        order_id_col = pick_column(sales_df.columns, ["orderid", "order_id", "shipment_nr"])
        if date_col and commission_col:
            order_dates = parse_datetime(sales_df[date_col])
            countries = sales_df[country_col].astype(str) if country_col else "Unknown"
            order_ids = sales_df[order_id_col].astype(str) if order_id_col else ""
            commissions = clean_numeric(sales_df[commission_col])
            for idx in range(len(sales_df)):
                value = commissions.iloc[idx]
                order_date = order_dates.iloc[idx]
                if pd.isna(order_date) or pd.isna(value) or float(value) == 0.0:
                    continue
                expense_rows.append({
                    "order_date": order_date,
                    "item_price": float(value),
                    "cost_category": "Sales Commission",
                    "store_country": countries.iloc[idx] if hasattr(countries, "iloc") else countries,
                    "source_type": "sale",
                    "order_id": order_ids.iloc[idx] if hasattr(order_ids, "iloc") else order_ids,
                    "order_total": pd.NA,
                })

    if not expense_rows:
        return pd.DataFrame()

    out = pd.DataFrame(expense_rows)
    out = out.dropna(subset=["order_date", "item_price"]).sort_values("order_date").reset_index(drop=True)
    out["month"] = out["order_date"].dt.to_period("M").dt.to_timestamp()
    return out


def get_data_diagnostics() -> dict[str, object]:
    files = [p.relative_to(DATA_DIR).as_posix() for p in iter_files(DATA_DIR, TABULAR_EXTENSIONS)]
    selected_files = {
        kind: [p.relative_to(DATA_DIR).as_posix() if DATA_DIR in p.parents else str(p) for p in select_source_files(kind)]
        for kind in ("orders", "articles", "expenses")
    }

    dataset_rows: dict[str, int | None] = {}
    for kind, loader in (
        ("orders", load_orders_data),
        ("articles", load_articles_data),
        ("expenses", load_expenses_data),
    ):
        try:
            dataset_rows[kind] = len(loader())
        except Exception:
            dataset_rows[kind] = None

    return {
        "data_dir_env": DATA_DIR_ENV,
        "data_dir": str(DATA_DIR),
        "exists": DATA_DIR.exists(),
        "files": files,
        "selected_files": selected_files,
        "dataset_rows": dataset_rows,
    }


def refresh_data() -> None:
    st.cache_data.clear()


def render_data_reload_button(*, key: str) -> None:
    with st.sidebar:
        if st.button("Data opnieuw laden", key=key, width="stretch"):
            refresh_data()
            st.rerun()






