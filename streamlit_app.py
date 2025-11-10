import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu

# ---------------------- PAGE SETUP ----------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

SKY = """
/* ----------- global background (sky gradient) ----------- */
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 50% -80px, #ffffff 0, #e9f3fb 35%, #cfe3f4 100%);
}
/* remove top padding */
.block-container {padding-top: 1.2rem; padding-bottom: 3rem;}
/* clean tables */
thead tr th {font-weight: 600 !important;}
/* paper card wrapper (background box behind sections) */
.paper {
  background: #fff;
  border-radius: 14px;
  padding: 18px 18px 8px 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
  border: 1px solid rgba(20,60,120,.06);
}
/* metric tiles */
.tile {
  background: #fff;
  border-radius: 14px;
  padding: 18px 16px;
  box-shadow: 0 6px 16px rgba(0,0,0,.05);
  border: 1px solid rgba(20,60,120,.06);
}
.tile h4 {margin: 0 0 6px 0; font-weight: 700;}
.tile span {color:#6b7a90; font-size:.9rem}

/* section titles */
h2, h3 {margin-top: .2rem; margin-bottom: .6rem;}

/* sidebar spacing */
.css-1d391kg, [data-testid="stSidebar"] .block-container {padding-top: .8rem !important}

/* chat */
.chat-box{
  background:#f6fbff;
  border:1px solid #d9e7f5; border-radius:12px;
  padding:14px; height:420px; overflow-y:auto;
}
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

# Supplier summary for the Suppliers page
supplier_summary = (products.groupby("Supplier")
                    .agg(Products=("Product_ID","nunique"),
                         Units=("Quantity","sum"))
                    .reset_index()
                    .rename(columns={"Supplier":"supplier"}))

# Chat memory
if "chat" not in st.session_state:
    st.session_state.chat = []  # list of dicts: {"role": "user"/"bot", "text": "..."}

# ---------------------- UTILITIES ----------------------
def metric_tile(label, value, sub):
    st.markdown('<div class="tile">', unsafe_allow_html=True)
    st.markdown(f"<h4>{label}</h4><div style='font-size:2rem;font-weight:800;margin:.2rem 0'>{value}</div><span>{sub}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def sales_bar(df):
    # make a stacked-by-supplier bar over categories (matches your reference look)
    tmp = df.groupby(["Category","Supplier"], as_index=False)["Quantity"].sum()
    fig = px.bar(tmp, x="Quantity", y="Category", color="Supplier", orientation="h",
                 color_discrete_sequence=["#34c38f","#f39c12","#4b77be"])
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), legend_title_text="supplier",
                      xaxis_title="Sales / Units", yaxis_title=None, bargap=.25, plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig

def trend_line():
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    a = [14,18,22,26,30,35]; b = [10,14,18,23,27,31]
    df = pd.DataFrame({"Month":months, "Product A":a, "Product B":b})
    fig = px.line(df, x="Month", y=["Product A","Product B"])
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10),
                      legend_title_text="Product", plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ---- simple, fast “intelligent” chat over the dataframe (no API) ----
def answer(q: str) -> str:
    ql = q.lower().strip()

    # 1) low stock list
    if "low stock" in ql or "need restock" in ql or "restocking" in ql:
        lows = products.loc[products["Low"], ["Name","Quantity","MinStock"]]
        if lows.empty:
            return "All items are at or above minimum stock."
        rows = [f"- {r.Name}: {int(r.Quantity)}/{int(r.MinStock)} (below min)" for r in lows.itertuples()]
        return "Items that need restocking:\n" + "\n".join(rows)

    # 2) quantity of a product by name
    m = re.search(r"quantity of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"I couldn't find any product matching '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} — Quantity: {int(r['Quantity'])}, MinStock: {int(r['MinStock'])}."

    # 3) supplier of a product
    m = re.search(r"supplier of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"No supplier found for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} is supplied by {r['Supplier']}."

    # 4) price of a product
    m = re.search(r"price of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"No price info found for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} costs ${int(r['UnitPrice'])}."

    # 5) find by SKU
    m = re.search(r"(?:sku|code)\s*([a-z0-9\-]+)", ql)
    if m:
        sku = m.group(1).upper()
        match = products[products["SKU"].str.upper() == sku]
        if match.empty:
            return f"I can't find any product with SKU '{sku}'."
        r = match.iloc[0]
        return f"{r['Name']} — Qty {int(r['Quantity'])}, Min {int(r['MinStock'])}, Price ${int(r['UnitPrice'])}, Supplier {r['Supplier']}."

    # 6) generic help
    return ("I didn't understand. Try:\n"
            " • 'low stock'\n"
            " • 'quantity of iPhone'\n"
            " • 'supplier of AirPods'\n"
            " • 'price of MacBook'\n"
            " • 'sku GS24'")

def chat_ui():
    st.subheader("Chat Assistant")
    with st.container():
        col = st.columns([1])[0]
        with col:
            st.markdown('<div class="paper">', unsafe_allow_html=True)
            user_q = st.text_input("Ask about stock, SKU, supplier, price…", key="chat_q")
            if user_q:
                st.session_state.chat.append({"role":"user","text":user_q})
                st.session_state.chat.append({"role":"bot","text":answer(user_q)})
                st.experimental_rerun()

            st.markdown('<div class="chat-box">', unsafe_allow_html=True)
            if not st.session_state.chat:
                st.info("Ask: 'low stock', 'quantity of iPhone', 'supplier of AirPods', 'price of MacBook', 'sku GS24'.")
            for m in st.session_state.chat[-30:]:
                if m["role"] == "user":
                    st.markdown(f"<div class='msg-u'>You:</div><div style='margin:-6px 0 10px 0'>{m['text']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='msg-b'>Bot:</div><div style='white-space:pre-wrap;margin:-6px 0 14px 0'>{m['text']}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------- SIDEBAR NAV ----------------------
with st.sidebar:
    choice = option_menu(
        None,
        ["Dashboard", "Inventory", "Suppliers", "Orders", "Chat Assistant", "Settings"],
        icons=["speedometer2", "box-seam", "people", "receipt", "chat-dots", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "10px 0"},
            "icon": {"color": "#5b6a88", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "margin":"4px 0", "--hover-color": "#e6f2ff"},
            "nav-link-selected": {"background-color": "#dfefff", "font-weight":"600"},
        }
    )

# ---------------------- PAGES ----------------------
if choice == "Dashboard":
    st.title("Inventory Management Dashboard")

    # --- Summary tiles row inside a wide paper ---
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    tiles = st.columns([1.3, 1.3, 1.3, 1.3, 3.7])  # last column just to stretch the paper background
    with tiles[0]: metric_tile("Stock Items", products["Product_ID"].nunique(), "distinct products")
    with tiles[1]: metric_tile("Low Stock", int(products["Low"].sum()), "below minimum")
    with tiles[2]: metric_tile("Reorder Needed", int(products["Low"].sum()), "order these")
    with tiles[3]: metric_tile("In Stock", int((~products["Low"]).sum()), "OK level")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Row: Supplier & Sales (left paper) + Chat (right paper) ---
    left, right = st.columns([7,5])
    with left:
        st.markdown('<div class="paper">', unsafe_allow_html=True)
        st.subheader("Supplier & Sales Data")
        st.plotly_chart(sales_bar(products), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        chat_ui()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Trend section in its own paper background ---
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.subheader("Trend Performance — Top-Selling Products")
    st.plotly_chart(trend_line(), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Inventory":
    st.title("Inventory")
    st.markdown('<div class="paper">', unsafe_allow_html=True)

    df = products.copy()
    df_display = df[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier","Low"]]
    st.dataframe(df_display, use_container_width=True, hide_index=True, height=420)

    st.info("Tip: items with **Low = True** need reordering.", icon="💡")
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Suppliers":
    st.title("Suppliers")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.dataframe(supplier_summary, use_container_width=True, hide_index=True, height=360)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Orders":
    st.title("Orders")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    orders = pd.DataFrame([
        {"Order_ID":"S-1001","Product":"Logitech Mouse","Units":2,"Price":29,"Date":"2025-01-10"},
        {"Order_ID":"S-1002","Product":"iPhone 15","Units":1,"Price":999,"Date":"2025-02-01"},
    ])
    st.dataframe(orders, use_container_width=True, hide_index=True, height=320)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Chat Assistant":
    st.title("Chat Assistant")
    chat_ui()

elif choice == "Settings":
    st.title("Settings")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.write("• (Add your preferences here — theme, thresholds, export, etc.)")
    st.markdown('</div>', unsafe_allow_html=True)
