import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu

# ---------------------- PAGE SETUP ----------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# ---------------------- THEME / CSS ----------------------
def inject_css(accent="#0d5fa6"):
    SKY = f"""
    /* sky gradient background */
    [data-testid="stAppViewContainer"] {{
      background: radial-gradient(1200px 600px at 50% -80px,#ffffff 0,#e9f3fb 35%,#cfe3f4 100%);
    }}
    .block-container {{padding-top: 1.2rem; padding-bottom: 3rem;}}
    thead tr th {{font-weight: 600 !important;}}
    /* card container */
    .paper {{
      background: #fff;
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(0,0,0,.06);
      border: 1px solid rgba(20,60,120,.06);
    }}
    /* metrics */
    .tile {{
      background: #fff;
      border-radius: 14px;
      padding: 18px 16px;
      box-shadow: 0 6px 16px rgba(0,0,0,.05);
      border: 1px solid rgba(20,60,120,.06);
    }}
    .tile h4 {{margin: 0 0 6px 0; font-weight: 700;}}
    .tile .big {{font-size:2rem;font-weight:800;margin:.2rem 0}}
    .tile span {{color:#6b7a90; font-size:.9rem}}

    h2, h3 {{margin-top: .2rem; margin-bottom: .6rem;}}

    /* chat */
    .chat-box{{
      background:#f6fbff;
      border:1px solid #d9e7f5; border-radius:12px;
      padding:14px; height:420px; overflow-y:auto;
    }}
    .msg-u{{font-weight:700; color:#0a3d62}}
    .msg-b{{color:{accent} }}

    /* tweak sidebar */
    [data-testid="stSidebar"] .block-container {{padding-top:.8rem}}
    """
    st.markdown(f"<style>{SKY}</style>", unsafe_allow_html=True)

# ----------- SESSION DEFAULTS (settings) -----------
if "accent" not in st.session_state: st.session_state.accent = "#0d5fa6"
if "currency" not in st.session_state: st.session_state.currency = "$"
if "threshold_bump" not in st.session_state: st.session_state.threshold_bump = 1.0

inject_css(st.session_state.accent)

# ---------------------- DATA ----------------------
base_products = pd.DataFrame([
    {"Product_ID": 101, "SKU": "IPH-15", "Name": "iPhone 15",      "Category": "Mobile",   "Quantity": 12, "MinStock": 15, "UnitPrice": 999, "Supplier": "ACME"},
    {"Product_ID": 102, "SKU": "GS24",   "Name": "Galaxy S24",     "Category": "Mobile",   "Quantity": 30, "MinStock": 8,  "UnitPrice": 899, "Supplier": "GX"},
    {"Product_ID": 103, "SKU": "MBA-M3", "Name": "MacBook Air M3", "Category": "Laptop",   "Quantity": 5,  "MinStock": 8,  "UnitPrice": 1299,"Supplier": "ACME"},
    {"Product_ID": 104, "SKU": "LG-MSE", "Name": "Logitech Mouse","Category": "Accessory","Quantity": 3,  "MinStock": 5,  "UnitPrice": 29,  "Supplier": "ACC"},
    {"Product_ID": 105, "SKU": "AP-PR2", "Name": "AirPods Pro",    "Category": "Accessory","Quantity": 20, "MinStock": 5,  "UnitPrice": 249, "Supplier": "ACME"},
])

def compute_products():
    df = base_products.copy()
    # apply threshold bump from Settings (e.g., 1.2 -> +20% MinStock)
    df["AdjMinStock"] = np.floor(df["MinStock"] * float(st.session_state.threshold_bump)).astype(int)
    df["Low"] = df["Quantity"] < df["AdjMinStock"]
    return df

products = compute_products()

supplier_summary = (products.groupby("Supplier")
                    .agg(Products=("Product_ID","nunique"),
                         Units=("Quantity","sum"))
                    .reset_index()
                    .rename(columns={"Supplier":"supplier"}))

if "chat" not in st.session_state:
    st.session_state.chat = []  # [{role:"user"/"bot", text:str}]

# ---------------------- UTILITIES ----------------------
def metric_tile(label, value, sub):
    st.markdown('<div class="tile">', unsafe_allow_html=True)
    st.markdown(f"<h4>{label}</h4><div class='big'>{value}</div><span>{sub}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def sales_bar(df):
    tmp = df.groupby(["Category","Supplier"], as_index=False)["Quantity"].sum()
    fig = px.bar(tmp, x="Quantity", y="Category", color="Supplier", orientation="h",
                 color_discrete_sequence=["#34c38f","#f39c12","#4b77be"])
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), legend_title_text="Supplier",
                      xaxis_title="Sales / Units", yaxis_title=None, bargap=.25,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
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

