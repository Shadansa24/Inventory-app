import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Inventory Management Dashboard", layout="wide")

# -------------------- LOAD CSS --------------------
def load_css():
    st.markdown("""
    <style>
        .stApp {
            background-color: #F0F4F8;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .nav-card {
            background-color: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 5px 10px -2px rgba(0,0,0,0.08);
            height: 100%;
            min-height: 100vh;
        }
        .nav-btn {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            width: 100%;
            padding: 10px 15px;
            border: none;
            border-radius: 10px;
            background: #fff;
            margin-bottom: 8px;
            color: #444;
            font-weight: 500;
            cursor: pointer;
            transition: 0.2s;
        }
        .nav-btn:hover {
            background-color: #E6EBF0;
        }
        .nav-btn.active {
            background-color: #E0E8F0;
            color: #007AFF;
            font-weight: 600;
        }
        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #222;
            margin-bottom: 15px;
        }
        .chat-bubble { padding: 8px 12px; border-radius: 15px; margin-bottom: 10px; max-width: 80%; line-height: 1.4; }
        .user-msg { background-color: #F0F4F8; text-align: right; margin-left: 20%; }
        .bot-msg { background-color: #E0E8F0; margin-right: 20%; }
        .legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.95rem; }
        .legend-color-box { width: 15px; height: 15px; border-radius: 4px; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# -------------------- MOCK DATA --------------------
@st.cache_data
def load_data():
    df = pd.DataFrame([
        {"SKU":"A101","Product":"iPhone 15","Category":"Mobile","Qty":12,"MinStock":15,"Price":999,"Supplier":"ACME"},
        {"SKU":"B202","Product":"Galaxy S24","Category":"Mobile","Qty":30,"MinStock":8,"Price":899,"Supplier":"GX"},
        {"SKU":"C303","Product":"MacBook Air M3","Category":"Laptop","Qty":5,"MinStock":8,"Price":1299,"Supplier":"ACME"},
        {"SKU":"D404","Product":"AirPods Pro","Category":"Accessory","Qty":20,"MinStock":5,"Price":249,"Supplier":"ACME"},
        {"SKU":"E505","Product":"Logitech Mouse","Category":"Accessory","Qty":3,"MinStock":5,"Price":29,"Supplier":"ACC"}
    ])
    return df

df = load_data()

# -------------------- SIDEBAR NAVIGATION --------------------
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_button(label, icon, key):
    css = "nav-btn active" if st.session_state.page == key else "nav-btn"
    if st.button(f"{icon} {label}", key=f"btn_{key}", use_container_width=True):
        st.session_state.page = key

with st.sidebar:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    nav_button("Dashboard", "📊", "Dashboard")
    nav_button("Inventory", "📦", "Inventory")
    nav_button("Suppliers", "🚚", "Suppliers")
    nav_button("Orders", "🛒", "Orders")
    nav_button("Chat Assistant", "💬", "Chat")
    nav_button("Settings", "⚙️", "Settings")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- DASHBOARD PAGE --------------------
def dashboard():
    st.title("📊 Inventory Management Dashboard")

    # --- KPIs ---
    total_items = len(df)
    low_stock = len(df[df["Qty"] < df["MinStock"]])
    reorder_needed = low_stock
    in_stock = df["Qty"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stock Items", total_items)
    col2.metric("Low Stock", low_stock)
    col3.metric("Reorder Needed", reorder_needed)
    col4.metric("In Stock", in_stock)

    st.divider()

    # --- SUPPLIER & SALES ---
    st.subheader("Supplier & Sales Data")
    supplier_sales = df.groupby("Supplier")["Qty"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=supplier_sales["Qty"],
        y=supplier_sales["Supplier"],
        orientation='h',
        marker_color=['#007AFF','#F39C12','#2ECC71'],
        text=supplier_sales["Qty"],
        textposition='outside'
    ))
    fig.update_layout(
        height=300, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor="white", plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- TREND PERFORMANCE ---
    st.subheader("Trend Performance")
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    product_A = [40, 45, 60, 55, 70, 85]
    product_B = [30, 50, 40, 65, 60, 75]
    product_C = [50, 35, 55, 45, 50, 60]

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=months, y=product_A, mode='lines+markers', name='Product A', line=dict(color='#007AFF', width=3)))
    fig2.add_trace(go.Scatter(x=months, y=product_B, mode='lines+markers', name='Product B', line=dict(color='#FF9500', width=3)))
    fig2.add_trace(go.Scatter(x=months, y=product_C, mode='lines+markers', name='Product C', line=dict(color='#34C759', width=3)))

    fig2.update_layout(
        height=280,
        margin=dict(l=20,r=20,t=40,b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

# -------------------- INVENTORY PAGE --------------------
def inventory():
    st.title("📦 Inventory Overview")

    col1, col2, col3 = st.columns(3)
    category = col1.selectbox("Category", ["All"] + sorted(df["Category"].unique()))
    supplier = col2.selectbox("Supplier", ["All"] + sorted(df["Supplier"].unique()))
    price_min, price_max = col3.slider("Price Range", 0, 2000, (0,2000))

    filtered = df.copy()
    if category != "All":
        filtered = filtered[filtered["Category"] == category]
    if supplier != "All":
        filtered = filtered[filtered["Supplier"] == supplier]
    filtered = filtered[(filtered["Price"] >= price_min) & (filtered["Price"] <= price_max)]

    st.dataframe(filtered, use_container_width=True)

    st.download_button("📤 Export Filtered Data", filtered.to_csv(index=False).encode(), "inventory.csv", "text/csv")

# -------------------- CHAT PAGE --------------------
def chat_page():
    st.title("💬 Chat Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble user-msg'>{msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble bot-msg'>{msg['text']}</div>", unsafe_allow_html=True)

    query = st.text_input("Ask about stock, SKU, supplier, or price...")
    if query:
        st.session_state.chat.append({"role":"user","text":query})
        df_lookup = df[df["Product"].str.lower().str.contains(query.lower())]
        if not df_lookup.empty:
            info = df_lookup.iloc[0]
            answer = f"Product **{info['Product']}** (SKU: {info['SKU']}) — Qty: {info['Qty']} | Supplier: {info['Supplier']} | Price: ${info['Price']}"
        else:
            answer = "Sorry, I couldn’t find that product."
        st.session_state.chat.append({"role":"bot","text":answer})
        st.rerun()

# -------------------- PAGE ROUTING --------------------
if st.session_state.page == "Dashboard":
    dashboard()
elif st.session_state.page == "Inventory":
    inventory()
elif st.session_state.page == "Chat":
    chat_page()
else:
    st.title(f"{st.session_state.page} section is under construction.")
