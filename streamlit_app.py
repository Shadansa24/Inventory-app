import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Load datasets ---
products = pd.read_csv("data/products.csv")
sales = pd.read_csv("data/sales.csv")
suppliers = pd.read_csv("data/suppliers.csv")

# --- إعداد الصفحة ---
st.set_page_config(layout="wide")

# --- CSS ---
def load_css():
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
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 18px;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
                padding: 25px 25px 35px 25px;
                margin-bottom: 25px;
            }
            .card-title {
                font-size: 1.2rem;
                font-weight: 700;
                color: #1c2d3a;
                margin-bottom: 15px;
            }
            .kpi-metric { text-align: center; margin-top: -10px; }
            .kpi-title { font-size: 0.9rem; color: #888; }
            .kpi-number { font-size: 1.6rem; font-weight: 600; }
            .kpi-items { font-size: 0.85rem; color: #777; }

            /* Chat */
            .chat-container {
                background-color: rgba(255,255,255,0.95);
                border-radius: 18px;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
                padding: 20px;
                height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
            }
            .chat-box {
                overflow-y: auto;
                padding: 10px;
                flex-grow: 1;
            }
            .chat-bubble {
                padding: 10px 14px;
                border-radius: 12px;
                margin-bottom: 10px;
                max-width: 85%;
            }
            .user-msg { background-color: #e1f0ff; align-self: flex-end; margin-left: 15%; }
            .bot-msg { background-color: #f1f4f7; align-self: flex-start; margin-right: 15%; }
        </style>
    """, unsafe_allow_html=True)

# --- Stock Overview (live from dataset) ---
def render_stock_overview():
    low_stock = products[products["Quantity"] < products["MinStock"]]
    reorder = products[(products["Quantity"] <= products["MinStock"]) & (products["Quantity"] > 0)]
    in_stock = products[products["Quantity"] >= products["MinStock"]]

    col1, col2, col3 = st.columns(3)

    def gauge(value, color):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                'axis': {'range': [None, len(products)]},
                'bar': {'color': color, 'thickness': 0.3},
                'bgcolor': "#f5f5f5"
            },
        ))
        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0))
        return fig

    with col1:
        st.plotly_chart(gauge(len(low_stock), "#E74C3C"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Low Stock</div><div class="kpi-number" style="color:#E74C3C;">{len(low_stock)}</div><div class="kpi-items">Items below threshold</div></div>', unsafe_allow_html=True)
    with col2:
        st.plotly_chart(gauge(len(reorder), "#F39C12"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Reorder</div><div class="kpi-number" style="color:#F39C12;">{len(reorder)}</div><div class="kpi-items">Pending reorder</div></div>', unsafe_allow_html=True)
    with col3:
        st.plotly_chart(gauge(len(in_stock), "#2ECC71"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">In Stock</div><div class="kpi-number" style="color:#2ECC71;">{len(in_stock)}</div><div class="kpi-items">Available inventory</div></div>', unsafe_allow_html=True)

# --- Supplier & Sales Data ---
def render_supplier_sales():
    merged = sales.merge(products, on="Product_ID").merge(suppliers, on="Supplier_ID")
    supplier_sales = merged.groupby("Supplier_Name")["Qty"].sum().reset_index()

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=supplier_sales["Supplier_Name"],
            x=supplier_sales["Qty"],
            orientation="h",
            marker_color=['#3498DB', '#F39C12', '#2ECC71']
        ))
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10),
                          plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<b>Sales Breakdown</b>", unsafe_allow_html=True)
        for _, row in supplier_sales.iterrows():
            st.markdown(f"<div>{row['Supplier_Name']} ({row['Qty']} sold)</div>", unsafe_allow_html=True)

# --- Simple Chat Assistant ---
def render_chat_assistant():
    st.markdown('<div class="card"><div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask something...", placeholder="e.g. Check SKU IPH-15 or show low stock")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        bot_reply = chat_logic(user_input)
        st.session_state.chat_history.append(("bot", bot_reply))

    st.markdown('<div class="chat-container"><div class="chat-box">', unsafe_allow_html=True)
    for role, msg in st.session_state.chat_history:
        css_class = "user-msg" if role == "user" else "bot-msg"
        st.markdown(f"<div class='chat-bubble {css_class}'>{msg}</div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def chat_logic(query):
    query = query.lower()
    if "low stock" in query:
        low = products[products["Quantity"] < products["MinStock"]]
        if low.empty:
            return "All items are above minimum stock."
        return "Low stock items:\n" + ", ".join(low["Name"].tolist())

    elif "sku" in query or "stock" in query:
        sku = query.split()[-1].upper()
        item = products[products["SKU"] == sku]
        if item.empty:
            return f"No item found for SKU {sku}."
        row = item.iloc[0]
        return f"{row['Name']} has {row['Quantity']} units available (Supplier: {row['Supplier_ID']})."

    elif "supplier" in query:
        return ", ".join(suppliers["Supplier_Name"].tolist())

    elif "id for" in query:
        name = query.replace("what is the id for", "").strip().title()
        item = products[products["Name"].str.contains(name, case=False, na=False)]
        if item.empty:
            return f"No product found matching '{name}'."
        return f"The ID for {item.iloc[0]['Name']} is {item.iloc[0]['Product_ID']}."

    return "Try asking things like: 'Check SKU IPH-15', 'Show low stock items', or 'List suppliers'."

# --- Trend Performance (static for now) ---
def render_trend_performance():
    trend = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Product A': [40, 45, 60, 55, 70, 85],
        'Product B': [30, 50, 40, 65, 60, 75],
        'Product C': [50, 35, 55, 45, 50, 60]
    })
    fig = go.Figure()
    for name, color in zip(['Product A', 'Product B', 'Product C'], ['#007AFF', '#FF9500', '#34C759']):
        fig.add_trace(go.Scatter(
            x=trend["Month"], y=trend[name],
            mode="lines+markers", name=name,
            line=dict(color=color, width=3)
        ))
    fig.update_layout(
        title="Top-Selling Products",
        title_x=0.5,
        height=300,
        margin=dict(l=10, r=10, t=40, b=20),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#eee'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.markdown('<div class="card"><div class="card-title">Trend Performance</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Layout ---
load_css()
st.markdown('<div class="card"><div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
render_stock_overview()
st.markdown("</div>", unsafe_allow_html=True)
render_supplier_sales()
c1, c2 = st.columns(2)
with c1: render_chat_assistant()
with c2: render_trend_performance()
