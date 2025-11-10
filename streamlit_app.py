import re
import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO
from streamlit_option_menu import option_menu

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# ---------------------- STYLE ----------------------
SKY = """
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 50% -80px, #ffffff 0, #e9f3fb 35%, #cfe3f4 100%);
}
.block-container {padding-top: 1rem; padding-bottom: 3rem;}
thead tr th {font-weight: 600 !important;}
h2, h3 {margin-top: .2rem; margin-bottom: .6rem;}
.msg-u{font-weight:700; color:#0a3d62}
.msg-b{color:#0d5fa6}
"""
st.markdown(f"<style>{SKY}</style>", unsafe_allow_html=True)

# ---------------------- DATA ----------------------
products = pd.DataFrame([
    {"Product_ID": 101, "SKU": "IPH-15", "Name": "iPhone 15",      "Category": "Mobile",   "Quantity": 12, "MinStock": 15, "UnitPrice": 999, "Supplier": "ACME"},
    {"Product_ID": 102, "SKU": "GS24",   "Name": "Galaxy S24",     "Category": "Mobile",   "Quantity": 30, "MinStock": 8,  "UnitPrice": 899, "Supplier": "GX"},
    {"Product_ID": 103, "SKU": "MBA-M3", "Name": "MacBook Air M3", "Category": "Laptop",   "Quantity": 5,  "MinStock": 8,  "UnitPrice": 1299,"Supplier": "ACME"},
    {"Product_ID": 104, "SKU": "LG-MSE", "Name": "Logitech Mouse","Category": "Accessory","Quantity": 3,  "MinStock": 5,  "UnitPrice": 29,  "Supplier": "ACC"},
    {"Product_ID": 105, "SKU": "AP-PR2", "Name": "AirPods Pro",    "Category": "Accessory","Quantity": 20, "MinStock": 5,  "UnitPrice": 249, "Supplier": "ACME"},
])
products["Low"] = products["Quantity"] < products["MinStock"]

supplier_summary = (
    products.groupby("Supplier")
    .agg(Products=("Product_ID", "nunique"), Units=("Quantity", "sum"))
    .reset_index()
    .rename(columns={"Supplier": "supplier"})
)

# ---------------------- SETTINGS MANAGEMENT ----------------------
SETTINGS_FILE = "user_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"theme": "Sky Blue", "reorder_threshold": 25, "persist_chat": True}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def export_to_excel():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        products.to_excel(writer, index=False, sheet_name="Inventory")
        supplier_summary.to_excel(writer, index=False, sheet_name="Suppliers")
    buffer.seek(0)
    return buffer

settings = load_settings()

# ---------------------- CHAT MEMORY ----------------------
CHAT_FILE = "chat_history.json"

def load_chat():
    if settings.get("persist_chat") and os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return []

def save_chat():
    if settings.get("persist_chat"):
        with open(CHAT_FILE, "w") as f:
            json.dump(st.session_state.chat, f, indent=4)

if "chat" not in st.session_state:
    st.session_state.chat = load_chat()

# ---------------------- UTILITIES ----------------------
def sales_bar(df):
    tmp = df.groupby(["Category","Supplier"], as_index=False)["Quantity"].sum()
    fig = px.bar(tmp, x="Quantity", y="Category", color="Supplier", orientation="h",
                 color_discrete_sequence=["#34c38f","#f39c12","#4b77be"])
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10),
                      legend_title_text="Supplier", xaxis_title="Units", yaxis_title=None,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

def trend_line():
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    a = [14,18,22,26,30,35]; b = [10,14,18,23,27,31]
    df = pd.DataFrame({"Month":months,"Product A":a,"Product B":b})
    fig = px.line(df, x="Month", y=["Product A","Product B"])
    fig.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10),
                      legend_title_text="Product", plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ---------------------- CHAT LOGIC ----------------------
def answer(q: str) -> str:
    ql = q.lower().strip()

    if any(k in ql for k in ["low stock", "need restock", "restocking"]):
        lows = products.loc[products["Low"], ["Name","Quantity","MinStock"]]
        if lows.empty:
            return "All items are at or above minimum stock."
        rows = [f"- {r.Name}: {int(r.Quantity)}/{int(r.MinStock)} (below min)" for r in lows.itertuples()]
        return "Items that need restocking:\n" + "\n".join(rows)

    m = re.search(r"quantity of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"I couldn't find '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} — Quantity: {int(r['Quantity'])}, MinStock: {int(r['MinStock'])}."

    m = re.search(r"supplier of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty: return f"No supplier found for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} is supplied by {r['Supplier']}."

    m = re.search(r"price of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty: return f"No price info for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} costs ${int(r['UnitPrice'])}."

    m = re.search(r"(?:sku|code)\s*([a-z0-9\-]+)", ql)
    if m:
        sku = m.group(1).upper()
        match = products[products["SKU"].str.upper() == sku]
        if match.empty: return f"No SKU '{sku}' found."
        r = match.iloc[0]
        return f"{r['Name']} — Qty {r['Quantity']}, Min {r['MinStock']}, Price ${r['UnitPrice']}, Supplier {r['Supplier']}."

    return ("I didn't understand. Try:\n"
            " • 'low stock'\n"
            " • 'quantity of iPhone'\n"
            " • 'supplier of AirPods'\n"
            " • 'price of MacBook'\n"
            " • 'sku GS24'")

