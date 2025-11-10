# app.py — Interactive Inventory Dashboard
# Streamlit Cloud ready

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Inventory Management", page_icon="📦", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    inv = pd.read_csv("data/inventory.csv")
    sup = pd.read_csv("data/suppliers.csv")
    sales = pd.read_csv("data/sales.csv")
    return inv, sup, sales

inventory, suppliers, sales = load_data()

# ---------- STYLE ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1300px 900px at 50% -10%, #e9f5ff 0%, #cfe2eb 40%, #97b6c0 100%);
}
.block-container {padding-top:1rem; padding-bottom:2rem;}
.sidebar-wrap {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(3px);
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
  padding: 18px 14px;
}
.sb-item {
  display:flex; align-items:center; gap:.65rem;
  font-weight:600; color:#3b4a54;
  background:#fff; border:1px solid #e8eef2;
  padding:.7rem .75rem; border-radius:12px;
  margin:.35rem 0; box-shadow: 0 3px 8px rgba(0,0,0,.06);
  cursor:pointer;
}
.sb-item.active {background:#edf6ff;border-color:#cfe2ff;color:#1e6fd8;}
h3 {color:#2d3c45;font-weight:800;font-size:1.1rem;}
.chat-box {
  background:#f6fbff;border:1px solid #ddebf6;border-radius:10px;
  padding:10px 14px;margin-top:8px;color:#4a5b65;font-size:.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- NAVIGATION ----------
st.sidebar.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Dashboard", "Inventory", "Suppliers", "Orders", "Settings", "Chat Assistant"],
                        label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ---------- UTILS ----------
def donut(value, total, color, label):
    fig = go.Figure()
    fig.add_trace(go.Pie(values=[value, total-value], hole=.7,
                         marker_colors=[color, "#edf2f6"], textinfo="none"))
    fig.update_layout(width=180, height=140, margin=dict(l=0,r=0,t=0,b=0),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    fig.add_annotation(text=f"<b>{label}</b><br><span style='font-size:22px'>{value}</span>",
                       x=0.5, y=0.5, showarrow=False)
    return fig

def hbar(df, xcol, ycol, color):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df[xcol], y=df[ycol], orientation="h",
                         marker_color=color, text=df[xcol], textposition="outside"))
    fig.update_layout(height=180, margin=dict(l=10,r=10,t=10,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(title=None))
    return fig

def line_chart(df):
    fig = go.Figure()
    for product in df.columns[1:]:
        fig.add_trace(go.Scatter(x=df["Month"], y=df[product], mode="lines+markers", name=product))
    fig.update_layout(height=260, margin=dict(l=10,r=10,t=30,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    return fig

# ---------- DASHBOARD ----------
if page == "Dashboard":
    st.markdown("<h1 style='font-weight:900; color:#26323a;'>Inventory Management Dashboard</h1>", unsafe_allow_html=True)

    low_stock = (inventory['Stock'] < 50).sum()
    reorder = ((inventory['Stock'] >= 50) & (inventory['Stock'] < 200)).sum()
    in_stock = (inventory['Stock'] >= 200).sum()

    st.markdown("<h3>Stock Overview</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(donut(low_stock, len(inventory), "#f24b5b", "Low Stock"), use_container_width=True)
    with c2:
        st.plotly_chart(donut(reorder, len(inventory), "#f3b234", "Reorder"), use_container_width=True)
    with c3:
        st.plotly_chart(donut(in_stock, len(inventory), "#24c285", "In Stock"), use_container_width=True)

    st.markdown("<h3>Supplier & Sales Data (Q3)</h3>", unsafe_allow_html=True)
    top_suppliers = suppliers.nlargest(3, 'Orders')
    categories = sales.groupby('Category')['Revenue'].sum().reset_index()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top Suppliers (Q3)**")
        st.plotly_chart(hbar(top_suppliers, "Orders", "Supplier", "#007AFF"), use_container_width=True)
    with c2:
        st.markdown("**Sales by Category (Q3)**")
        st.plotly_chart(hbar(categories, "Revenue", "Category", "#F39C12"), use_container_width=True)

    c1, c2 = st.columns([1.05, 1.9])
    with c1:
        st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)
        st.markdown('<div class="chat-box">Ask anything about stock or suppliers.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("<h3>Trend Performance</h3>", unsafe_allow_html=True)
        trend = sales.groupby('Month')[['Product A', 'Product B']].sum().reset_index()
        st.plotly_chart(line_chart(trend), use_container_width=True)

# ---------- INVENTORY ----------
elif page == "Inventory":
    st.title("📦 Inventory")
    st.dataframe(inventory)

# ---------- SUPPLIERS ----------
elif page == "Suppliers":
    st.title("🤝 Suppliers")
    st.dataframe(suppliers)

# ---------- ORDERS ----------
elif page == "Orders":
    st.title("🧾 Orders")
    st.dataframe(sales)

# ---------- SETTINGS ----------
elif page == "Settings":
    st.title("⚙️ Settings")
    st.info("Settings section placeholder — add configuration options later.")

# ---------- CHAT ASSISTANT ----------
elif page == "Chat Assistant":
    st.title("💬 Chat Assistant")
    query = st.text_input("Ask about your stock, suppliers, or sales:")
    if query:
        query_lower = query.lower()
        if "stock" in query_lower:
            sku = query_lower.split("sku")[-1].strip()
            row = inventory[inventory['SKU'].astype(str).str.contains(sku, case=False)]
            if not row.empty:
                qty = int(row['Stock'].values[0])
                supplier = row['Supplier'].values[0]
                st.success(f"SKU {sku} has {qty} units available from supplier {supplier}.")
            else:
                st.warning("SKU not found in inventory.")
        elif "supplier" in query_lower:
            names = ", ".join(suppliers['Supplier'].tolist())
            st.info(f"Available suppliers: {names}")
        elif "sales" in query_lower:
            total = sales['Revenue'].sum()
            st.success(f"Total sales revenue: ${total:,.2f}")
        else:
            st.warning("Sorry, I didn’t understand that query.")
