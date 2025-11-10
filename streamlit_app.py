# streamlit_app.py
# Inventory Dashboard — Streamlit (AI chat; no barcode/detailed reports/nav; no Inventory Snapshot)

import os
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat. App still loads without a key; chat shows a message instead.
try:
    import openai
except Exception:
    openai = None


# =============================================================================
# PAGE CONFIG + STYLES
# =============================================================================
st.set_page_config(
    page_title="Inventory Control Dashboard",
    page_icon="📦",
    layout="wide",
)

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
        .main {{ background: {PRIMARY_BG_GRADIENT}; }}
        .small-muted {{ color:#718b89; font-size:12px; }}
        .card {{ {CARD_STYLE} }}
        .chip {{
            display:inline-block;
            padding:4px 10px;
            font-size:12px;
            border-radius:12px;
            background:#ecf5f4;
            color:#2f5e59;
            margin-right:6px;
            border:1px solid #d2e8e6;
        }}
        hr {{
            margin: 8px 0 6px 0;
            border-color:#e7eeed;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# DATA LOADING
# =============================================================================
DATA_DIR = "data"


def read_csv_clean(path: str):
    """Load CSV safely with stripped headers."""
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None


products = read_csv_clean(os.path.join(DATA_DIR, "products.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))


# Fallback demo data
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


# =============================================================================
# CLEAN & DERIVED METRICS
# =============================================================================
for df in (products, sales, suppliers):
    df.columns = [c.strip() for c in df.columns]

sales.rename(columns={"ProductId": "Product_ID", "product_id": "Product_ID", "Units": "Qty"}, inplace=True)

if "Name" not in products.columns:
    products["Name"] = products["SKU"]

products["StockValue"] = products["Quantity"] * products["UnitPrice"]

# Key indicators
low_stock_items_count = int((products["Quantity"] < products["MinStock"]).sum())
low_stock_qty_total = int(products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum())
reorder_qty_total = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_qty_total = int(products["Quantity"].sum())

# Supplier totals by stock value
supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

# Sales extensions
sales_ext = sales.merge(products[["Product_ID", "Name", "Category", "SKU"]], on="Product_ID", how="left").copy()

if "Qty" not in sales_ext.columns:
    sales_ext["Qty"] = 1

sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum().sort_values("Qty", ascending=False)

if "Timestamp" in sales_ext.columns:
    sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)
else:
    sales_ext["Month"] = "2025-01"


# =============================================================================
# HELPERS
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    """Reusable gauge indicator."""
    max_value = max(max_value, 1)
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
                "steps": [{"range": [0, max_value], "color": "rgba(47,94,89,0.06)"}],
            },
            number={"font": {"size": 28, "color": "#1f3937"}},
        )
    )
    fig.update_layout(margin=dict(l=6, r=6, t=40, b=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def df_preview_text(df: pd.DataFrame, limit: int = 5) -> str:
    """Compact CSV-like preview for safe LLM context."""
    cols = ", ".join(map(str, df.columns))
    sample = df.head(limit).to_csv(index=False)
    return f"rows={len(df)}, cols=[{cols}]\npreview:\n{sample}"


# =============================================================================
# TOP SECTION — MENU / STOCK OVERVIEW / QUICK STATS
# =============================================================================
top_cols = st.columns([1.0, 2.0, 1.4], gap="large")

# Menu
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

# Stock Overview
with top_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px;'>Stock Overview</div>", unsafe_allow_html=True)
    gcols = st.columns(3)
    max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)

    with gcols[0]:
        st.plotly_chart(
            gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#e25d4f", max_kpi),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with gcols[1]:
        st.plotly_chart(
            gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#f0b429", max_kpi),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with gcols[2]:
        st.plotly_chart(
            gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", "#1ea97c", max_kpi),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    st.markdown("</div>", unsafe_allow_html=True)

# Quick Stats
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


# =============================================================================
# MIDDLE SECTION — SUPPLIER / SALES / SNAPSHOTS
# =============================================================================
mid_cols = st.columns([2.0, 1.3], gap="large")

# Supplier & Sales
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

    st.markdown("<hr>", unsafe_allow_html=True)

    legends = ["Acme Corp", "Innovate Ltd", "Global Goods", "Electronics", "Apparel", "Home Goods"]
    st.markdown("<div>" + "".join([f"<span class='chip'>{l}</span>" for l in legends]) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Snapshot card
with mid_cols[1]:
    st.markdown(
        f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Data Snapshots</div>
            <div class="small-muted">Updated: {datetime.now().strftime('%b %d, %Y')}</div>
            <hr/>
            <div style="{LABEL_STYLE}">Fast Facts</div>
            <ul style="margin-top:6px; color:#2b4a47;">
                <li>{low_stock_items_count} products below min stock</li>
                <li>{len(suppliers)} active suppliers</li>
                <li>{int(sales_ext['Qty'].sum())} units sold (YTD)</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# BOTTOM SECTION — CHAT ASSISTANT / TREND PERFORMANCE
# =============================================================================
bot_cols = st.columns([1.1, 2.3], gap="large")

# -- Chat setup
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
if openai and OPENAI_KEY:
    openai.api_key = OPENAI_KEY


def answer_query_llm(query: str) -> str:
    """LLM-powered query handler."""
    prod_ctx = df_preview_text(products)
    sales_ctx = df_preview_text(sales)
    supp_ctx = df_preview_text(suppliers)

    context = (
        "You are a precise data analyst. ONLY use the CSV context provided.\n"
        "Data:\n"
        f"[PRODUCTS]\n{prod_ctx}\n\n"
        f"[SALES]\n{sales_ctx}\n\n"
        f"[SUPPLIERS]\n{supp_ctx}\n\n"
        "If a figure is not derivable from the data above, say you cannot confirm it."
    )

    prompt = f"{context}\n\nUser question: {query}\nGive a concise, factual answer."

    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise, no-nonsense data analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Chat error: {e}"


# -- Chat Assistant
with bot_cols[0]:
    st.markdown(
        f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
            <div class="small-muted">Ask questions about inventory, suppliers, or sales.</div>
            <hr/>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_q = st.text_input("Type your question here:", key="chat_input")

    if user_q:
        if not openai or not OPENAI_KEY:
            st.warning("AI chat is disabled: missing OpenAI package or OPENAI_API_KEY secret.")
        else:
            with st.spinner("Analyzing data..."):
                st.success(answer_query_llm(user_q))
    else:
        st.info("Try: “Which supplier has the highest stock value?” or “What’s the Product_ID for iPhone 15?”")


# -- Trend Performance
with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)

    name_col = "Name" if "Name" in sales_ext.columns else "Category"
    qty_col = "Qty"

    series_df = sales_ext.groupby(["Month", name_col], as_index=False)[qty_col].sum()
    months_sorted = sorted(series_df["Month"].unique(), key=lambda x: pd.to_datetime(x))

    fig_trend = go.Figure()
    for label in series_df[name_col].unique():
        sub = series_df[series_df[name_col] == label].set_index("Month").reindex(months_sorted).fillna(0)
        fig_trend.add_trace(go.Scatter(x=months_sorted, y=sub[qty_col], mode="lines+markers", name=label))

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
