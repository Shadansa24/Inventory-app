import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

            /* Cards (expanded bubbles) */
            .card {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 20px;
                box-shadow: 0 8px 22px rgba(0, 0, 0, 0.08);
                padding: 35px 30px 40px 30px; /* زودنا الـ padding السفلي */
                margin-bottom: 25px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .card-title {
                font-size: 1.3rem;
                font-weight: 700;
                color: #1c2d3a;
                margin-bottom: 20px;
                text-align: left;
            }

            /* باقي التنسيقات كما هي */
            .kpi-metric { text-align: center; margin-top: -10px; }
            .kpi-title { font-size: 0.9rem; color: #888; }
            .kpi-number { font-size: 1.6rem; font-weight: 600; }
            .kpi-items { font-size: 0.85rem; color: #777; }
            .chat-box {
                height: 250px; overflow-y: auto;
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
def render_stock_overview():
    st.markdown('<div class="card"><div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    def gauge(value, color):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                'axis': {'range': [None, 150]},
                'bar': {'color': color, 'thickness': 0.2},
                'bgcolor': "#f5f5f5"
            },
        ))
        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0))
        return fig

    with col1:
        st.plotly_chart(gauge(47, "#E74C3C"), use_container_width=True)
        st.markdown('<div class="kpi-metric"><div class="kpi-title">Low Stock</div><div class="kpi-number" style="color:#E74C3C;">47</div><div class="kpi-items">Items below threshold</div></div>', unsafe_allow_html=True)
    with col2:
        st.plotly_chart(gauge(120, "#F39C12"), use_container_width=True)
        st.markdown('<div class="kpi-metric"><div class="kpi-title">Reorder</div><div class="kpi-number" style="color:#F39C12;">120</div><div class="kpi-items">Pending reorder</div></div>', unsafe_allow_html=True)
    with col3:
        st.plotly_chart(gauge(890, "#2ECC71"), use_container_width=True)
        st.markdown('<div class="kpi-metric"><div class="kpi-title">In Stock</div><div class="kpi-number" style="color:#2ECC71;">890</div><div class="kpi-items">Available inventory</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Supplier & Sales ---
def render_supplier_sales():
    st.markdown('<div class="card"><div class="card-title">Supplier & Sales Data</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    suppliers = {
        'Acme Corp': 200, 'Innovate Ltd': 180, 'Global Goods': 120,
        'Apparel': 100, 'Home Goods': 90, 'Electronics': 150
    }
    df = pd.DataFrame(list(suppliers.items()), columns=["Supplier", "Sales"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Supplier"], x=df["Sales"], orientation="h",
        marker_color=['#3498DB','#F39C12','#2ECC71','#E74C3C','#9B59B6','#1ABC9C']
    ))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10),
                      plot_bgcolor="white", paper_bgcolor="white")
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<b>Sales Breakdown</b>", unsafe_allow_html=True)
        for c, color in [('Acme Corp','#3498DB'),('Innovate Ltd','#F39C12'),
                         ('Global Goods','#2ECC71'),('Apparel','#E74C3C'),
                         ('Home Goods','#9B59B6'),('Electronics','#1ABC9C')]:
            st.markdown(f"<div class='legend-item'><div class='legend-color-box' style='background-color:{color};'></div>{c}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Chat Assistant ---
def render_chat_assistant():
    st.markdown('<div class="card"><div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="chat-box">
            <div class="chat-bubble user-msg">User: Check stock for SKU 789</div>
            <div class="chat-bubble bot-msg">Bot: SKU 789 has 150 units available.<br>Supplier: Acme Corp.</div>
            <div class="chat-bubble user-msg">User: Show low stock items</div>
            <div class="chat-bubble bot-msg">Bot: 3 items below minimum stock. Reorder recommended.</div>
        </div>
    """, unsafe_allow_html=True)
    st.text_input("Type your query...", placeholder="Ask about SKU, supplier, or stock...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Trend Performance ---
def render_trend_performance():
    st.markdown('<div class="card"><div class="card-title">Trend Performance</div>', unsafe_allow_html=True)
    trend = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Product A': [40, 45, 60, 55, 70, 85],
        'Product B': [30, 50, 40, 65, 60, 75],
        'Product C': [50, 35, 55, 45, 50, 60]
    })
    fig = go.Figure()
    for name, color in zip(['Product A','Product B','Product C'], ['#007AFF','#FF9500','#34C759']):
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
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#eee'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Layout ---
load_css()
col_nav, col_content = st.columns([1, 4])

with col_nav:
    render_sidebar()

with col_content:
    render_stock_overview()
    render_supplier_sales()
    c1, c2 = st.columns(2)
    with c1: render_chat_assistant()
    with c2: render_trend_performance()