# ── Chat over the dataframe ──────────────────────────────────────────────────
def answer(q: str) -> str:
    ql = q.lower().strip()

    # 0) ID lookup by name
    m = re.search(r"(?:id\s+of|id\s+for)\s+([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"I couldn't find any product matching '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} → ID {int(r['Product_ID'])}, SKU {r['SKU']}."

    # 1) low stock list
    if "low stock" in ql or "need restock" in ql or "restocking" in ql:
        lows = products.loc[products["Low"], ["Name","Quantity","AdjMinStock"]]
        if lows.empty:
            return "All items are at or above minimum stock."
        rows = [f"- {r.Name}: {int(r.Quantity)}/{int(r.AdjMinStock)} (below min)" for r in lows.itertuples()]
        return "Items that need restocking:\n" + "\n".join(rows)

    # 2) quantity of a product by name
    m = re.search(r"quantity of ([\w\s\-]+)", ql)
    if m:
        name = m.group(1).strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"I couldn't find any product matching '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} — Quantity: {int(r['Quantity'])}, Min: {int(r['AdjMinStock'])}."

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
        return f"{r['Name']} costs {st.session_state.currency}{int(r['UnitPrice'])}."

    # 5) find by SKU (or “code …”)
    m = re.search(r"(?:sku|code)\s*([a-z0-9\-]+)", ql)
    if m:
        sku = m.group(1).upper()
        match = products[products["SKU"].str.upper() == sku]
        if match.empty:
            return f"I can't find any product with SKU '{sku}'."
        r = match.iloc[0]
        return (f"{r['Name']} — ID {int(r['Product_ID'])}, Qty {int(r['Quantity'])}, "
                f"Min {int(r['AdjMinStock'])}, Price {st.session_state.currency}{int(r['UnitPrice'])}, "
                f"Supplier {r['Supplier']}.")

    # 6) generic help
    return ("I didn't understand. Try:\n"
            " • 'low stock'\n"
            " • 'id for iPhone'\n"
            " • 'quantity of iPhone'\n"
            " • 'supplier of AirPods'\n"
            " • 'price of MacBook'\n"
            " • 'sku GS24'")

def chat_ui():
    st.subheader("Chat Assistant")
    st.markdown('<div class="paper">', unsafe_allow_html=True)

    # input
    user_q = st.text_input("Ask about stock, SKU, supplier, price…", key="chat_q")
    if user_q:
        st.session_state.chat.append({"role":"user","text":user_q})
        st.session_state.chat.append({"role":"bot","text":answer(user_q)})
        st.rerun()  # <-- fix for Streamlit Cloud (replaces experimental_rerun)

    # history
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    if not st.session_state.chat:
        st.info("Ask: 'low stock', 'id for iPhone', 'quantity of iPhone', 'supplier of AirPods', 'price of MacBook', 'sku GS24'.")
    for m in st.session_state.chat[-50:]:
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

    # === Metric tiles inside a single paper (NO empty stretch column) ===
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_tile("Stock Items", products["Product_ID"].nunique(), "distinct products")
    with c2: metric_tile("Low Stock", int(products["Low"].sum()), "below minimum")
    with c3: metric_tile("Reorder Needed", int(products["Low"].sum()), "order these")
    with c4: metric_tile("In Stock", int((~products["Low"]).sum()), "OK level")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Supplier & Sales (left) + Chat (right) each in their own paper ===
    left, right = st.columns([7,5], gap="large")
    with left:
        st.markdown('<div class="paper">', unsafe_allow_html=True)
        st.subheader("Supplier & Sales Data")
        st.plotly_chart(sales_bar(products), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        chat_ui()

    st.markdown("<br>", unsafe_allow_html=True)

    # === Trend ===
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.subheader("Trend Performance — Top-Selling Products")
    st.plotly_chart(trend_line(), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Inventory":
    st.title("Inventory")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    df_display = products[["Product_ID","SKU","Name","Category","Quantity","AdjMinStock","UnitPrice","Supplier","Low"]]
    df_display = df_display.rename(columns={"AdjMinStock":"MinStock"})
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

    st.subheader("Display")
    col1, col2 = st.columns(2)
    with col1:
        accent = st.color_picker("Accent color", value=st.session_state.accent, key="acc_color")
    with col2:
        currency = st.selectbox("Currency", ["$", "€", "£", "AED", "SAR"], index=["$","€","£","AED","SAR"].index(st.session_state.currency))
    st.session_state.currency = currency
    if accent != st.session_state.accent:
        st.session_state.accent = accent
        inject_css(accent)

    st.subheader("Inventory Rules")
    st.session_state.threshold_bump = st.slider(
        "Minimum stock multiplier", min_value=0.5, max_value=2.0, value=float(st.session_state.threshold_bump), step=0.1,
        help="1.0 keeps your MinStock as-is, 1.2 increases all MinStock by 20%, etc."
    )
    # Recompute products with new settings on demand
    if st.button("Apply inventory rules"):
        st.experimental_set_query_params()  # harmless nudge
        st.rerun()

    st.subheader("Data")
    csv_bytes = compute_products().to_csv(index=False).encode("utf-8")
    st.download_button("Download products.csv", data=csv_bytes, file_name="products.csv", mime="text/csv")

    st.markdown('</div>', unsafe_allow_html=True)
