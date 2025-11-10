# streamlit_app.py — professional design, same logic, fixed Plotly margin error

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat (kept unchanged)
try:
    import openai
except Exception:
    openai = None


# =============================================================================
# PAGE CONFIGURATION & GLOBAL STYLES
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

# --- Theme styling ---
PRIMARY_BG_GRADIENT = """
linear-gradient(145deg,
rgba(233,245,243,1) 0%,
rgba(214,233,230,1) 40%,
rgba(190,222,218,1) 70%,
rgba(173,211,208,1) 100%)
"""

CARD_STYLE = """
background: rgba(255,255,255,0.92);
backdrop-filter: blur(10px);
border-radius: 18px;
padding: 22px 22px 16px 22px;
box-shadow: 0 10px 30px rgba(20, 60, 55, 0.12);
transition: all 0.3s ease;
"""

LABEL_STYLE = "color:#607472; font-weight:600; font-size:13px; letter-spacing:.2px;"
TITLE_STYLE = "color:#153733; font-weight:700;"
ACCENT_COLOR = "#1ea97c"

# --- CSS injection ---
st.markdown(
    f"""
    <style>
        .main {{
            background: {PRIMARY_BG_GRADIENT};
            font-family: 'Inter', sans-serif;
            color: #1f3937;
        }}
        .stTextInput > div > div > input {{
            background-color: #ffffff;
            border: 1px solid #d9e5e4;
            border-radius: 10px;
            padding: 8px 10px;
            color: #1f3937;
        }}
        .stTextInput > div > div > input:focus {{
            border-color: {ACCENT_COLOR};
            box-shadow: 0 0 0 2px rgba(30,169,124,0.15);
        }}
        .stButton button {{
            background-color: {ACCENT_COLOR};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 6px 14px;
            font-weight: 600;
            transition: 0.2s;
        }}
        .stButton button:hover {{
            background-color: #169b6e;
        }}
        .card {{
            {CARD_STYLE}
        }}
        .card:hover {{
            box-shadow: 0 12px 36px rgba(20, 60, 55, 0.18);
        }}
        .chip {{
            display:inline-block;
            padding:4px 10px;
            font-size:12px;
            border-radius:12px;
            background:#ebf7f5;
            color:#2f5e59;
            margin:3px;
            border:1px solid #d6ebe8;
        }}
        hr {{
            margin: 10px 0;
            border-color:#d8e8e6;
        }}
        .small-muted {{
            color:#708c88;
            font-size:12px;
        }}
        ul {{
            list-style-type: circle;
            padding-left: 20px;
        }}
        .metric-highlight {{
            color: {ACCENT_COLOR};
            font-weight: 600;
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
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

products = read_csv_clean(os.path.join(DATA_DIR, "products.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))

# --- Demo fallback ---
if products is None:
    products = pd.DataFrame({
        "Product_ID": [101, 102, 103, 104, 105],
        "SKU": ["IPH-15", "GS24", "MB-Air-M3", "LG-MSE", "AP-PR2"],
        "Name": ["iPhone 15", "Galaxy S24", "MacBook Air M3", "Logitech Mouse", "AirPods Pro"],
        "Category": ["Mobile", "Mobile", "Laptop", "Accessory", "Accessory"],
        "Quantity": [12, 30, 5, 3, 20],
        "MinStock": [15, 10, 8, 5, 10],
        "UnitPrice": [999, 899, 1299, 29, 249],
        "Supplier_ID": ["ACME", "GX", "ACME", "ACC", "ACME"],
    })

if suppliers is None:
    suppliers = pd.DataFrame({
        "Supplier_ID": ["ACME", "GX", "ACC"],
        "Supplier_Name": ["ACME Distribution", "GX Mobile", "Accessory House"],
        "Email": ["orders@acme.com", "gx@mobile.com", "hello@acc.com"],
        "Phone": ["+1-555-0100", "+1-555-0111", "+1-555-0122"],
    })

if sales is None:
    sales = pd.DataFrame({
        "Sale_ID": ["S-1001", "S-1002", "S-1003", "S-1004"],
        "Product_ID": [104, 101, 105, 102],
        "Qty": [2, 1, 3, 5],
        "UnitPrice": [29, 999, 249, 899],
        "Timestamp": ["2025-01-10", "2025-02-01", "2025-02-15", "2025-03-12"],
    })


# =============================================================================
# DATA CLEANING & METRICS
# =============================================================================
for df in (products, sales, suppliers):
    df.columns = [c.strip() for c in df.columns]

sales.rename(columns={"ProductId": "Product_ID", "product_id": "Product_ID", "Units": "Qty"}, inplace=True)
products["StockValue"] = products["Quantity"] * products["UnitPrice"]

low_stock_items_count = int((products["Quantity"] < products["MinStock"]).sum())
low_stock_qty_total = int(products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum())
reorder_qty_total = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_qty_total = int(products["Quantity"].sum())

supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

sales_ext = sales.merge(products[["Product_ID", "Name", "Category", "SKU"]], on="Product_ID", how="left")
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum()
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)


# =============================================================================
# REUSABLE COMPONENTS
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    max_value = max(max_value, 1)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={
            "text": f"<b>{title}</b><br><span style='font-size:12px; color:#607472;'>{subtitle}</span>",
            "font": {"size": 13},
        },
        gauge={
            "axis": {"range": [0, max_value], "tickwidth": 0},
            "bar": {"color": color, "thickness": 0.35},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [{"range": [0, max_value], "color": "rgba(50,90,85,0.07)"}],
        },
        number={"font": {"size": 28, "color": "#1f3937"}},
    ))
    fig.update_layout(margin=dict(l=6, r=6, t=20, b=0), paper_bgcolor="rgba(0,0,0,0)")  # FIXED LINE
    return fig


# =============================================================================
# DASHBOARD LAYOUT
# =============================================================================
top_cols = st.columns([1.0, 2.0, 1.4], gap="large")

# --- Menu
with top_cols[0]:
    st.markdown(f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:22px; margin-bottom:10px;">Menu</div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                {''.join(f"<div class='chip'>{c}</div>" for c in
                    ['Dashboard','Inventory','Suppliers','Orders','Settings','Chat Assistant'])}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Stock Overview
with top_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px;'>Stock Overview</div>", unsafe_allow_html=True)
    gcols = st.columns(3)
    max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)

    with gcols[0]:
        st.plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#e25d4f", max_kpi),
                        use_container_width=True, config={"displayModeBar": False})
    with gcols[1]:
        st.plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#f0b429", max_kpi),
                        use_container_width=True, config={"displayModeBar": False})
    with gcols[2]:
        st.plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR, max_kpi),
                        use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# --- Quick Stats
with top_cols[2]:
    st.markdown(f"""
        <div class="card" style="min-height:168px; display:flex; align-items:center; justify-content:center;">
            <div style="text-align:center;">
                <div style="{LABEL_STYLE}">Quick Stats</div>
                <div style="font-size:28px; {TITLE_STYLE}">{products['SKU'].nunique()} SKUs</div>
                <div class="small-muted">Total Stock Value: <span class="metric-highlight">${products['StockValue'].sum():,.0f}</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Supplier & Sales
mid_cols = st.columns([2.0, 1.3], gap="large")
with mid_cols[0]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    subcols = st.columns(2)

    with subcols[0]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:4px;'>Top Suppliers</div>", unsafe_allow_html=True)
        fig_sup = px.bar(supplier_totals, x="StockValue", y="Supplier_Name", orientation="h", text="StockValue")
        fig_sup.update_traces(texttemplate="$%{text:,}", textposition="outside")
        fig_sup.update_layout(margin=dict(l=0, r=6, t=4, b=6),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis_visible=False, yaxis_title=None)
        st.plotly_chart(fig_sup, use_container_width=True, config={"displayModeBar": False})

    with subcols[1]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:4px;'>Sales by Category</div>", unsafe_allow_html=True)
        fig_cat = px.bar(sales_by_cat, x="Category", y="Qty", text="Qty", color="Category",
                         color_discrete_sequence=["#1ea97c", "#f0b429", "#e25d4f", "#3498db"])
        fig_cat.update_traces(textposition="outside")
        fig_cat.update_layout(margin=dict(l=6, r=6, t=4, b=6),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              yaxis_title=None, xaxis_title=None, showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)

# --- Data Snapshot
with mid_cols[1]:
    st.markdown(f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Data Snapshot</div>
            <div class="small-muted">Updated: {datetime.now().strftime('%b %d, %Y')}</div>
            <hr/>
            <div style="{LABEL_STYLE}">Highlights</div>
            <ul>
                <li>{low_stock_items_count} products below minimum stock</li>
                <li>{len(suppliers)} active suppliers</li>
                <li>{int(sales_ext['Qty'].sum())} units sold YTD</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

# --- Chat + Trend
bot_cols = st.columns([1.1, 2.3], gap="large")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
if openai and OPENAI_KEY:
    openai.api_key = OPENAI_KEY

def answer_query_llm(query):
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":query}],
            temperature=0.2,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Chat error: {e}"

with bot_cols[0]:
    st.markdown(f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
            <div class="small-muted">Ask about inventory, suppliers, or sales.</div>
            <hr/>
        </div>
    """, unsafe_allow_html=True)

    user_q = st.text_input("Type your question here:", key="chat_input")
    if user_q:
        if not openai or not OPENAI_KEY:
            st.warning("AI chat is disabled (missing OpenAI key).")
        else:
            with st.spinner("Analyzing data..."):
                st.success(answer_query_llm(user_q))
    else:
        st.info("Try: 'Which supplier has the highest stock value?'")

# --- Trend Performance
with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    series_df = sales_ext.groupby(["Month", "Name"], as_index=False)["Qty"].sum()
    months_sorted = sorted(series_df["Month"].unique(), key=lambda x: pd.to_datetime(x))
    fig_trend = go.Figure()
    for label in series_df["Name"].unique():
        sub = series_df[series_df["Name"] == label].set_index("Month").reindex(months_sorted).fillna(0)
        fig_trend.add_trace(go.Scatter(x=months_sorted, y=sub["Qty"], mode="lines+markers", name=label))
    fig_trend.update_layout(
        margin=dict(l=6, r=6, t=8, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None, yaxis_title=None, legend_title_text="Top-Selling Products",
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