# ---------------------- CHAT UI ----------------------
def chat_ui():
    st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)

    # Chat box container
    chat_container = st.container()
    with chat_container:
        st.markdown(
            '<div class="chat-box" style="height:400px;overflow-y:auto;background:#ffffff;border:1px solid #dce6f7;border-radius:12px;padding:12px;">',
            unsafe_allow_html=True,
        )

        if not st.session_state.chat:
            st.info("Try: 'low stock', 'quantity of iPhone', 'supplier of AirPods', or 'price of MacBook'.")
        else:
            for m in st.session_state.chat[-25:]:
                if m["role"] == "user":
                    st.markdown(f"<div class='msg-u'>You:</div><div style='margin:-6px 0 10px 0'>{m['text']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='msg-b'>Bot:</div><div style='white-space:pre-wrap;margin:-6px 0 14px 0'>{m['text']}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Fixed input at bottom
    with st.form("chat_form", clear_on_submit=True):
        user_q = st.text_input("Ask about stock, SKU, supplier, or price…", key="chat_input_fixed")
        submitted = st.form_submit_button("Send")
        if submitted and user_q.strip():
            st.session_state.chat.append({"role": "user", "text": user_q})
            reply = answer(user_q)
            st.session_state.chat.append({"role": "bot", "text": reply})
            save_chat()

# ---------------------- SIDEBAR NAV ----------------------
with st.sidebar:
    choice = option_menu(
        None,
        ["Dashboard", "Inventory", "Suppliers", "Orders", "Chat Assistant", "Settings"],
        icons=["speedometer2","box-seam","people","receipt","chat-dots","gear"],
        default_index=0,
        styles={
            "container": {"padding": "10px 0"},
            "icon": {"color": "#5b6a88", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "margin":"4px 0", "--hover-color": "#e6f2ff"},
            "nav-link-selected": {"background-color": "#dfefff", "font-weight":"600"},
        }
    )

# ---------------------- DASHBOARD ----------------------
if choice == "Dashboard":
    st.title("Inventory Management Dashboard")

    # Top KPIs
    st.subheader("Stock Overview")
    kpi = st.columns(3)
    kpi[0].metric("Low Stock", int(products["Low"].sum()), "47 Items")
    kpi[1].metric("Reorder", 120, "120 Items")
    kpi[2].metric("In Stock", int(products["Quantity"].sum()), "890 Items")

    st.markdown("<br>", unsafe_allow_html=True)

    # Supplier data + reports
    col1, col2 = st.columns([7, 5])
    with col1:
        st.subheader("Supplier & Sales Data")
        st.plotly_chart(sales_bar(products), use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.subheader("Detailed Reports")
        st.markdown("""
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;text-align:center;margin-top:10px">
            <div style="border:1px solid rgba(0,0,0,.06);border-radius:12px;padding:16px;background:#ffffff">
                📦<br><b>Inventory</b><br><span style="font-size:12px;color:#687c9c">History</span>
            </div>
            <div style="border:1px solid rgba(0,0,0,.06);border-radius:12px;padding:16px;background:#ffffff">
                📈<br><b>Movement</b><br><span style="font-size:12px;color:#687c9c">Reports</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chat + Trend row
    c1, c2 = st.columns([6, 6])
    with c1:
        chat_ui()
    with c2:
        st.subheader("Trend Performance — Top-Selling Products")
        st.plotly_chart(trend_line(), use_container_width=True)

# ---------------------- INVENTORY ----------------------
elif choice == "Inventory":
    st.title("Inventory")
    st.dataframe(products, use_container_width=True, hide_index=True, height=420)
    st.info("💡 Tip: items with **Low = True** need reordering.")

# ---------------------- SUPPLIERS ----------------------
elif choice == "Suppliers":
    st.title("Suppliers")
    st.dataframe(supplier_summary, use_container_width=True, hide_index=True, height=360)

# ---------------------- ORDERS ----------------------
elif choice == "Orders":
    st.title("Orders")
    orders = pd.DataFrame([
        {"Order_ID":"S-1001","Product":"Logitech Mouse","Units":2,"Price":29,"Date":"2025-01-10"},
        {"Order_ID":"S-1002","Product":"iPhone 15","Units":1,"Price":999,"Date":"2025-02-01"},
    ])
    st.dataframe(orders, use_container_width=True, hide_index=True, height=320)

# ---------------------- CHAT PAGE ----------------------
elif choice == "Chat Assistant":
    st.title("Chat Assistant")
    chat_ui()

# ---------------------- SETTINGS ----------------------
elif choice == "Settings":
    st.title("Settings")

    st.subheader("Preferences")
    theme = st.selectbox("Theme", ["Sky Blue", "Dark Mode (coming soon)"], index=0)
    threshold = st.slider("Reorder Alert Threshold (%)", 0, 100, settings.get("reorder_threshold", 25))
    persist_chat = st.checkbox("Persist Chat History", value=settings.get("persist_chat", True))

    if st.button("💾 Save Settings"):
        save_settings({"theme": theme, "reorder_threshold": threshold, "persist_chat": persist_chat})
        st.success("Settings saved successfully!")

    st.divider()
    st.subheader("Data Export")
    if st.button("📤 Export to Excel"):
        file = export_to_excel()
        st.download_button("Download Excel File", data=file, file_name="inventory_data.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()
    st.subheader("Chat Management")
    if st.button("🧹 Clear Chat History"):
        st.session_state.chat = []
        if os.path.exists(CHAT_FILE): os.remove(CHAT_FILE)
        st.success("Chat history cleared.")

    st.caption("Version 1.3.1 — Streamlit Inventory Manager")
