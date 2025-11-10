# app.py — Streamlit Dashboard (Clean Layout Version)
# Designed for Streamlit Cloud

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")

# ----------------------------- CUSTOM STYLING -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: radial-gradient(1400px 800px at 50% -15%, #eaf4ff 0%, #d4e6ee 38%, #97b6c0 100%);
}
.block-container {padding-top:1rem; padding-bottom:1rem;}
.sidebar-wrap {
    background: rgba(255,255,255,.8);
    backdrop-filter: blur(3px);
    border-radius: 16px;
    box-shadow: 0 10px 20px rgba(0,0,0,.08);
    padding: 18px 14px;
}
.sb-item {
    display:flex; align-items:center; gap:.65rem;
    font-weight:600; color:#3b4a54;
    background:#fff; border:1px solid #e8eef2;
    padding:.7rem .75rem; border-radius:12px;
    margin:.35rem 0; box-shadow: 0 3px 8px rgba(0,0,0,.05);
}
.sb-item.active {
    background:#edf6ff; border-color:#cfe2ff; color:#1e6fd8;
}
.card {
    background:#ffffff;
    border:1px solid rgba(35,73,102,.08);
    border-radius:14px;
    box-shadow:0 12px 24px rgba(0,0,0,.08);
    padding:16px 20px;
}
.card h3 {
    margin:.1rem 0 1rem 0; font-size:1.1rem; font-weight:800; color:#2d3c45;
}
.kpi-caption {color:#7c8c98; font-size:.8rem; text-align:center;}
.chat-input {
    background:#ffffff; border:1px solid #e6edf3;
    border-radius:10px; padding:10px 12px; color:#5c6d79;
}
.chat-bubble {
    background:#f6fbff; border:1px solid #ddebf6;
    border-radius:12px; padding:10px 12px; margin-top:10px;
    color:#6b7a86; font-size:.9rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- DATA -----------------------------
low_stock, reorder, instock = 47, 120, 890

suppliers = pd.DataFrame({
    "Supplier": ["Acme Corp", "Innovate Ltd", "Global Goods"],
    "Sales": [38, 28, 18]
})
categories = pd.DataFrame({
    "Category": ["Electronics", "Apparel", "Home Goods"],
    "Sales": [40, 26, 14]
})
trend = pd.DataFrame({
    "Month":["Jan","Feb","Mar","Apr","May","Jun"],
    "Product A":[20,45,60,75,85,108],
    "Product B":[15,35,50,65,85,95]
})

# ----------------------------- HELPERS -----------------------------
def donut(value, total, color, label):
    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=[value, total - value],
        hole=.7, sort=False,
        marker_colors=[color, "#edf2f6"], textinfo="none"
    ))
    fig.update_layout(
        width=200, height=140, margin=dict(l=0,r=0,t=0,b=0),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)"
    )
    fig.add_annotation(text=f"<b>{label}</b><br><span style='font-size:22px'>{value}</span>",
                       x=0.5, y=0.5, showarrow=False)
    return fig

def hbar(df, color):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Sales"], y=df[df.columns[0]],
        orientation='h', marker_color=color,
        text=df["Sales"], textposition="outside"
    ))
    fig.update_layout(
        height=180, margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(title=None)
    )
    return fig

def line_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Month"], y=df["Product A"], mode="lines+markers",
                             name="Product A", line=dict(width=3, color="#007AFF")))
    fig.add_trace(go.Scatter(x=df["Month"], y=df["Product B"], mode="lines+markers",
                             name="Product B", line=dict(width=3, color="#FF9500")))
    fig.update_layout(
        height=260, margin=dict(l=10,r=10,t=30,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
    )
    return fig

# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="sb-item active">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">📦 Inventory</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">🤝 Suppliers</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">🧾 Orders</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">💬 Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------- MAIN DASHBOARD -----------------------------
st.markdown("<h1 style='font-weight:900; color:#26323a;'>Inventory Management Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# === STOCK OVERVIEW ===
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Stock Overview</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(donut(low_stock, 150, "#f24b5b", "Low Stock"), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"<div class='kpi-caption'>{low_stock} Items</div>", unsafe_allow_html=True)
    with c2:
        st.plotly_chart(donut(reorder, 150, "#f3b234", "Reorder"), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"<div class='kpi-caption'>{reorder} Items</div>", unsafe_allow_html=True)
    with c3:
        st.plotly_chart(donut(instock, 1000, "#24c285", "In Stock"), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"<div class='kpi-caption'>{instock} Items</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# === SUPPLIER & SALES ===
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Supplier & Sales Data (Q3)</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top Suppliers (Q3)**")
        st.plotly_chart(hbar(suppliers, "#007AFF"), use_container_width=True, config={"displayModeBar":False})
    with c2:
        st.markdown("**Sales by Category (Q3)**")
        st.plotly_chart(hbar(categories, "#F39C12"), use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# === CHAT & TREND ROW ===
c1, c2 = st.columns([1.1, 1.9])
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)
    st.markdown('<div class="chat-input">Type your query…</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-bubble"><b>User:</b> “Check stock for SKU 789”<br><b>Bot:</b> SKU: 150 units available.<br>Supplier: Acme Corp.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Trend Performance</h3>", unsafe_allow_html=True)
    st.plotly_chart(line_chart(trend), use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)
