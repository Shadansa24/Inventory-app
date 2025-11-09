import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# -------------------- Page setup --------------------
st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")

CSS = """
<style>
:root{
  --bg1:#dfedf1;
  --bg2:#a8c4cc;
  --panel:#ffffff;
  --muted:#6a7d88;
  --text:#23313a;
  --accent:#3aaed8;
  --green:#39c27d;
  --amber:#f2b62b;
  --red:#e45b5b;
  --shadow:0 10px 24px rgba(40,68,80,.18);
  --radius:16px;
}
html, body, [data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 800px at 10% -5%, var(--bg1) 0%, var(--bg2) 65%);
  color: var(--text);
}
.block-container{padding-top: 1.2rem; padding-bottom:1.2rem; max-width: 1200px;}
.card{
  background: var(--panel);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid rgba(20,40,50,.06);
  padding: 16px 16px;
}
.card-tight{ padding: 12px 14px; }
.kicker{ color: var(--muted); font-size:.9rem; margin-bottom:6px; }
.h{
  font-weight: 800; letter-spacing:.2px; color: var(--text); margin:2px 0 10px 0;
}
.h1{ font-size:1.15rem; }
.h2{ font-size:1.05rem; }
.small{ font-size:.84rem; color:var(--muted); }
.row{ display:grid; gap:16px; }
.grid-2{ grid-template-columns: 2.2fr 1fr; }
.grid-3{ grid-template-columns: 1fr 1fr 1fr; }
.grid-4{ grid-template-columns: 1fr 1fr 1fr 1fr; }
.pill{ display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .6rem; border-radius:999px; background:#eef5f7; color:#40525c; font-weight:700; font-size:.85rem; }
.badge{ display:inline-flex; align-items:center; gap:.35rem; padding:.18rem .55rem; border-radius:999px; font-size:.78rem; font-weight:700;}
.badge-red{ background: #fdecec; color:#b23a3a; }
.badge-amber{ background: #fff3de; color:#b17c00; }
.badge-green{ background: #e8f8f0; color:#0f8e53; }

.menu{
  position: sticky; top: 12px;
  display:flex; flex-direction:column; gap:12px;
}
.menu .item{
  display:flex; gap:10px; align-items:center;
  background: var(--panel); border-radius: 14px; padding:12px 14px;
  color: var(--text); border:1px solid rgba(20,40,50,.06); box-shadow: var(--shadow);
}
.menu .item .ico{ width:24px; text-align:center; opacity:.75 }
.menu .item-active{ outline:2px solid rgba(58,174,216,.35) }
.code-slot{
  background:linear-gradient(180deg,#fff,#f3f7f9);
  border:1px dashed #cddbe2; border-radius:12px; text-align:center; padding:12px 10px; color:#6a7d88;
}
.barcode-box{
  border-radius: 14px; padding: 12px 12px; background: #f6fbfe; border:1px solid #d6e7ef;
}
.barcode-img{
  background:#fff; border:1px solid #dfe9ee; border-radius:8px; padding:8px 10px; display:inline-block;
  box-shadow: inset 0 0 0 1px #eef4f7;
}
input, textarea{ border-radius: 10px !important; }
.footer-note{ color:#7c8f99; font-size:.8rem; margin-top:6px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -------------------- Sample data (replace with your own data pipelines) --------------------
np.random.seed(7)
months = ["Jan","Feb","Mar","Apr","May","Jun"]
trend_df = pd.DataFrame({
    "Month": months,
    "Top-Selling A": np.random.randint(60,160,size=len(months)),
    "Top-Selling B": np.random.randint(40,140,size=len(months)),
    "Top-Selling C": np.random.randint(50,150,size=len(months)),
})
suppliers_df = pd.DataFrame({
    "Supplier": ["Acme Corp","Innovate Ltd","Global Goods","Apparel","Home Goods"],
    "Score":    [92,86,80,74,68],
})
sales_by_cat = pd.DataFrame({
    "Category":["Electronics","Apparel","Home Goods"],
    "Sales":[145,92,78]
})

# -------------------- Helpers --------------------
def gauge(value, title, color, suffix=" Items", max_val=900):
    # Plotly semi gauge (donut style)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': "", 'font': {'size': 26, 'color':'#263640'}},
        title={'text': title, 'font': {'size': 14, 'color': '#5c6a73'}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': color, 'thickness': 0.28},
            'bgcolor': "#f3f7f9",
            'bordercolor': "#e2edf2",
            'borderwidth': 1,
            'steps': [{'range': [0,max_val], 'color': '#eef5f7'}],
        },
        domain={'x':[0,1],'y':[0,1]}
    ))
    fig.update_layout(height=180, margin=dict(l=8,r=8,t=24,b=0), paper_bgcolor="rgba(0,0,0,0)")
    # add subtitle (value with suffix)
    fig.add_annotation(text=f"<b>{value}</b> <span style='color:#6a7d88'>{suffix}</span>",
                       showarrow=False, y=0.08, x=0.5, xanchor="center", yanchor="bottom",
                       font=dict(size=13, color="#263640"))
    return fig

def mini_bar(df, x, y, title=""):
    fig = px.bar(df, x=x, y=y, orientation="h",
                 color_discrete_sequence=["#3aaed8"])
    fig.update_layout(height=168, margin=dict(l=8,r=8,t=30,b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      title=title, title_font=dict(size=14,color="#52636c"),
                      xaxis=dict(visible=False), yaxis=dict(title=None, tickfont=dict(color="#50606a")))
    return fig

def line_trend(df):
    fig = go.Figure()
    for col, colr in zip(df.columns[1:], ["#3aaed8","#ff9c40","#7ec77b"]):
        fig.add_trace(go.Scatter(x=df["Month"], y=df[col],
                                 mode="lines+markers", name=col,
                                 line=dict(width=2.5, color=colr)))
    fig.update_layout(height=240, legend=dict(orientation="h", y=1.15, font=dict(size=11,color="#5c6a73")),
                      margin=dict(l=12,r=12,t=24,b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor="#e8eff2", tickfont=dict(color="#51616a")),
                      yaxis=dict(gridcolor="#e8eff2", tickfont=dict(color="#51616a")))
    return fig

# -------------------- Layout --------------------
left, right = st.columns([1,3], gap="large")

# ----- Left menu -----
with left:
    st.markdown("<div class='menu'>", unsafe_allow_html=True)
    st.markdown("<div class='item item-active'><span class='ico'>📊</span> Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='item'><span class='ico'>📦</span> Inventory</div>", unsafe_allow_html=True)
    st.markdown("<div class='item'><span class='ico'>🤝</span> Suppliers</div>", unsafe_allow_html=True)
    st.markdown("<div class='item'><span class='ico'>🧾</span> Orders</div>", unsafe_allow_html=True)
    st.markdown("<div class='item'><span class='ico'>⚙️</span> Settings</div>", unsafe_allow_html=True)
    st.markdown("<div class='item'><span class='ico'>💬</span> Chat Assistant</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----- Main canvas -----
with right:

    # Top row: Stock Overview (3 gauges) + Barcode Scan
    st.markdown("<div class='row grid-2'>", unsafe_allow_html=True)

    # --- Stock Overview card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Stock Overview</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(gauge(47, "Low Stock", "#e45b5b", suffix=" Items", max_val=150), use_container_width=True)
        st.markdown("<div class='badge badge-red'>47 Items</div>", unsafe_allow_html=True)
    with c2:
        st.plotly_chart(gauge(120, "Reorder", "#f2b62b", suffix=" Items", max_val=150), use_container_width=True)
        st.markdown("<div class='badge badge-amber'>120 Items</div>", unsafe_allow_html=True)
    with c3:
        st.plotly_chart(gauge(890, "In Stock", "#39c27d", suffix=" Items", max_val=900), use_container_width=True)
        st.markdown("<div class='badge badge-green'>890 Items</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # /card

    # --- Barcode Scan card
    st.markdown("<div class='card card-tight'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Barcode Scan</div>", unsafe_allow_html=True)
    st.markdown("<div class='barcode-box'>", unsafe_allow_html=True)
    scan_input = st.text_input(" ", value="", placeholder="Enter / scan barcode here", label_visibility="collapsed")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='barcode-img'>▌▌▍▍▌▍▌▌▍▍▌▍▍▌▍▌▍▌▍▍▌▌</div>", unsafe_allow_html=True)
    st.markdown("<div class='footer-note'>SCANNING…</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # /barcode-box
    st.markdown("</div>", unsafe_allow_html=True)  # /card

    st.markdown("</div>", unsafe_allow_html=True)  # /row grid-2

    # Middle row: Supplier & Sales Data (bars) + Detailed Reports icons
    st.markdown("<div class='row grid-2' style='margin-top:16px;'>", unsafe_allow_html=True)

    # --- Supplier & Sales Data card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    sub_left, sub_right = st.columns([1.1,1])
    with sub_left:
        st.plotly_chart(mini_bar(suppliers_df, x="Score", y="Supplier", title="Top Suppliers (Q3)"),
                        use_container_width=True)
        st.plotly_chart(mini_bar(pd.DataFrame({"Item":["Electronics"],"Val":[1]}),
                                 x="Val", y="Item", title="Electronics"), use_container_width=True)
    with sub_right:
        fig = px.bar(sales_by_cat, x="Category", y="Sales", text="Sales",
                     color="Category", color_discrete_sequence=["#3aaed8","#ff9c40","#7ec77b"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=200, margin=dict(l=8,r=8,t=30,b=8),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          title="Sales by Category (Q3)", title_font=dict(size=14,color="#52636c"),
                          xaxis=dict(title=None, tickfont=dict(color="#50606a")),
                          yaxis=dict(title=None, visible=False))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)  # /card

    # --- Detailed Reports card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Detailed Reports</div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    r1.button("📈 Inventory", use_container_width=True)
    r2.button("📦 Movement History", use_container_width=True)
    r3.button("🧾 Orders", use_container_width=True)
    r4.button("📤 Exports", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)  # /card

    st.markdown("</div>", unsafe_allow_html=True)  # /row grid-2

    # Bottom row: Chat Assistant + Trend Performance
    st.markdown("<div class='row grid-2' style='margin-top:16px;'>", unsafe_allow_html=True)

    # --- Chat Assistant card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Chat Assistant</div>", unsafe_allow_html=True)
    q = st.text_input("Type your query…", value="", label_visibility="collapsed",
                      placeholder="Type your query…")
    st.markdown("<div class='code-slot small'>User: “Check stock for SKU 789”<br/>Bot: “SKU: 150 units available.”<br/>Supplier: Acme Corp.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Trend Performance card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Trend Performance</div>", unsafe_allow_html=True)
    st.plotly_chart(line_trend(trend_df), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # /row grid-2
