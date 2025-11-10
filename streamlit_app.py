# streamlit_app.py
# Inventory Dashboard — Streamlit (clean layout + editable tables + working chat + persistence)

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat
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
BG_GRADIENT = """
linear-gradient(145deg, #F0F5F9 0%, #E3EAF0 50%, #D8E0E8 100%)
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
.main {{ background: {BG_GRADIENT}; }}
.chip {{
    display:flex; align-items:center;
    padding:10px 15px; font-size:14px;
    border-radius:12px; background:#E8F4F3;
    color:{MUTED_TEXT}; margin-bottom:6px;
    font-weight:600; cursor:pointer;
}}
.chip:hover {{ background:#D5EBEA; color:#005691; }}
.chip.active {{
    background:#D5EBEA; color:{PRIMARY_COLOR};
    border-left:4px solid {PRIMARY_COLOR};
    padding-left:11px;
}}
.nav-link {{ text-decoration:none; color:inherit; }}
.modebar {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADERS
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
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))

# Demo fallback data
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
# SESSION STATE INIT
# =============================================================================
for key, df in {
    "products_edit": products,
    "suppliers_edit": suppliers,
    "sales_edit": sales,
}.items():
    if key not in st.session_state:
        st.session_state[key] = df.copy()

if "chat_log" not in st.session_state:
    st.session_state.chat_log = [
        ("user", "Which supplier has the highest stock value?"),
        ("bot", "ACME Distribution has the highest stock value at $12,345."),
    ]

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
# CHAT UTILITIES
# =============================================================================
def render_chat_messages():
    html = []
    for role, text in st.session_state.chat_log:
        if role == "user":
            html.append(f"<p style='text-align:right; font-size:13px;'>🧍‍♂️ <b>You:</b> {text}</p>")
        else:
            html.append(f"<p style='font-size:13px; background:#E8F4F3; color:{DARK_TEXT}; "
                        f"padding:6px 10px; border-radius:8px; margin:4px 0;'>🤖 {text}</p>")
    return "\n".join(html)

def handle_chat_input(input_text):
    OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
    if not (openai and OPENAI_KEY):
        return "AI chat is disabled (no API key)."
    openai.api_key = OPENAI_KEY
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an inventory data assistant."},
                {"role": "user", "content": input_text},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# =============================================================================
# ROUTING
# =============================================================================
DEFAULT_PAGE = "Dashboard"
qp = st.query_params
current_page = qp.get("page", DEFAULT_PAGE)

def _chip(label, icon, active):
    act = "active" if active else ""
    href = f"?page={label.replace(' ', '%20')}"
    return f"<a class='nav-link' href='{href}'><div class='chip {act}'>{icon} {label}</div></a>"

# =============================================================================
# LAYOUT — NAV + CONTENT
# =============================================================================
cols = st.columns([0.8, 3.0], gap="large")

# Navigation bar
with cols[0]:
    st.markdown(f"""
    <div class="card">
        <div style="{TITLE_STYLE}; font-size:18px;">Navigation</div>
        <div style="margin-top:10px;">
            {_chip("Dashboard", "📊", current_page=="Dashboard")}
            {_chip("Inventory", "📦", current_page=="Inventory")}
            {_chip("Suppliers", "🚚", current_page=="Suppliers")}
            {_chip("Orders", "🛒", current_page=="Orders")}
            {_chip("Chat Assistant", "💬", current_page=="Chat Assistant")}
            {_chip("Settings", "⚙️", current_page=="Settings")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# CONTENT AREA
# =============================================================================
with cols[1]:
    # Dashboard
    if current_page == "Dashboard":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px;'>📦 Stock Overview</div>", unsafe_allow_html=True)
        gcols = st.columns(3)
        max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)
        def gauge(t, v, sub, c): 
            fig = go.Figure(go.Indicator(mode="gauge+number", value=v, title={"text": f"<b>{t}</b><br><span style='font-size:13px'>{sub}</span>"},
                                         gauge={"axis": {"range": [0, max_kpi]}, "bar": {"color": c}}))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0))
            return fig
        gcols[0].plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#E74C3C"))
        gcols[1].plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#F39C12"))
        gcols[2].plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR))
        st.markdown("</div>", unsafe_allow_html=True)

        st.plotly_chart(px.bar(supplier_totals, x="StockValue", y="Supplier_Name", orientation="h", color_discrete_sequence=[PRIMARY_COLOR]), use_container_width=True)
        st.plotly_chart(px.bar(sales_by_cat, x="Category", y="Qty", color_discrete_sequence=[ACCENT_COLOR]), use_container_width=True)

        # Dashboard chat
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>💬 Chat Assistant</div>", unsafe_allow_html=True)
        st.markdown(render_chat_messages(), unsafe_allow_html=True)
        with st.form("chat_dashboard", clear_on_submit=True):
            c1, c2 = st.columns([0.8, 0.2])
            msg = c1.text_input("", placeholder="Ask something...", label_visibility="collapsed")
            send = c2.form_submit_button("Send")
        if send and msg.strip():
            st.session_state.chat_log.append(("user", msg))
            ans = handle_chat_input(msg)
            st.session_state.chat_log.append(("bot", ans))
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Editable tables
    elif current_page in ["Inventory", "Suppliers", "Orders"]:
        title_map = {
            "Inventory": ("📦 Inventory", "products_edit"),
            "Suppliers": ("🚚 Suppliers", "suppliers_edit"),
            "Orders": ("🛒 Orders", "sales_edit"),
        }
        label, key = title_map[current_page]
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>{label} (Editable)</div>", unsafe_allow_html=True)
        edited = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", key=f"{key}_editor")
        st.session_state[key] = edited.copy()
        st.markdown("</div>", unsafe_allow_html=True)

    # Chat page
    elif current_page == "Chat Assistant":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>💬 Chat Assistant</div>", unsafe_allow_html=True)
        st.markdown(render_chat_messages(), unsafe_allow_html=True)
        with st.form("chat_page", clear_on_submit=True):
            c1, c2 = st.columns([0.8, 0.2])
            msg = c1.text_input("", placeholder="Ask something...", label_visibility="collapsed")
            send = c2.form_submit_button("Send")
        if send and msg.strip():
            st.session_state.chat_log.append(("user", msg))
            ans = handle_chat_input(msg)
            st.session_state.chat_log.append(("bot", ans))
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Settings page
    elif current_page == "Settings":
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>⚙️ Settings</div>", unsafe_allow_html=True)
        st.write("Download your latest edited tables:")
        st.download_button("Download Inventory (CSV)", st.session_state.products_edit.to_csv(index=False).encode(), "inventory_edited.csv", "text/csv")
        st.download_button("Download Suppliers (CSV)", st.session_state.suppliers_edit.to_csv(index=False).encode(), "suppliers_edited.csv", "text/csv")
        st.download_button("Download Orders (CSV)", st.session_state.sales_edit.to_csv(index=False).encode(), "orders_edited.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
