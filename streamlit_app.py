# streamlit_app.py
# Inventory Dashboard — unified chat card (scrollable inside the same container)

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import openai
except Exception:
    openai = None

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

PRIMARY_COLOR = "#0077B6"
ACCENT_COLOR = "#1EA97C"
DARK_TEXT = "#1B4E4D"
MUTED_TEXT = "#4A7D7B"

CARD_STYLE = """
background: rgba(255,255,255,0.98);
backdrop-filter: blur(8px);
border-radius: 20px; 
padding: 22px 22px 16px 22px; 
box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08); 
border: 1px solid rgba(240, 240, 240, 0.5);
"""

st.markdown(
    f"""
    <style>
        .main {{
            background: linear-gradient(145deg, #F0F5F9 0%, #E3EAF0 50%, #D8E0E8 100%);
        }}
        .card {{ {CARD_STYLE} }}
        .small-muted {{ color:#718b89; font-size:12px; }}
        .modebar {{ visibility:hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# LOAD DATA
# =============================================================================
DATA_DIR = "data"

def read_csv_clean(path):
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None

products = read_csv_clean(os.path.join(DATA_DIR, "products.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))

# fallback demo data
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
# METRICS
# =============================================================================
products["StockValue"] = products["Quantity"] * products["UnitPrice"]
low_stock_items_count = (products["Quantity"] < products["MinStock"]).sum()
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
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum()

# =============================================================================
# GAUGE FUNCTION
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b><br><span style='font-size:13px; color:{MUTED_TEXT};'>{subtitle}</span>"},
        gauge={
            "axis": {"range": [0, max(max_value, 1)], "tickwidth": 0},
            "bar": {"color": color, "thickness": 0.5},
            "steps": [{"range": [0, max(max_value, 1)], "color": "rgba(47,94,89,0.06)"}],
        },
        number={"font": {"size": 30, "color": DARK_TEXT}},
    ))
    fig.update_layout(margin=dict(l=6, r=6, t=40, b=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# =============================================================================
# LAYOUT
# =============================================================================
top_cols = st.columns([0.8, 2.0, 1.5], gap="large")

with top_cols[1]:
    gcols = st.columns(3)
    max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)
    gcols[0].plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#E74C3C", max_kpi), use_container_width=True)
    gcols[1].plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#F39C12", max_kpi), use_container_width=True)
    gcols[2].plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR, max_kpi), use_container_width=True)

# =============================================================================
# CHAT + TREND SECTION
# =============================================================================
bot_cols = st.columns([1.1, 2.3], gap="large")

if "chat_log" not in st.session_state:
    st.session_state.chat_log = [
        ("user", "Which supplier has the highest stock value?"),
        ("bot", f"ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}."),
    ]

def render_chat_messages():
    html = []
    for role, text in st.session_state.chat_log:
        if role == "user":
            html.append(f"<p style='text-align:right; font-size:13px; margin:4px 0;'>🧍‍♂️ <b>You:</b> {text}</p>")
        else:
            html.append(f"<p style='font-size:13px; background:#E8F4F3; color:{DARK_TEXT}; "
                        f"padding:6px 10px; border-radius:8px; display:inline-block; margin:4px 0;'>🤖 {text}</p>")
    return "\n".join(html)

def answer_query_llm(query):
    try:
        if not (openai and st.secrets.get("OPENAI_API_KEY")):
            return "AI chat disabled or missing API key."
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        context = f"Products: {products.to_dict()}"
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Be concise and factual."},
                {"role": "user", "content": f"{context}\n\nUser: {query}"},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- CHAT BOX
with bot_cols[0]:
    st.markdown(
        f"""
        <div class="card" style="padding:18px; height:430px; display:flex; flex-direction:column;">
            <div style="color:{DARK_TEXT}; font-weight:800; font-size:18px;">Chat Assistant</div>
            <div class="small-muted" style="margin-bottom:8px;">Ask questions about inventory, suppliers, or sales.</div>
            <hr style="margin:8px 0 10px 0;"/>
            <div id="chat-box" style="
                flex-grow:1;
                overflow-y:auto;
                background:#f9fbfc;
                border:1px solid #eef1f5;
                padding:10px 12px;
                border-radius:10px;
                margin-bottom:10px;">
        """,
        unsafe_allow_html=True,
    )

    # render chat log inside box
    st.markdown(render_chat_messages(), unsafe_allow_html=True)

    # close div after messages
    st.markdown("</div>", unsafe_allow_html=True)

    # input form inside same card
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            user_q = st.text_input("", placeholder="Type your question...", label_visibility="collapsed")
        with cols[1]:
            send = st.form_submit_button("Send")

    if send and user_q.strip():
        q = user_q.strip()
        st.session_state.chat_log.append(("user", q))
        with st.spinner("Analyzing data..."):
            ans = answer_query_llm(q)
        st.session_state.chat_log.append(("bot", ans))
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- TREND PERFORMANCE
with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='color:{DARK_TEXT}; font-weight:800; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    name_col = "Name"
    qty_col = "Qty"
    df = sales_ext.groupby(["Month", name_col], as_index=False)[qty_col].sum()
    months_sorted = sorted(df["Month"].unique(), key=lambda x: pd.to_datetime(x))
    fig = go.Figure()
    colors = ["#0077B6", "#FF9500", "#1EA97C", "#E74C3C"]
    for i, label in enumerate(df[name_col].unique()):
        sub = df[df[name_col] == label].set_index("Month").reindex(months_sorted).fillna(0)
        fig.add_trace(go.Scatter(x=months_sorted, y=sub[qty_col], mode="lines+markers", name=label,
                                 line=dict(color=colors[i % len(colors)], width=3)))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=6, r=6, t=8, b=6))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
