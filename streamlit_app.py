import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- إعداد الصفحة ---
st.set_page_config(layout="wide")

# --- Load dataset ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("products.csv")
        df.columns = [c.strip().lower() for c in df.columns]  # normalize columns
        return df
    except Exception as e:
        st.error(f"❌ Error loading products.csv: {e}")
        return pd.DataFrame()

df = load_data()

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
            .nav-card {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 20px;
                padding: 20px;
                box-shadow: 0 8px 14px rgba(0, 0, 0, 0.1);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .nav-item {
                display: flex; align-items: center;
                padding: 10px 15px;
                font-size: 1rem;
                font-weight: 500;
                color: #333;
                border-radius: 10px;
                margin-bottom: 10px;
                transition: all 0.2s;
            }
            .nav-item:hover { background-color: #dbe9f5; color: #000; }
            .nav-item.active { background-color: #bcd7ec; font-weight: 600; }
            .nav-item span { margin-right: 10px; }
            .card {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 18px;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
                padding: 25px 25px 35px 25px;
                margin-bottom: 25px;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
            }
            .card-title { font-size: 1.2rem; font-weight: 700; color: #1c2d3a; margin-bottom: 15px; }
            .kpi-metric { text-align: center; margin-top: -10px; }
            .kpi-title { font-size: 0.9rem; color: #888; }
            .kpi-number { font-size: 1.6rem; font-weight: 600; }
            .kpi-items { font-size: 0.85rem; color: #777; }
            .chat-bubble { padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; max-width: 80%; }
            .user-msg { background-color: #e1f0ff; align-self: flex-end; margin-left: 20%; }
            .bot-msg { background-color: #f1f4f7; align-self: flex-start; margin-right: 20%; }
            .chat-box {
                height: 220px; overflow-y: auto;
                background: #f9fcff; border-radius: 10px;
                padding: 15px; margin-bottom: 10px;
                box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
            }
            .legend-item { display: flex; align-items: center; margin-bottom: 8px; }
            .legend-color-box { width: 15px; height: 15px; border-radius: 4px; margin-right: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
def render_sidebar():
    st.markdown("""
        <div class="nav-card">
            <div class="nav-group-top">
                <div class="nav-item active"><span>📊</span> Dashboard</div>
                <div class="nav-item"><span>📦</span> Inventory</div>
                <div class="nav-item"><span>🚚</span> Suppliers</div>
                <div class="nav-item"><span>🛒</span> Orders</div>
                <div class="nav-item"><span>⚙️</span> Settings</div>
            </div>
            <div class="nav-group-bottom">
                <div class="nav-item"><span>💬</span> Chat Assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Stock Overview ---
def render_stock_overview(df):
    st.markdown('<div class="card"><div class="card-title">Stock Overview</div>', unsafe_allow_html=True)

    if df.empty:
        st.warning("No data loaded from products.csv")
        return

    low_stock = (df['stock'] < df['reorder_level']).sum()
    reorder = (df['stock'] <= df['reorder_level'] * 1.2).sum()
    in_stock = len(df[df['stock'] > df['reorder_level']])

    def gauge(value, color):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                'axis': {'range': [None, max(150, value * 1.2)]},
                'bar': {'color': color, 'thickness': 0.2},
                'bgcolor': "#f5f5f5"
            },
        ))
        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0))
        return fig

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(gauge(low_stock, "#E74C3C"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Low Stock</div><div class="kpi-number" style="color:#E74C3C;">{low_stock}</div><div class="kpi-items">Items below threshold</div></div>', unsafe_allow_html=True)
    with col2:
        st.plotly_chart(gauge(reorder, "#F39C12"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Reorder</div><div class="kpi-number" style="color:#F39C12;">{reorder}</div><div class="kpi-items">Pending reorder</div></div>', unsafe_allow_html=True)
    with col3:
        st.plotly_chart(gauge(in_stock, "#2ECC71"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">In Stock</div><div class="kpi-number" style="color:#2ECC71;">{in_stock}</div><div class="kpi-items">Available inventory</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Supplier & Sales ---
def render_supplier_sales(df):
    st.markdown('<div class="card"><div class="card-title">Supplier & Sales Data</div>', unsafe_allow_html=True)
    if df.empty:
        st.warning("No supplier data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col1, col2 = st.columns([2, 1])
    df_summary = df.groupby('supplier')['sales'].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_summary["supplier"], x=df_summary["sales"], orientation="h",
        marker_color=['#3498DB','#F39C12','#2ECC71','#E74C3C','#9B59B6','#1ABC9C']
    ))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10),
                      plot_bgcolor="white", paper_bgcolor="white")
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<b>Sales Breakdown</b>", unsafe_allow_html=True)
        for _, row in df_summary.iterrows():
            st.markdown(f"<div class='legend-item'><div class='legend-color-box' style='background-color:#3498DB;'></div>{row['supplier']}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Chat Assistant ---
def render_chat_assistant(df):
    st.markdown('<div class="card"><div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)

    user_query = st.text_input("Type your query...", placeholder="Ask about SKU, supplier, or stock...", label_visibility="collapsed")

    if user_query:
        st.markdown(f'<div class="chat-bubble user-msg">User: {user_query}</div>', unsafe_allow_html=True)

        response = handle_query(user_query, df)
        st.markdown(f'<div class="chat-bubble bot-msg">{response}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def handle_query(query, df):
    if df.empty:
        return "No product data loaded."

    q = query.lower()

    # Find by SKU
    if "sku" in q:
        import re
        skus = re.findall(r'\d+', q)
        if skus:
            sku = int(skus[0])
            match = df[df["sku"] == sku]
            if not match.empty:
                row = match.iloc[0]
                return f"SKU {sku}: {row['product_name']} — Stock: {row['stock']} units — Supplier: {row['supplier']}"
            return f"SKU {sku} not found."

    # Low stock
    if "low stock" in q:
        low_df = df[df["stock"] < df["reorder_level"]]
        if low_df.empty:
            return "No items are below their threshold."
        return "Low stock items:<br>" + "<br>".join(f"- {r['product_name']} ({r['stock']} units)" for _, r in low_df.iterrows())

    # Supplier info
    if "supplier" in q:
        suppliers = df['supplier'].unique().tolist()
        return f"Suppliers: {', '.join(suppliers)}"

    # Default
    return "I'm not sure what you mean. Try asking about a SKU, supplier, or low stock items."

# --- Trend Performance ---
def render_trend_performance():
    st.markdown("""
        <div class="card">
            <div style="margin-bottom:15px;">
                <span class="card-title">Trend Performance</span>
            </div>
        """, unsafe_allow_html=True)
    trend = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Product A': [40, 45, 60, 55, 70, 85],
        'Product B': [30, 50, 40, 65, 60, 75],
        'Product C': [50, 35, 55, 45, 50, 60]
    })
    fig = go.Figure()
    for name, color in zip(['Product A','Product B','Product C'], ['#007AFF','#FF9500','#34C759']):
        fig.add_trace(go.Scatter(x=trend["Month"], y=trend[name],
                                 mode="lines+markers", name=name,
                                 line=dict(color=color, width=3)))
    fig.update_layout(title="Top-Selling Products", title_x=0.5, height=300,
                      margin=dict(l=10, r=10, t=40, b=20),
                      paper_bgcolor="white", plot_bgcolor="white",
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#eee'),
                      legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Layout ---
load_css()
col_nav, col_content = st.columns([1, 4])

with col_nav:
    render_sidebar()

with col_content:
    render_stock_overview(df)
    render_supplier_sales(df)
    c1, c2 = st.columns(2)
    with c1: render_chat_assistant(df)
    with c2: render_trend_performance()
