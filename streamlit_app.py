import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Inventory Dashboard")

# --- Load data ---
@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    suppliers = pd.read_csv("data/suppliers.csv")
    sales = pd.read_csv("data/sales.csv")
    return products, suppliers, sales

products, suppliers, sales = load_data()

# --- Derived metrics ---
low_stock = products[products["Quantity"] < products["MinStock"]]
reorder = products[(products["Quantity"] >= products["MinStock"]) & (products["Quantity"] <= products["MinStock"] * 2)]
in_stock = products[products["Quantity"] > products["MinStock"] * 2]

total_low = len(low_stock)
total_reorder = len(reorder)
total_in_stock = len(in_stock)

# Supplier summary
supplier_sales = products.groupby("Supplier_ID")["Quantity"].sum().reset_index()
supplier_sales = supplier_sales.merge(suppliers, on="Supplier_ID", how="left")

# Sales trend
sales["Timestamp"] = pd.to_datetime(sales["Timestamp"])
monthly_sales = sales.groupby(sales["Timestamp"].dt.strftime("%b"))["Qty"].sum().reindex(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
).fillna(0)

# --- Styles ---
def load_css():
    st.markdown("""
        <style>
            .stApp {
                background: radial-gradient(1300px 900px at 50% -10%, #e9f5ff 0%, #cfe2eb 40%, #97b6c0 100%);
            }
            .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1500px; }
            .card {
                background-color: rgba(173,216,230,0.6);
                border-radius: 16px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                padding: 25px 30px;
                margin-bottom: 25px;
            }
            .card-title {
                font-size: 1.25rem; font-weight: 600; color: #222;
                margin-bottom: 25px;
            }
            .kpi-metric { text-align: center; }
            .kpi-title { font-size: 0.9rem; color: #888; }
            .kpi-number { font-size: 1.5rem; font-weight: 600; }
            .kpi-items { font-size: 0.85rem; color: #777; }
            .legend-item { display: flex; align-items: center; margin-bottom: 10px; }
            .legend-color-box { width: 15px; height: 15px; border-radius: 4px; margin-right: 10px; }
        </style>
    """, unsafe_allow_html=True)

load_css()

# --- Stock Overview ---
def render_stock_overview():
    st.markdown('<div class="card"><div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    def gauge(value, color, max_val=20):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={'axis': {'range': [None, max_val]},
                   'bar': {'color': color, 'thickness': 0.25},
                   'bgcolor': "#f5f5f5"},
        ))
        fig.update_layout(height=160, margin=dict(l=0, r=0, t=10, b=0))
        return fig
    with col1:
        st.plotly_chart(gauge(total_low, "#E74C3C"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Low Stock</div><div class="kpi-number" style="color:#E74C3C;">{total_low}</div><div class="kpi-items">{len(low_stock)} Items</div></div>', unsafe_allow_html=True)
    with col2:
        st.plotly_chart(gauge(total_reorder, "#F39C12"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">Reorder</div><div class="kpi-number" style="color:#F39C12;">{total_reorder}</div><div class="kpi-items">{len(reorder)} Items</div></div>', unsafe_allow_html=True)
    with col3:
        st.plotly_chart(gauge(total_in_stock, "#2ECC71"), use_container_width=True)
        st.markdown(f'<div class="kpi-metric"><div class="kpi-title">In Stock</div><div class="kpi-number" style="color:#2ECC71;">{total_in_stock}</div><div class="kpi-items">{len(in_stock)} Items</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Supplier & Sales Data ---
def render_supplier_sales():
    st.markdown('<div class="card"><div class="card-title">Supplier & Stock Data</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure(go.Bar(
            y=supplier_sales["Supplier_Name"],
            x=supplier_sales["Quantity"],
            orientation="h",
            marker_color=['#3498DB','#F39C12','#2ECC71','#E74C3C','#9B59B6','#1ABC9C']
        ))
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10),
                          plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<b>Suppliers Overview</b>", unsafe_allow_html=True)
        for _, row in supplier_sales.iterrows():
            st.markdown(
                f"<div class='legend-item'><div class='legend-color-box' style='background-color:#3498DB;'></div>"
                f"{row['Supplier_Name']} — {row['Quantity']} units</div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

# --- Sales Trend ---
def render_trend():
    st.markdown('<div class="card"><div class="card-title">Sales Trend</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(
        x=monthly_sales.index,
        y=monthly_sales.values,
        mode="lines+markers",
        line=dict(color="#007AFF", width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(title="Units Sold Per Month", title_x=0.5,
                      height=300, margin=dict(l=10, r=10, t=40, b=20),
                      paper_bgcolor="white", plot_bgcolor="white",
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#eee"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chat Assistant (Static Placeholder) ---
def render_chat():
    st.markdown('<div class="card"><div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-box"><div class="chat-bubble user-msg">User: Check stock for SKU IPH-15</div>'
                f'<div class="chat-bubble bot-msg">Bot: {products.loc[products["SKU"]=="IPH-15", "Quantity"].values[0]} units available.<br>'
                f'Supplier: {products.loc[products["SKU"]=="IPH-15", "Supplier_ID"].values[0]}</div></div>',
                unsafe_allow_html=True)
    st.text_input("Type your query...", placeholder="Type your query...", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Layout ---
render_stock_overview()
render_supplier_sales()
c1, c2 = st.columns(2)
with c1: render_chat()
with c2: render_trend()
