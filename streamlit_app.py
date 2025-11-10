# streamlit_app.py — UI-Polished version
# Logic unchanged; cleaner spacing, alignment, and consistent card hierarchy

import os, re
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import openai
except Exception:
    openai = None

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

PRIMARY_COLOR = "#0077B6"
ACCENT_COLOR = "#1EA97C"
DARK_TEXT = "#1B4E4D"
MUTED_TEXT = "#4A7D7B"

BG_GRADIENT = """
linear-gradient(145deg,#F0F5F9 0%,#E3EAF0 50%,#D8E0E8 100%)
"""

CARD = """
background: rgba(255,255,255,0.98);
backdrop-filter: blur(8px);
border-radius: 18px;
padding: 22px 24px 18px 24px;
box-shadow: 0 10px 28px rgba(0, 0, 0, 0.07);
border: 1px solid rgba(240,240,240,0.55);
"""

TITLE = f"color:{DARK_TEXT}; font-weight:800; font-size:22px;"
LABEL = f"color:{MUTED_TEXT}; font-weight:600; font-size:13px; letter-spacing:.3px;"

st.markdown(f"""
<style>
.main {{ background: {BG_GRADIENT}; }}
.card {{ {CARD} }}
.small-muted {{ color:#718b89; font-size:12px; }}

.chip {{
    display:flex; align-items:center; gap:8px;
    padding:10px 14px; border-radius:12px;
    background:#E8F4F3; color:{MUTED_TEXT};
    font-weight:600; font-size:14px; cursor:pointer;
    transition: all .2s ease;
    margin-bottom:6px;
}}
.chip:hover {{ background:#D5EBEA; color:#005691; }}
.chip.active {{ background:#D5EBEA; color:{PRIMARY_COLOR}; border-left:4px solid {PRIMARY_COLOR}; padding-left:10px; }}

.modebar {{ visibility:hidden; }}
hr {{ margin:12px 0; border-color:#e3e9e7; }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADING (unchanged)
# =============================================================================
DATA_DIR = "data"

def read_csv_clean(p):
    try:
        df = pd.read_csv(p); df.columns = [c.strip() for c in df.columns]; return df
    except Exception:
        return None

products = read_csv_clean(os.path.join(DATA_DIR, "products.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))

# DEMO fallback
if products is None:
    products = pd.DataFrame({
        "Product_ID":[101,102,103,104,105],
        "SKU":["IPH-15","GS24","MB-Air-M3","LG-MSE","AP-PR2"],
        "Name":["iPhone 15","Galaxy S24","MacBook Air M3","Logitech Mouse","AirPods Pro"],
        "Category":["Mobile","Mobile","Laptop","Accessory","Accessory"],
        "Quantity":[12,30,5,3,20],
        "MinStock":[15,10,8,5,10],
        "UnitPrice":[999,899,1299,29,249],
        "Supplier_ID":["ACME","GX","ACME","ACC","ACME"]
    })

if suppliers is None:
    suppliers = pd.DataFrame({
        "Supplier_ID":["ACME","GX","ACC"],
        "Supplier_Name":["ACME Distribution","GX Mobile","Accessory House"],
        "Email":["orders@acme.com","gx@mobile.com","hello@acc.com"],
        "Phone":["+1-555-0100","+1-555-0111","+1-555-0122"]
    })

if sales is None:
    sales = pd.DataFrame({
        "Sale_ID":["S-1001","S-1002","S-1003","S-1004"],
        "Product_ID":[104,101,105,102],
        "Qty":[2,1,3,5],
        "UnitPrice":[29,999,249,899],
        "Timestamp":["2025-01-10","2025-02-01","2025-02-15","2025-03-12"]
    })

# =============================================================================
# DATA CALCS (unchanged)
# =============================================================================
for df in (products, sales, suppliers): df.columns = [c.strip() for c in df.columns]
sales.rename(columns={"ProductId":"Product_ID","product_id":"Product_ID","Units":"Qty"}, inplace=True)
products["StockValue"] = products["Quantity"] * products["UnitPrice"]

low_stock_count = int((products["Quantity"] < products["MinStock"]).sum())
low_stock_total = int(products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum())
reorder_total = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_total = int(products["Quantity"].sum())

supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

sales_ext = sales.merge(products[["Product_ID","Name","Category","SKU"]], on="Product_ID", how="left")
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum().sort_values("Qty", ascending=False)
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"], errors="coerce").dt.to_period("M").astype(str)

# =============================================================================
# HELPER — unchanged
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b><br><span style='font-size:14px; color:{MUTED_TEXT};'>{subtitle}</span>"},
        gauge={"axis":{"range":[0,max_value or 1],"tickwidth":0},
               "bar":{"color":color,"thickness":0.5},
               "bgcolor":"rgba(0,0,0,0)","steps":[{"range":[0,max_value],"color":"rgba(47,94,89,0.05)"}]},
        number={"font":{"size":32,"color":DARK_TEXT}}
    ))
    fig.update_layout(margin=dict(l=4,r=4,t=38,b=4),paper_bgcolor="rgba(0,0,0,0)")
    return fig

# =============================================================================
# LAYOUT
# =============================================================================

# ---- TOP ROW
top = st.columns([0.9,2.0,1.4], gap="large")

with top[0]:
    st.markdown(f"""
    <div class="card" style="height:255px;">
        <div style="{TITLE};font-size:18px;margin-bottom:12px;">Navigation</div>
        <div style="display:flex;flex-direction:column;">
            <div class='chip active'>📊 Dashboard</div>
            <div class='chip'>📦 Inventory</div>
            <div class='chip'>🚚 Suppliers</div>
            <div class='chip'>🛒 Orders</div>
            <div class='chip'>⚙️ Settings</div>
            <hr/>
            <div class='chip'>💬 Chat Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top[1]:
    st.markdown(f"<div class='card'><div style='{TITLE};font-size:20px;margin-bottom:8px;'>Stock Overview</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    m = max(in_stock_total, reorder_total, low_stock_total, 1)
    cols[0].plotly_chart(gauge("Low Stock", low_stock_total, f"{low_stock_count} items", "#E74C3C", m), use_container_width=True, config={"displayModeBar":False})
    cols[1].plotly_chart(gauge("Reorder", reorder_total, f"{reorder_total} items", "#F39C12", m), use_container_width=True, config={"displayModeBar":False})
    cols[2].plotly_chart(gauge("In Stock", in_stock_total, f"{in_stock_total} items", ACCENT_COLOR, m), use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

with top[2]:
    total_val = products["StockValue"].sum()
    st.markdown(f"""
    <div class="card" style="height:255px;display:flex;align-items:center;justify-content:center;">
        <div style="text-align:center;">
            <div style="{LABEL}">Quick Stats</div>
            <div style="font-size:32px;color:{DARK_TEXT};font-weight:800;">{products['SKU'].nunique()} SKUs</div>
            <div class="small-muted">Total Stock Value: <b>${total_val:,.0f}</b></div>
            <hr/>
            <div style="{LABEL}">Supplier Base</div>
            <div style="font-size:24px;color:{DARK_TEXT};font-weight:700;">{len(suppliers)} Active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---- MIDDLE
mid = st.columns([2.0,1.3], gap="large")
with mid[0]:
    st.markdown(f"<div class='card'><div style='{TITLE};font-size:18px;'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    c = st.columns(2)
    fig1 = px.bar(supplier_totals.head(4), x="StockValue", y="Supplier_Name", orientation="h", text="StockValue", color_discrete_sequence=[PRIMARY_COLOR])
    fig1.update_traces(texttemplate="$%{text:,}", textposition="outside", marker_opacity=0.85)
    fig1.update_layout(margin=dict(l=0,r=6,t=4,b=6),paper_bgcolor="rgba(0,0,0,0)",xaxis_visible=False,yaxis_title=None)
    c[0].plotly_chart(fig1,use_container_width=True,config={"displayModeBar":False})

    fig2 = px.bar(sales_by_cat, x="Category", y="Qty", text="Qty", color_discrete_sequence=[ACCENT_COLOR])
    fig2.update_traces(textposition="outside", marker_opacity=0.85)
    fig2.update_layout(margin=dict(l=6,r=6,t=4,b=6),paper_bgcolor="rgba(0,0,0,0)",xaxis_title=None,yaxis_title=None)
    c[1].plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with mid[1]:
    st.markdown(f"""
    <div class="card">
        <div style="{TITLE};font-size:18px;">Data Snapshots</div>
        <div class="small-muted">Updated {datetime.now().strftime('%b %d, %Y - %H:%M')}</div>
        <hr/>
        <ul style="padding-left:18px;line-height:1.6;color:{DARK_TEXT};font-size:14px;">
            <li><b>{low_stock_count}</b> products below min stock</li>
            <li><b>{len(suppliers)}</b> active suppliers</li>
            <li><b>{int(sales_ext['Qty'].sum()):,}</b> units sold YTD</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ---- BOTTOM
bottom = st.columns([1.1,2.3], gap="large")
with bottom[0]:
    st.markdown(f"""
    <div class="card" style="height:350px;">
        <div style="{TITLE};font-size:18px;">Chat Assistant</div>
        <div class="small-muted">Ask about stock, sales, suppliers.</div>
        <hr/>
        <div style="height:150px;overflow-y:auto;border-radius:10px;padding:10px;background:#f9fbfc;border:1px solid #eef1f5;margin-bottom:10px;">
            <p style="font-size:12px;color:#555;text-align:right;margin-bottom:5px;">User: Highest stock value supplier?</p>
            <p style="font-size:12px;color:{DARK_TEXT};background:#E8F4F3;padding:5px 8px;border-radius:8px;display:inline-block;">
                Bot: ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.text_input("Type your question here:", placeholder="Enter your query...")

with bottom[1]:
    st.markdown(f"<div class='card'><div style='{TITLE};font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    df = sales_ext.groupby(["Month","Name"],as_index=False)["Qty"].sum()
    months = sorted(df["Month"].unique(), key=lambda x: pd.to_datetime(x))
    fig = go.Figure()
    colors = ["#0077B6","#FF9500","#1EA97C","#E74C3C"]
    for i,label in enumerate(df["Name"].unique()):
        sub=df[df["Name"]==label].set_index("Month").reindex(months).fillna(0)
        fig.add_trace(go.Scatter(x=months,y=sub["Qty"],mode="lines+markers",name=label,
                                 line=dict(color=colors[i%len(colors)],width=3)))
    fig.update_layout(margin=dict(l=6,r=6,t=8,b=6),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=DARK_TEXT))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)
