# streamlit_app.py
# Inventory Dashboard — Streamlit (AI chat; aligned layout, no feature changes)

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI integration
try:
    import openai
except Exception:
    openai = None


# -----------------------------------------------------------------------------
# PAGE CONFIG & STYLES
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

st.markdown(
    """
    <style>
        .main {
            background: linear-gradient(145deg, rgba(197,226,223,0.65) 0%, rgba(157,190,186,0.55) 35%,
                        rgba(124,164,160,0.50) 70%, rgba(108,150,146,0.45) 100%);
        }
        .card {
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(6px);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 24px rgba(22, 60, 56, 0.12);
            margin-bottom: 20px;
        }
        .chip {
            display: inline-block;
            padding: 4px 10px;
            font-size: 12px;
            border-radius: 12px;
            background: #ecf5f4;
            color: #2f5e59;
            margin-right: 6px;
            margin-bottom: 6px;
            border: 1px solid #d2e8e6;
        }
        .title { color:#1f3937; font-weight:700; }
        .label { color:#5b6b69; font-weight:600; font-size:13px; letter-spacing:.2px; }
        .muted { color:#718b89; font-size:12px; }
        hr { margin: 8px 0 6px 0; border-color:#e7eeed; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------
DATA_DIR = "data"


def load_csv(path):
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None


products = load_csv(os.path.join(DATA_DIR, "products.csv"))
sales = load_csv(os.path.join(DATA_DIR, "sales.csv"))
suppliers = load_csv(os.path.join(DATA_DIR, "suppliers.csv"))


# -----------------------------------------------------------------------------
# FALLBACK DATA (if CSVs missing)
# -----------------------------------------------------------------------------
if products is None:
    products = pd.DataFrame({
        "Product_ID": [101, 102, 103, 104, 105],
        "SKU": ["IPH-15", "GS24", "MB-Air-M3", "LG-MSE", "AP-PR2"],
        "Name": ["iPhone 15", "Galaxy S24", "MacBook Air M3", "Logitech Mouse", "AirPods Pro"],
        "Category": ["Mobile", "Mobile", "Laptop", "Accessory", "Accessory"],
        "Quantity": [12, 30, 5, 3, 20],
        "MinStock": [15, 10, 8, 5, 10],
        "UnitPrice": [999, 899, 1299, 29, 249],
        "Supplier_ID": ["ACME", "GX", "ACME", "ACC", "ACME"]
    })

if suppliers is None:
    suppliers = pd.DataFrame({
        "Supplier_ID": ["ACME", "GX", "ACC"],
        "Supplier_Name": ["ACME Distribution", "GX Mobile", "Accessory House"],
        "Email": ["orders@acme.com", "gx@mobile.com", "hello@acc.com"],
        "Phone": ["+1-555-0100", "+1-555-0111", "+1-555-0122"]
    })

if sales is None:
    sales = pd.DataFrame({
        "Sale_ID": ["S-1001", "S-1002", "S-1003", "S-1004"],
        "Product_ID": [104, 101, 105, 102],
        "Qty": [2, 1, 3, 5],
        "UnitPrice": [29, 999, 249, 899],
        "Timestamp": ["2025-01-10", "2025-02-01", "2025-02-15", "2025-03-12"]
    })


# -----------------------------------------------------------------------------
# DATA CLEANUP
# -----------------------------------------------------------------------------
for df in (products, sales, suppliers):
    df.columns = [c.strip() for c in df.columns]

if "Name" not in products.columns:
    products["Name"] = products["SKU"]

sales.rename(columns={"ProductId": "Product_ID", "Units": "Qty"}, inplace=True)
products["StockValue"] = products["Quantity"] * products["UnitPrice"]


# -----------------------------------------------------------------------------
# METRICS
# -----------------------------------------------------------------------------
low_stock = (products["Quantity"] < products["MinStock"])
low_stock_items = int(low_stock.sum())
low_stock_qty = int(products.loc[low_stock, "Quantity"].sum())
reorder_qty = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_qty = int(products["Quantity"].sum())

supplier_value = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

sales_ext = sales.merge(products[["Product_ID", "Name", "Category", "SKU"]], on="Product_ID", how="left")
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum().sort_values("Qty", ascending=False)


# -----------------------------------------------------------------------------
# HELPER COMPONENTS
# -----------------------------------------------------------------------------
def gauge(title, value, subtitle, color, max_value):
    max_value = max(max_value, 1)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"<b>{title}</b><br><span style='font-size:12px; color:#5b6b69;'>{subtitle}</span>"},
            gauge={
                "axis": {"range": [0, max_value], "tickwidth": 0},
                "bar": {"color": color, "thickness": 0.35},
                "steps": [{"range": [0, max_value], "color": "rgba(47,94,89,0.06)"}],
            },
            number={"font": {"size": 28, "color": "#1f3937"}},
        )
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


# -----------------------------------------------------------------------------
# LAYOUT
# -----------------------------------------------------------------------------
# ====== TOP SECTION ======
col_menu, col_overview, col_stats = st.columns([1, 2, 1.4])

with col_menu:
    st.markdown("""
        <div class="card">
            <div class="title" style="font-size:22px;">Menu</div>
            <div style="margin-top:10px;">
                <div class="chip">Dashboard</div><div class="chip">Inventory</div>
                <div class="chip">Suppliers</div><div class="chip">Orders</div>
                <div class="chip">Settings</div><div class="chip">Chat Assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_overview:
    st.markdown(f"<div class='card'><div class='title' style='font-size:20px;'>Stock Overview</div>", unsafe_allow_html=True)
    kcols = st.columns(3)
    max_val = max(in_stock_qty, reorder_qty, low_stock_qty, 1)
    kcols[0].plotly_chart(gauge("Low Stock", low_stock_qty, f"{low_stock_items} items", "#e25d4f", max_val), use_container_width=True)
    kcols[1].plotly_chart(gauge("Reorder", reorder_qty, f"{reorder_qty} items", "#f0b429", max_val), use_container_width=True)
    kcols[2].plotly_chart(gauge("In Stock", in_stock_qty, f"{in_stock_qty} items", "#1ea97c", max_val), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_stats:
    st.markdown(f"""
        <div class="card" style="text-align:center;">
            <div class="label">Quick Stats</div>
            <div class="title" style="font-size:28px;">{products['SKU'].nunique()} SKUs</div>
            <div class="muted">Total Stock Value: ${products['StockValue'].sum():,.0f}</div>
        </div>
    """, unsafe_allow_html=True)


# ====== MIDDLE SECTION ======
col_left, col_right = st.columns([2, 1.2])

with col_left:
    st.markdown(f"<div class='card'><div class='title' style='font-size:18px;'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    sub1, sub2 = st.columns(2)

    # Suppliers chart
    fig1 = px.bar(supplier_value.head(4), x="StockValue", y="Supplier_Name", orientation="h", text="StockValue")
    fig1.update_traces(texttemplate="$%{text:,}", textposition="outside")
    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", xaxis_visible=False, yaxis_title=None)
    sub1.plotly_chart(fig1, use_container_width=True)

    # Sales chart
    fig2 = px.bar(sales_by_cat, x="Category", y="Qty", text="Qty")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", yaxis_title=None)
    sub2.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    chips = ["Acme Corp", "Innovate Ltd", "Global Goods", "Electronics", "Apparel", "Home Goods"]
    st.markdown("<div>" + "".join([f"<span class='chip'>{c}</span>" for c in chips]) + "</div></div>", unsafe_allow_html=True)

with col_right:
    st.markdown(f"""
        <div class="card">
            <div class="title" style="font-size:18px;">Data Snapshots</div>
            <div class="muted">Updated: {datetime.now().strftime('%b %d, %Y')}</div>
            <hr/>
            <div class="label">Fast Facts</div>
            <ul style="color:#2b4a47;">
                <li>{low_stock_items} products below min stock</li>
                <li>{len(suppliers)} active suppliers</li>
                <li>{int(sales_ext['Qty'].sum())} units sold (YTD)</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)


# ====== BOTTOM SECTION ======
col_chat, col_trend = st.columns([1.1, 2.3])

# Chat Assistant
with col_chat:
    st.markdown(f"""
        <div class="card">
            <div class="title" style="font-size:18px;">Chat Assistant</div>
            <div class="muted">Ask questions about inventory, suppliers, or sales.</div>
            <hr/>
        </div>
    """, unsafe_allow_html=True)

    st.text_input("Type your question here:", key="chat_input")
    st.info("Try: “Which supplier has the highest stock value?” or “What’s the Product_ID for iPhone 15?”")

# Trend Performance
with col_trend:
    st.markdown(f"<div class='card'><div class='title' style='font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    trend_df = sales_ext.groupby(["Month", "Name"], as_index=False)["Qty"].sum()
    months = sorted(trend_df["Month"].unique(), key=lambda x: pd.to_datetime(x))
    fig = go.Figure()
    for prod in trend_df["Name"].unique():
        sub = trend_df[trend_df["Name"] == prod].set_index("Month").reindex(months).fillna(0)
        fig.add_trace(go.Scatter(x=months, y=sub["Qty"], mode="lines+markers", name=prod))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", legend_title_text="Top-Selling Products")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
