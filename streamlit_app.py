import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Inventory Dashboard")

# -------------------------
# Load data
# -------------------------
@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    suppliers = pd.read_csv("data/suppliers.csv")
    sales = pd.read_csv("data/sales.csv")
    return products, suppliers, sales

products, suppliers, sales = load_data()

# -------------------------
# Basic metrics
# -------------------------
low_stock = products[products["Quantity"] < products["MinStock"]]
reorder = products[(products["Quantity"] >= products["MinStock"]) & (products["Quantity"] <= products["MinStock"] * 2)]
in_stock = products[products["Quantity"] > products["MinStock"] * 2]

# -------------------------
# Style
# -------------------------
st.markdown("""
    <style>
        .stApp {
            background: radial-gradient(1300px 900px at 50% -10%, #e9f5ff 0%, #cfe2eb 40%, #97b6c0 100%);
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 1500px;
        }
        .card {
            background-color: rgba(173,216,230,0.6);
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            padding: 25px 30px;
            margin-bottom: 25px;
        }
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #222;
            margin-bottom: 25px;
        }
        .kpi-metric { text-align: center; }
        .kpi-title { font-size: 0.9rem; color: #888; }
        .kpi-number { font-size: 1.5rem; font-weight: 600; }
        .kpi-items { font-size: 0.85rem; color: #777; }
        .chat-bubble { padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; max-width: 80%; }
        .user-msg { background-color: #e1f0ff; align-self: flex-end; margin-left: 20%; }
        .bot-msg { background-color: #f1f4f7; align-self: flex-start; margin-right: 20%; }
        .chat-box {
            height: 220px; overflow-y: auto;
            background: lightblue; border-radius: 10px;
            padding: 15px; margin-bottom: 10px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
        }
        .legend-item { display: flex; align-items: center; margin-bottom: 10px; }
        .legend-color-box { width: 15px; height: 15px; border-radius: 4px; margin-right: 10px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# STOCK OVERVIEW CARD
# -------------------------
def render_stock_overview():
    st.markdown('<div class="card"><div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    def gauge(value, color, max_val):
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=value,
            gauge={'axis': {'range': [None, max_val]},
                   'bar': {'color': color, 'thickness': 0.25},
                   'bgcolor': "#f5f5f5"}))
        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0))
        return fig

    with col1:
        st.plotly_chart(gauge(len(low_stock), "#E74C3C", 10), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Low Stock</div><div class="kpi-number" style="color:#E74C3C;">{len(low_stock)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.plotly_chart(gauge(len(reorder), "#F39C12", 10), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Reorder</div><div class="kpi-number" style="color:#F39C12;">{len(reorder)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.plotly_chart(gauge(len(in_stock), "#2ECC71", 10), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">In Stock</div><div class="kpi-number" style="color:#2ECC71;">{len(in_stock)}</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# SUPPLIER SALES CARD
# -------------------------
def render_supplier_sales():
    st.markdown('<div class="card"><div class="card-title">Supplier Stock Summary</div>', unsafe_allow_html=True)
    supplier_summary = products.groupby("Supplier_ID")["Quantity"].sum().reset_index()
    supplier_summary = supplier_summary.merge(suppliers, on="Supplier_ID", how="left")
    fig = go.Figure(go.Bar(
        y=supplier_summary["Supplier_Name"],
        x=supplier_summary["Quantity"],
        orientation="h",
        marker_color=['#3498DB','#F39C12','#2ECC71']))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10),
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# SALES TREND CARD
# -------------------------
def render_sales_trend():
    st.markdown('<div class="card"><div class="card-title">Sales Trend</div>', unsafe_allow_html=True)
    sales["Timestamp"] = pd.to_datetime(sales["Timestamp"])
    monthly = sales.groupby(sales["Timestamp"].dt.strftime("%b"))["Qty"].sum().reindex(
        ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]).fillna(0)
    fig = go.Figure(go.Scatter(
        x=monthly.index, y=monthly.values,
        mode="lines+markers", line=dict(color="#007AFF", width=3)))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=20),
                      paper_bgcolor="white", plot_bgcolor="white",
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#eee'))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# CHAT ASSISTANT CARD
# -------------------------
def render_chat_assistant():
    st.markdown('<div class="card"><div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    query = st.text_input("Ask something (e.g., 'Check stock for SKU IPH-15')", label_visibility="collapsed")

    if query:
        st.session_state.chat_history.append(("user", query))
        response = handle_query(query)
        st.session_state.chat_history.append(("bot", response))

    # display chat
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for sender, msg in st.session_state.chat_history[-6:]:
        bubble_class = "user-msg" if sender == "user" else "bot-msg"
        st.markdown(f'<div class="chat-bubble {bubble_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def handle_query(text):
    text = text.lower()
    if "sku" in text:
        parts = text.split("sku")
        if len(parts) > 1:
            sku = parts[1].strip().upper().replace(" ", "")
            match = products[products["SKU"].str.upper() == sku]
            if not match.empty:
                row = match.iloc[0]
                supplier = suppliers[suppliers["Supplier_ID"] == row["Supplier_ID"]]["Supplier_Name"].values[0]
                return f"{row['Name']} — {row['Quantity']} units available. Supplier: {supplier}."
            return "SKU not found in product list."
    if "low stock" in text:
        return f"There are {len(low_stock)} items below minimum stock."
    if "reorder" in text:
        return f"{len(reorder)} items are in the reorder range."
    if "help" in text:
        return "You can ask: 'Check stock for SKU GS24' or 'Show low stock'."
    return "Sorry, I didn't understand that. Try 'Check stock for SKU ...'."

# -------------------------
# Layout
# -------------------------
render_stock_overview()
render_supplier_sales()
col1, col2 = st.columns(2)
with col1:
    render_chat_assistant()
with col2:
    render_sales_trend()
