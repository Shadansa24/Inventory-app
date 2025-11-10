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

# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    suppliers = pd.read_csv("data/suppliers.csv")
    sales = pd.read_csv("data/sales.csv")

    # Fix sales dataset
    if "Qty" in sales.columns and "UnitPrice" in sales.columns:
        sales["Revenue"] = sales["Qty"] * sales["UnitPrice"]
    if "Timestamp" in sales.columns:
        sales["Month"] = pd.to_datetime(sales["Timestamp"]).dt.strftime("%Y-%m")

    # Merge supplier names for summary
    merged = pd.merge(products, suppliers, on="Supplier_ID", how="left")
    return products, suppliers, sales, merged

try:
    products, suppliers, sales, merged = load_data()
except FileNotFoundError as e:
    st.error(f"⚠️ Missing data file: {e.filename}. Ensure products.csv, suppliers.csv, and sales.csv are inside /data.")
    st.stop()

# ------------------ KPI CALCULATIONS ------------------
low_stock = (products['Quantity'] < products['MinStock']).sum()
reorder = ((products['Quantity'] >= products['MinStock']) & (products['Quantity'] < products['MinStock'] * 2)).sum()
instock = (products['Quantity'] >= products['MinStock'] * 2).sum()

# Supplier summary
suppliers_sum = (
    merged.groupby("Supplier_Name")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Sales"})
    if "Supplier_Name" in merged.columns else pd.DataFrame({"Supplier_Name": [], "Sales": []})
)

# Category summary
if "Category" in products.columns:
    categories = products.groupby("Category")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Sales"})
else:
    categories = pd.DataFrame({"Category": [], "Sales": []})

# Trend summary
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
    y_col = "Sales" if "Sales" in df.columns else "Revenue"
    if "Month" in df.columns and y_col in df.columns:
        fig.add_trace(go.Scatter(x=df["Month"], y=df[y_col],
                                 mode="lines+markers", name=y_col,
                                 line=dict(width=3, color="#007AFF")))
    fig.update_layout(height=260, margin=dict(l=10,r=10,t=30,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    return fig

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📦 Inventory", "🤝 Suppliers", "🧾 Orders", "⚙️ Settings", "💬 Chat Assistant"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ MAIN CONTENT ------------------
st.markdown("<h1 style='font-weight:900; color:#26323a;'>Inventory Management Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ------------------ PAGES ------------------
if page == "📊 Dashboard":
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

    # Trend
    st.markdown("<h3>Trend Performance</h3>", unsafe_allow_html=True)
    if not trend.empty:
        st.plotly_chart(line_chart(trend), use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("No trend data found in sales.csv.")

elif page == "📦 Inventory":
    st.markdown("### Inventory Overview")
    st.dataframe(products)

elif page == "🤝 Suppliers":
    st.markdown("### Supplier List")
    st.dataframe(suppliers)

elif page == "🧾 Orders":
    st.markdown("### Sales Orders")
    st.dataframe(sales)

elif page == "⚙️ Settings":
    st.info("Settings page under development.")

elif page == "💬 Chat Assistant":
    st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)
    user_query = st.text_input("Type your query:")
    if user_query:
        q = user_query.lower().strip()
        response = ""

        # Product ID or SKU lookup
        if any(word in q for word in ["id", "sku", "product"]):
            term = q.replace("what is the id for", "").replace("sku", "").strip()
            match = products[products["Name"].str.lower().str.contains(term, na=False)]
            if not match.empty:
                pid = match.iloc[0]["Product_ID"]
                sku = match.iloc[0]["SKU"]
                response = f"Product '{match.iloc[0]['Name']}' → Product ID: {pid}, SKU: {sku}."
            else:
                response = f"No product found matching '{term}'."

        elif "low stock" in q or "low" in q:
            low_df = products[products['Quantity'] < products['MinStock']][['SKU', 'Name', 'Quantity']]
            if not low_df.empty:
                response = f"{len(low_df)} products are below minimum stock."
                st.dataframe(low_df)
            else:
                response = "All products are above their minimum stock levels."

        elif "supplier" in q:
            supplier_col = "Supplier_Name" if "Supplier_Name" in suppliers.columns else "Supplier_ID"
            response = "Suppliers: " + ", ".join(suppliers[supplier_col].astype(str).tolist())

        elif "sales" in q or "revenue" in q:
            total_sales = sales["Revenue"].sum() if "Revenue" in sales.columns else "N/A"
            response = f"Total recorded sales revenue: ${total_sales:,.2f}"

        else:
            response = "Sorry, I didn’t understand that. Try asking about a product, SKU, or supplier."

        st.markdown(f'<div class="chat-box"><b>Bot:</b> {response}</div>', unsafe_allow_html=True)
