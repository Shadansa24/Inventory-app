# app.py — same layout, now linked to your CSV dataset and working chatbot

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")

# ------------------ STYLE ------------------
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
}
.sb-item.active {background:#edf6ff;border-color:#cfe2ff;color:#1e6fd8;}

h3 {
  color:#2d3c45; font-weight:800; font-size:1.1rem;
  margin-top:0; margin-bottom:.8rem;
}
.kpi-caption {color:#6c7a86; font-size:.82rem; text-align:center;}
.chat-box {
  background:#f6fbff; border:1px solid #ddebf6;
  border-radius:10px; padding:10px 14px; margin-top:8px;
  color:#4a5b65; font-size:.9rem;
}
</style>
""", unsafe_allow_html=True)

# ------------------ DATA ------------------
@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    suppliers = pd.read_csv("data/suppliers.csv")
    sales = pd.read_csv("data/sales.csv")

    # --- Fix sales dataset ---
    if "Qty" in sales.columns and "UnitPrice" in sales.columns:
        sales["Revenue"] = sales["Qty"] * sales["UnitPrice"]
    if "Timestamp" in sales.columns:
        sales["Month"] = pd.to_datetime(sales["Timestamp"]).dt.strftime("%Y-%m")

    # --- Merge supplier info for later use ---
    merged = pd.merge(products, suppliers, on="Supplier_ID", how="left")

    return products, suppliers, sales, merged


try:
    products, suppliers, sales, merged = load_data()
except FileNotFoundError as e:
    st.error(f"⚠️ Missing data file: {e.filename}. Make sure products.csv, suppliers.csv, and sales.csv are inside /data.")
    st.stop()

# --- KPIs ---
low_stock = (products['Quantity'] < products['MinStock']).sum()
reorder = ((products['Quantity'] >= products['MinStock']) & (products['Quantity'] < products['MinStock'] * 2)).sum()
instock = (products['Quantity'] >= products['MinStock'] * 2).sum()

# --- Supplier Sales Summary ---
suppliers_sum = (
    merged.groupby("Supplier_Name")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Sales"})
    if "Supplier_Name" in merged.columns else pd.DataFrame({"Supplier_Name": [], "Sales": []})
)

# --- Category Sales Summary ---
if "Category" in products.columns:
    categories = products.groupby("Category")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Sales"})
else:
    categories = pd.DataFrame({"Category": [], "Sales": []})

# --- Trend Summary ---
if "Month" in sales.columns and "Revenue" in sales.columns:
    trend = sales.groupby("Month")["Revenue"].sum().reset_index()
else:
    trend = pd.DataFrame()


# ------------------ CHART HELPERS ------------------
def donut(value, total, color, label):
    fig = go.Figure()
    fig.add_trace(go.Pie(values=[value, total - value], hole=.7, marker_colors=[color, "#edf2f6"], textinfo="none"))
    fig.update_layout(width=180, height=140, margin=dict(l=0,r=0,t=0,b=0),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    fig.add_annotation(text=f"<b>{label}</b><br><span style='font-size:22px'>{value}</span>",
                       x=0.5, y=0.5, showarrow=False)
    return fig

def hbar(df, color):
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Sales"], y=df[df.columns[0]], orientation='h',
                         marker_color=color, text=df["Sales"], textposition="outside"))
    fig.update_layout(height=180, margin=dict(l=10,r=10,t=10,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(title=None))
    return fig

def line_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Month"], y=df["Sales"], mode="lines+markers", name="Sales", line=dict(width=3, color="#007AFF")))
    fig.update_layout(height=260, margin=dict(l=10,r=10,t=30,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    return fig

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="sb-item active">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">📦 Inventory</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">🤝 Suppliers</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">🧾 Orders</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item">💬 Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ MAIN CONTENT ------------------
st.markdown("<h1 style='font-weight:900; color:#26323a;'>Inventory Management Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Stock Overview
st.markdown("<h3>Stock Overview</h3>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.plotly_chart(donut(low_stock,len(products),"#f24b5b","Low Stock"),use_container_width=True,config={"displayModeBar":False})
    st.markdown(f"<div class='kpi-caption'>{low_stock} Items</div>", unsafe_allow_html=True)
with c2:
    st.plotly_chart(donut(reorder,len(products),"#f3b234","Reorder"),use_container_width=True,config={"displayModeBar":False})
    st.markdown(f"<div class='kpi-caption'>{reorder} Items</div>", unsafe_allow_html=True)
with c3:
    st.plotly_chart(donut(instock,len(products),"#24c285","In Stock"),use_container_width=True,config={"displayModeBar":False})
    st.markdown(f"<div class='kpi-caption'>{instock} Items</div>", unsafe_allow_html=True)

# Supplier & Sales
st.markdown("<h3>Supplier & Sales Data (Q3)</h3>", unsafe_allow_html=True)
cc1, cc2 = st.columns(2)
with cc1:
    st.markdown("**Top Suppliers (Q3)**")
    st.plotly_chart(hbar(suppliers_sum,"#007AFF"),use_container_width=True,config={"displayModeBar":False})
with cc2:
    st.markdown("**Sales by Category (Q3)**")
    st.plotly_chart(hbar(categories,"#F39C12"),use_container_width=True,config={"displayModeBar":False})

# Chat + Trend
col1, col2 = st.columns([1.05,1.9])
with col1:
    st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)
    user_query = st.text_input("Type your query:")
    if user_query:
        q = user_query.lower()
        response = ""
        if "sku" in q:
            sku = q.split("sku")[-1].strip()
            match = products[products['SKU'].astype(str).str.contains(sku, case=False, na=False)]
            if not match.empty:
                qty = int(match.iloc[0]['Quantity'])
                supplier = match.iloc[0]['Supplier_ID']
                response = f"SKU {sku} has {qty} units available from supplier {supplier}."
            else:
                response = "SKU not found in the product list."
        elif "low stock" in q:
            low_df = products[products['Quantity'] < products['MinStock']][['SKU', 'Name', 'Quantity']]
            if not low_df.empty:
                response = f"{len(low_df)} products have low stock."
                st.dataframe(low_df)
            else:
                response = "No products are currently low on stock."
        elif "supplier" in q:
            supplier_col = 'SupplierName' if 'SupplierName' in suppliers.columns else 'Supplier_ID'
            response = "Suppliers: " + ", ".join(suppliers[supplier_col].astype(str).tolist())
        elif "sales" in q:
            total_sales = sales['Total'].sum() if 'Total' in sales.columns else "N/A"
            response = f"Total recorded sales revenue: ${total_sales}"
        else:
            response = "Sorry, I didn’t understand that. Try asking about SKU, supplier, or stock."
        st.markdown(f'<div class="chat-box"><b>Bot:</b> {response}</div>', unsafe_allow_html=True)
with col2:
    st.markdown("<h3>Trend Performance</h3>", unsafe_allow_html=True)
    if not trend.empty:
        st.plotly_chart(line_chart(trend), use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("No trend data found in sales.csv.")
