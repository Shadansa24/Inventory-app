# streamlit_app.py
# Inventory Dashboard — Streamlit (clean layout + unified chat container + functional navigation)

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat (disabled if no key)
try:
    import openai
except Exception:
    openai = None


# =============================================================================
# PAGE CONFIGURATION & STYLES
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

PRIMARY_COLOR = "#0077B6"
ACCENT_COLOR = "#1EA97C"
DARK_TEXT = "#1B4E4D"
MUTED_TEXT = "#4A7D7B"

PRIMARY_BG_GRADIENT = """
linear-gradient(145deg,
#F0F5F9 0%, 
#E3EAF0 50%, 
#D8E0E8 100%)
"""

CARD_STYLE = """
background: rgba(255,255,255,0.98);
backdrop-filter: blur(8px);
border-radius: 20px; 
padding: 22px; 
box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08); 
border: 1px solid rgba(240, 240, 240, 0.5);
"""

LABEL_STYLE = f"color:{MUTED_TEXT}; font-weight:600; font-size:13px;"
TITLE_STYLE = f"color:{DARK_TEXT}; font-weight:800; font-size:24px;"

st.markdown(f"""
    <style>
        .main {{ background: {PRIMARY_BG_GRADIENT}; }}
        .small-muted {{ color:#718b89; font-size:12px; }}
        .card {{ {CARD_STYLE} }}
        .chip {{
            display:flex;
            align-items:center;
            padding:10px 15px;
            font-size:14px;
            border-radius:12px;
            background:#E8F4F3;
            color:{MUTED_TEXT};
            margin-bottom:6px;
            font-weight:600;
            cursor:pointer;
            transition: background 0.2s, color 0.2s;
        }}
        .chip:hover {{ background:#D5EBEA; color:#005691; }}
        .chip.active {{
            background:#D5EBEA; 
            color:{PRIMARY_COLOR};
            border-left:4px solid {PRIMARY_COLOR};
            padding-left:11px;
        }}
        hr {{ margin:12px 0 10px 0; border-color:#e7eeed; }}
        .modebar {{ visibility:hidden; }}
    </style>
""", unsafe_allow_html=True)

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

# Fallback demo data
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
# DERIVED METRICS
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
# HELPERS
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b><br><span style='font-size:14px; color:{MUTED_TEXT};'>{subtitle}</span>"},
        gauge={
            "axis": {"range": [0, max(max_value, 1)], "tickwidth": 0},
            "bar": {"color": color, "thickness": 0.5},
            "steps": [{"range": [0, max(max_value, 1)], "color": "rgba(47,94,89,0.06)"}],
        },
        number={"font": {"size": 32, "color": DARK_TEXT}},
    ))
    fig.update_layout(margin=dict(l=6, r=6, t=30, b=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# =============================================================================
# SESSION STATE
# =============================================================================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "chat_log" not in st.session_state:
    st.session_state.chat_log = [
        ("user", "Which supplier has the highest stock value?"),
        ("bot", f"ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}."),
    ]

# =============================================================================
# NAVIGATION BAR
# =============================================================================
def navigation_bar():
    nav_items = [
        ("📊 Dashboard", "Dashboard"),
        ("📦 Inventory", "Inventory"),
        ("🚚 Suppliers", "Suppliers"),
        ("🛒 Orders", "Orders"),
        ("⚙️ Settings", "Settings"),
        ("💬 Chat Assistant", "Chat Assistant"),
    ]

    for icon, page in nav_items:
        active = "active" if st.session_state.page == page else ""
        if st.button(f"{icon} {page}", key=page, use_container_width=True):
            st.session_state.page = page
            st.rerun()
        st.markdown(f"<div class='chip {active}'>{icon} {page}</div>" if active else "", unsafe_allow_html=True)

# =============================================================================
# CHAT ASSISTANT
# =============================================================================
def render_chat():
    chat_html = []
    for role, text in st.session_state.chat_log:
        if role == "user":
            chat_html.append(f"<p style='text-align:right; font-size:13px;'>🧍‍♂️ <b>You:</b> {text}</p>")
        else:
            chat_html.append(f"<p style='font-size:13px; background:#E8F4F3; color:{DARK_TEXT}; "
                             f"padding:6px 10px; border-radius:8px;'>🤖 {text}</p>")

    st.markdown(f"""
        <div class="card" style="padding:18px; height:480px;">
            <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
            <div class="small-muted">Ask questions about inventory, suppliers, or sales.</div>
            <hr/>
            <div style="overflow-y:auto; height:320px;">{''.join(chat_html)}</div>
        </div>
    """, unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([0.8, 0.2])
        user_q = cols[0].text_input("", placeholder="Type your question...", label_visibility="collapsed")
        send = cols[1].form_submit_button("Send")

        if send and user_q.strip():
            st.session_state.chat_log.append(("user", user_q.strip()))
            st.session_state.chat_log.append(("bot", f"Simulated answer about '{user_q}'"))
            st.rerun()

# =============================================================================
# PAGE RENDERING
# =============================================================================
top_cols = st.columns([0.8, 3.0], gap="large")

# --- Left Navigation
with top_cols[0]:
    st.markdown(f"<div class='card' style='padding:20px;'><div style='{TITLE_STYLE}; font-size:18px;'>Navigation</div>", unsafe_allow_html=True)
    navigation_bar()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Right Main Section
with top_cols[1]:
    page = st.session_state.page

    if page == "Dashboard":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>📊 Dashboard Overview</div>", unsafe_allow_html=True)
        gcols = st.columns(3)
        gcols[0].plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#E74C3C", 50), use_container_width=True)
        gcols[1].plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#F39C12", 50), use_container_width=True)
        gcols[2].plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR, 50), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        render_chat()

    elif page == "Inventory":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>📦 Inventory</div>", unsafe_allow_html=True)
        st.dataframe(products, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif page == "Suppliers":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>🚚 Suppliers</div>", unsafe_allow_html=True)
        st.dataframe(suppliers, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif page == "Orders":
        orders_joined = sales.merge(products[["Product_ID", "Name", "UnitPrice"]], on="Product_ID", how="left")
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>🛒 Orders</div>", unsafe_allow_html=True)
        st.dataframe(orders_joined, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif page == "Settings":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>⚙️ Settings</div>", unsafe_allow_html=True)
        st.text("Placeholder for settings, API keys, or preferences.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif page == "Chat Assistant":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}'>💬 Chat Assistant</div>", unsafe_allow_html=True)
        render_chat()
