# streamlit_app.py
# Inventory Dashboard — Streamlit (single file, Streamlit Cloud ready)
# NOTE: No barcode/QR scanner, no detailed reports panel, and no navigation bar.

import os
from datetime import datetime
import re

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# Page + Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Inventory Control Dashboard",
    page_icon="📦",
    layout="wide",
)

# Custom CSS to replicate the look & feel
PRIMARY_BG_GRADIENT = """
linear-gradient(145deg, rgba(197,226,223,0.65) 0%, rgba(157,190,186,0.55) 35%,
rgba(124,164,160,0.50) 70%, rgba(108,150,146,0.45) 100%)
"""

CARD_STYLE = """
background: rgba(255,255,255,0.92);
backdrop-filter: blur(6px);
border-radius: 16px;
padding: 18px 18px 12px 18px;
box-shadow: 0 8px 24px rgba(22, 60, 56, 0.12);
"""

LABEL_STYLE = "color:#5b6b69; font-weight:600; font-size:13px; letter-spacing:.2px;"
TITLE_STYLE = "color:#1f3937; font-weight:700;"

st.markdown(
    f"""
    <style>
        .main {{
            background: {PRIMARY_BG_GRADIENT};
        }}
        .small-muted {{
            color:#718b89; font-size:12px;
        }}
        .card {{
            {CARD_STYLE}
        }}
        .chip {{
            display:inline-block; padding:4px 10px; font-size:12px; border-radius:12px;
            background:#ecf5f4; color:#2f5e59; margin-right:6px; border:1px solid #d2e8e6;
        }}
        hr {{
            margin: 8px 0 6px 0; border-color:#e7eeed;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data Loading (uses provided CSVs if present; otherwise creates small demo data)
# -----------------------------------------------------------------------------
DATA_DIR = "data"

def load_csv_or_none(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return None

products = load_csv_or_none(os.path.join(DATA_DIR, "products.csv"))
sales = load_csv_or_none(os.path.join(DATA_DIR, "sales.csv"))
suppliers = load_csv_or_none(os.path.join(DATA_DIR, "suppliers.csv"))

# Fallback demo data mirroring the screenshots if files are missing
if products is None:
    products = pd.DataFrame(
        {
            "Product_ID": [101, 102, 103, 104, 105],
            "SKU": ["IPH-15", "GS24", "MB-Air-M3", "LG-MSE", "AP-PR2"],
            "Name": ["iPhone 15", "Galaxy S24", "MacBook Air M3", "Logitech Mouse", "AirPods Pro"],
            "Category": ["Mobile", "Mobile", "Laptop", "Accessory", "Accessory"],
            "Quantity": [12, 30, 5, 3, 20],
            "MinStock": [15, 10, 8, 5, 10],
            "UnitPrice": [999, 899, 1299, 29, 249],
            "Supplier_ID": ["ACME", "GX", "ACME", "ACC", "ACME"],
        }
    )

if suppliers is None:
    suppliers = pd.DataFrame(
        {
            "Supplier_ID": ["ACME", "GX", "ACC"],
            "Supplier_Name": ["ACME Distribution", "GX Mobile", "Accessory House"],
            "Email": ["orders@acme.com", "gx@mobile.com", "hello@acc.com"],
            "Phone": ["+1-555-0100", "+1-555-0111", "+1-555-0122"],
        }
    )

if sales is None:
    sales = pd.DataFrame(
        {
            "Sale_ID": ["S-1001", "S-1002", "S-1003", "S-1004"],
            "Product_ID": [104, 101, 105, 102],
            "Qty": [2, 1, 3, 5],
            "UnitPrice": [29, 999, 249, 899],
            "Timestamp": ["2025-01-10", "2025-02-01", "2025-02-15", "2025-03-12"],
        }
    )

# Derived data
products = products.copy()
products["StockValue"] = products["Quantity"] * products["UnitPrice"]

# KPI calculations similar to the screenshot
low_stock_items = products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum()
reorder_qty = (products["MinStock"] - products["Quantity"]).clip(lower=0).sum()
in_stock_qty = int(products["Quantity"].sum())

# For “Top Suppliers” we’ll aggregate StockValue by supplier
supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

# Sales by category (based on product categories from sales)
sales_ext = sales.merge(products[["Product_ID", "Category", "Name"]], on="Product_ID", how="left")
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum().sort_values("Qty", ascending=False)

# Trend series (fake monthly series if needed)
if "Timestamp" in sales_ext:
    sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)
    trend = sales_ext.groupby(["Month", "Category"], as_index=False)["Qty"].sum()
else:
    trend = pd.DataFrame(
        {
            "Month": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"],
            "Category": ["Mobile", "Mobile", "Mobile", "Accessory", "Accessory", "Laptop"],
            "Qty": [80, 120, 95, 110, 130, 160],
        }
    )

# -----------------------------------------------------------------------------
# Helper: circular gauge (Plotly)
# -----------------------------------------------------------------------------
def gauge(title, value, subtitle, color, max_value):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"<b>{title}</b><br><span style='font-size:12px; color:#5b6b69;'>{subtitle}</span>"},
            gauge={
                "axis": {"range": [0, max_value], "tickwidth": 0},
                "bar": {"color": color, "thickness": 0.35},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [{"range": [0, max_value], "color": "rgba(47, 94, 89, 0.06)"}],
            },
            number={"font": {"size": 28, "color": "#1f3937"}},
        )
    )
    fig.update_layout(
        margin=dict(l=6, r=6, t=40, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# -----------------------------------------------------------------------------
# Layout — Three rows to match screenshot (minus barcode & detailed reports)
# -----------------------------------------------------------------------------
top_cols = st.columns([1.0, 2.0, 1.4], gap="large")

# LEFT: "Menu" look-alike card (static labels to mimic the screenshot; no navigation behavior)
with top_cols[0]:
    st.markdown(
        f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:22px; margin-bottom:10px;">Menu</div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <div class="chip">Dashboard</div>
                <div class="chip">Inventory</div>
                <div class="chip">Suppliers</div>
                <div class="chip">Orders</div>
                <div class="chip">Settings</div>
                <div class="chip">Chat Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# CENTER: Stock Overview (three gauges)
with top_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px;'>Stock Overview</div>", unsafe_allow_html=True)
    gcols = st.columns(3)
    max_kpi = max(in_stock_qty, reorder_qty if reorder_qty > 0 else 1, low_stock_items if low_stock_items > 0 else 1)
    with gcols[0]:
        st.plotly_chart(gauge("Low Stock", int(low_stock_items), f"{int((products['Quantity'] < products['MinStock']).sum())} items", "#e25d4f", max_kpi), use_container_width=True, config={"displayModeBar": False})
    with gcols[1]:
        st.plotly_chart(gauge("Reorder", int(reorder_qty), f"{int(reorder_qty)} items", "#f0b429", max_kpi), use_container_width=True, config={"displayModeBar": False})
    with gcols[2]:
        st.plotly_chart(gauge("In Stock", int(in_stock_qty), f"{int(in_stock_qty)} items", "#1ea97c", max_kpi), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# RIGHT: (Intentionally blank to keep symmetry with removed barcode/detailed panels)
with top_cols[2]:
    st.markdown(
        f"""
        <div class="card" style="min-height:168px; display:flex; align-items:center; justify-content:center;">
            <div style="text-align:center;">
                <div style="{LABEL_STYLE}">Quick Stats</div>
                <div style="font-size:28px; {TITLE_STYLE}">{products['SKU'].nunique()} SKUs</div>
                <div class="small-muted">Total Stock Value: ${products['StockValue'].sum():,.0f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# MIDDLE ROW: Supplier & Sales Data (two slim cards side-by-side as in screenshot)
mid_cols = st.columns([2.0, 1.3], gap="large")

with mid_cols[0]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Supplier &amp; Sales Data</div>", unsafe_allow_html=True)

    subcols = st.columns(2)
    with subcols[0]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:4px;'>Top Suppliers (by stock value)</div>", unsafe_allow_html=True)
        fig_sup = px.bar(
            supplier_totals.head(4),
            x="StockValue",
            y="Supplier_Name",
            orientation="h",
            text="StockValue",
        )
        fig_sup.update_traces(texttemplate="$%{text:,}", textposition="outside")
        fig_sup.update_layout(
            margin=dict(l=0, r=6, t=4, b=6),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_visible=False,
            yaxis_title=None,
        )
        st.plotly_chart(fig_sup, use_container_width=True, config={"displayModeBar": False})

    with subcols[1]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:4px;'>Sales by Category (Qty)</div>", unsafe_allow_html=True)
        fig_cat = px.bar(sales_by_cat, x="Category", y="Qty", text="Qty")
        fig_cat.update_traces(textposition="outside")
        fig_cat.update_layout(
            margin=dict(l=6, r=6, t=4, b=6),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title=None,
            xaxis_title=None,
        )
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

    # Legend-like chips to mimic the screenshot look
    st.markdown("<hr>", unsafe_allow_html=True)
    legends = ["Acme Corp", "Innovate Ltd", "Global Goods", "Electronics", "Apparel", "Home Goods"]
    st.markdown(
        "<div>" + "".join([f"<span class='chip'>{l}</span>" for l in legends]) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

with mid_cols[1]:
    # Small card summarizing inventory movement (placeholder for compact detail)
    st.markdown(
        f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Data Snapshots</div>
            <div class="small-muted">Updated: {datetime.now().strftime('%b %d, %Y')}</div>
            <hr/>
            <div style="{LABEL_STYLE}">Fast Facts</div>
            <ul style="margin-top:6px; color:#2b4a47;">
                <li>{(products['Quantity'] < products['MinStock']).sum()} products below min stock</li>
                <li>{len(suppliers)} active suppliers</li>
                <li>{sales_ext['Qty'].sum() if 'Qty' in sales_ext else sales['Qty'].sum()} units sold (YTD)</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# BOTTOM ROW: Chat Assistant (left) & Trend Performance (right)
bot_cols = st.columns([1.1, 2.3], gap="large")

with bot_cols[0]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Chat Assistant</div>", unsafe_allow_html=True)
    user_input = st.text_input("Type your query…", key="chat_input", label_visibility="collapsed")

    def find_sku(query_text: str):
        # very small NL parser: look for 'sku CODE'
        m = re.search(r"sku[:\s\-]*([A-Za-z0-9\-]+)", query_text, flags=re.I)
        return m.group(1) if m else None

    if user_input:
        sku = find_sku(user_input)
        if sku:
            row = products.loc[products["SKU"].str.lower() == sku.lower()]
            if not row.empty:
                r = row.iloc[0]
                supp_name = suppliers.loc[suppliers["Supplier_ID"] == r["Supplier_ID"], "Supplier_Name"]
                supp_name = supp_name.iloc[0] if not supp_name.empty else r["Supplier_ID"]
                st.success(
                    f"SKU **{r['SKU']}** — **{int(r['Quantity'])}** units available. "
                    f"Supplier: **{supp_name}**. Unit price: **${int(r['UnitPrice']):,}**."
                )
            else:
                st.warning("SKU not found.")
        else:
            st.info("Try: `Check stock for SKU IPH-15` or `Do we have SKU GS24?`")
    else:
        st.caption("Tip: Ask about a SKU to get live stock and supplier info.")

    st.markdown("</div>", unsafe_allow_html=True)

with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)

    # Build a clean two/three-series line chart like the mockup
    # Prepare a monthly pivot for top-selling products (by Name) if available
    month_label = "Month"
    if "Month" not in sales_ext.columns:
        sales_ext["Month"] = "2025-01"

    top_items = (
        sales_ext.merge(products[["Product_ID", "Name"]], on="Product_ID", how="left")
        .groupby("Name")["Qty"].sum()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )
    series_df = (
        sales_ext.merge(products[["Product_ID", "Name"]], on="Product_ID", how="left")
        .query("Name in @top_items")
        .groupby(["Month", "Name"], as_index=False)["Qty"].sum()
    )

    # Ensure chronological order
    def sort_period(s):
        try:
            return pd.to_datetime(s, format="%Y-%m").sort_values()
        except Exception:
            return pd.to_datetime(s).sort_values()

    months_sorted = sorted(series_df["Month"].unique(), key=lambda x: pd.to_datetime(x))
    fig_trend = go.Figure()
    for name in series_df["Name"].unique():
        sub = series_df[series_df["Name"] == name].set_index("Month").reindex(months_sorted).fillna(0)
        fig_trend.add_trace(
            go.Scatter(
                x=months_sorted,
                y=sub["Qty"],
                mode="lines+markers",
                name=name,
            )
        )

    fig_trend.update_layout(
        margin=dict(l=6, r=6, t=8, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title=None,
        legend_title_text="Top-Selling Products",
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Small bottom table preview similar to an "Inventory" peek (optional but handy)
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="card" style="margin-top:10px;">
        <div style="{TITLE_STYLE}; font-size:16px; margin-bottom:6px;">Inventory Snapshot</div>
        <div class="small-muted">A compact view of products to mirror the professional dashboard style.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.dataframe(
    products[["SKU", "Name", "Category", "Quantity", "MinStock", "UnitPrice"]]
    .sort_values(["Category", "Name"])
    .rename(columns={"UnitPrice": "Unit Price ($)"}),
    use_container_width=True,
    hide_index=True,
)
