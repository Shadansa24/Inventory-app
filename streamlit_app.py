# app.py
# Streamlit dashboard that visually matches the provided mockup (no QR/scan functionality)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ----------------------------- Page Config -----------------------------
st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")

# ----------------------------- CSS (theme + layout + cards) -----------------------------
CSS = """
/* App background (soft teal/blue gradient) */
[data-testid="stAppViewContainer"]{
  background: radial-gradient(1400px 800px at 50% -15%, #eaf4ff 0%, #d4e6ee 38%, #97b6c0 100%);
}

/* Reduce default top/bottom padding */
.block-container{
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

/* Sidebar styling to match mock */
.sidebar-wrap{
  background: rgba(255,255,255,.75);
  backdrop-filter: blur(3.5px);
  border-radius: 16px;
  box-shadow: 0 12px 24px rgba(0,0,0,.08);
  padding: 18px 14px;
}
.sb-item{
  display:flex; align-items:center; gap:.65rem;
  font-weight:600; color:#3b4a54; 
  background:#fff; border:1px solid #e8eef2;
  padding:.7rem .75rem; border-radius:12px; margin:.35rem 0;
  box-shadow: 0 3px 10px rgba(0,0,0,.04);
}
.sb-item .ico{width:22px;height:22px;display:flex;align-items:center;justify-content:center;
  color:#6a7c86}
.sb-item.active{background:#edf6ff;border-color:#d7e9ff;color:#1e6fd8}
.sb-title{font-size:.92rem}

/* Generic card (glass-like) */
.card{
  background:#ffffff;
  border:1px solid rgba(35,73,102,.08);
  border-radius:14px;
  box-shadow:0 12px 24px rgba(0,0,0,.08);
  padding:16px 16px 14px 16px;
}
.card h3{margin:.1rem 0 .8rem 0; font-size:1.05rem; font-weight:800; color:#2d3c45}

/* Small subcards (metrics) */
.subcard{
  background:#ffffff;
  border:1px solid rgba(35,73,102,.08);
  border-radius:14px;
  box-shadow:0 10px 18px rgba(0,0,0,.07);
  padding:12px 12px 6px 12px;
}

/* Mini text under donuts */
.kpi-caption{color:#7c8c98; font-size:.8rem}

/* "Barcode" (visual only) */
.barcode-box{
  height:160px; border-radius:12px; 
  background:#eef3f8; border:1px solid #e0e7ee;
  display:flex; justify-content:center; align-items:center; 
  position:relative;
  box-shadow: inset 0 2px 8px rgba(0,0,0,.05);
}
.barcode{
  height:90px; width:200px; background:
    repeating-linear-gradient(90deg,
      #0f1e2a 0, #0f1e2a 3px,
      transparent 3px, transparent 6px);
  border-radius:4px;
  box-shadow: 0 0 0 8px #fff, 0 0 0 9px #cfd9e1;
}
.scan-caption{
  position:absolute; bottom:8px; left:0; right:0; text-align:center;
  letter-spacing:.12rem; color:#7290a2; font-size:.72rem;
}

/* Detailed reports icons row */
.report-row{display:flex; gap:14px; align-items:center}
.rep{
  flex:1; text-align:center; background:#f5f9fc; border:1px solid #e3edf5; 
  border-radius:12px; padding:12px 8px;
}
.rep-ico{
  width:30px;height:30px;border-radius:8px; background:#eaf3ff; 
  display:inline-flex; align-items:center; justify-content:center; color:#2f7fe3;
  box-shadow: inset 0 -2px 0 rgba(0,0,0,.04);
  margin-bottom:6px;
}
.rep span{display:block; color:#607485; font-weight:600; font-size:.85rem}

/* Chat widget */
.chat-wrap{display:flex; gap:14px}
.chat-avatar{
  width:34px;height:34px;border-radius:50%; background:#e6f3ff; 
  display:flex; align-items:center; justify-content:center; color:#2b7de9;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
}
.chat-bubble{
  flex:1; background:#f6fbff; border:1px solid #ddebf6; border-radius:12px; 
  padding:10px 12px;
}
.chat-input{
  background:#ffffff; border:1px solid #e6edf3; border-radius:10px; padding:10px 12px; 
  color:#5c6d79
}

/* Section spacer bars (subtle rounded pill) */
.pill{
  background:#ffffff; border:1px solid rgba(35,73,102,.08);
  border-radius:999px; height:24px; box-shadow:0 6px 14px rgba(0,0,0,.06)
}

/* Tighten column vertical alignment */
[data-testid="stHorizontalBlock"]{align-items:stretch}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ----------------------------- Data (static to match mock) -----------------------------
# Stock KPIs
low_stock_val   = 47
reorder_val     = 120
instock_val     = 890

# Supplier & Sales bars (two blocks like image)
top_suppliers = pd.DataFrame({
    "label":["Acme Corp","Innovate Ltd","Global Goods"],
    "value":[38,28,18]
})
by_category = pd.DataFrame({
    "label":["Electronics","Apparel","Home Goods"],
    "value":[40,26,14]
})

# Trend chart
trend_df = pd.DataFrame({
    "Month":["Jan","Feb","Mar","Apr","May","Jun"],
    "Product A":[20,45,60,75,85,108],
    "Product B":[15,35,50,65,85,95]
})

# ----------------------------- Small helpers -----------------------------
def donut(value, total, color, label):
    """Donut gauge with central text."""
    fig = go.Figure()
    # colored part + remainder
    v = max(0, min(value, total))
    fig.add_trace(go.Pie(
        values=[v, total - v],
        hole=.7,
        sort=False,
        direction="clockwise",
        marker_colors=[color, "#edf2f6"],
        textinfo="none"
    ))
    fig.update_layout(
        width=210, height=150, margin=dict(l=0,r=0,b=0,t=6),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    # overlay annotation
    fig.add_annotation(text=f"<b style='font-size:20px'>{label}</b><br>"
                            f"<span style='font-size:28px'>{value}</span>",
                       x=.5,y=.5,showarrow=False)
    return fig

def hbar_block(df: pd.DataFrame, color="#4b7bec"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["value"], y=df["label"], orientation="h",
        marker=dict(color=color),
        text=df["value"], textposition="outside", insidetextanchor="start"
    ))
    fig.update_layout(
        height=160, margin=dict(l=10,r=10,t=6,b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(title=None, tickfont=dict(size=12)),
        bargap=.35
    )
    return fig

def line_block(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Month"], y=df["Product A"], mode="lines+markers",
                             name="Product A", line=dict(width=3)))
    fig.add_trace(go.Scatter(x=df["Month"], y=df["Product B"], mode="lines+markers",
                             name="Product B", line=dict(width=3)))
    fig.update_layout(
        height=260, margin=dict(l=10,r=10,t=20,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=dict(text="Top-Selling Products", x=.5, font=dict(size=14))
    )
    return fig

# ----------------------------- Layout -----------------------------
# Sidebar (non-interactive — visual like the mock)
with st.sidebar:
    st.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="sb-item active"><div class="ico">📊</div><div class="sb-title">Dashboard</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item"><div class="ico">📦</div><div class="sb-title">Inventory</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item"><div class="ico">🤝</div><div class="sb-title">Suppliers</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item"><div class="ico">🧾</div><div class="sb-title">Orders</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item"><div class="ico">⚙️</div><div class="sb-title">Settings</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-item"><div class="ico">💬</div><div class="sb-title">Chat Assistant</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Title row
st.markdown("<h1 style='font-weight:900; color:#26323a; margin-bottom:.35rem'>Inventory Management Dashboard</h1>", unsafe_allow_html=True)
st.markdown('<div class="pill"></div>', unsafe_allow_html=True)
st.markdown("<br/>", unsafe_allow_html=True)

# --- Row 1: Stock Overview + (visual) Barcode card ---
r1c1, r1c2, r1c3, r1c4 = st.columns([1.6,1.6,1.6,1.2], gap="large")

with r1c1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h3>Stock Overview</h3>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            st.plotly_chart(donut(low_stock_val, 150, "#f24b5b", "Low Stock"), use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"<div class='kpi-caption'>{low_stock_val} Items</div>", unsafe_allow_html=True)
        with c2:
            st.plotly_chart(donut(reorder_val, 150, "#f3b234", "Reorder"), use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"<div class='kpi-caption'>{reorder_val} Items</div>", unsafe_allow_html=True)
        with c3:
            st.plotly_chart(donut(instock_val, 1000, "#24c285", "In Stock"), use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"<div class='kpi-caption'>{instock_val} Items</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with r1c4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Barcode Scan</h3>", unsafe_allow_html=True)
    st.markdown('<div class="barcode-box"><div class="barcode"></div><div class="scan-caption">SCANNING…</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Spacer bar
st.markdown("<div class='pill' style='margin:14px 0 6px 0'></div>", unsafe_allow_html=True)

# --- Row 2: Supplier & Sales + Detailed Reports (right small card) ---
r2c1, r2c2, r2c3 = st.columns([1.55, 1.05, 1.05], gap="large")
with r2c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Supplier & Sales Data (Q3)</h3>", unsafe_allow_html=True)
    left,right = st.columns([1,1])
    with left:
        st.markdown("<b>Top Suppliers (Q3)</b>", unsafe_allow_html=True)
        st.plotly_chart(hbar_block(top_suppliers, "#4b7bec"), use_container_width=True, config={"displayModeBar":False})
    with right:
        st.markdown("<b>Sales by Category (Q3)</b>", unsafe_allow_html=True)
        st.plotly_chart(hbar_block(by_category, "#f5a623"), use_container_width=True, config={"displayModeBar":False})
        # legend to match mock
        st.markdown("""
        <div style="display:flex; gap:18px; color:#4f5f6a; font-size:.9rem">
            <div>▮ Acme Corp</div>
            <div>▮ Innovate Ltd</div>
            <div>▮ Global Goods</div>
            <div>▮ Apparel</div>
            <div>▮ Home Goods</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Detailed Reports</h3>", unsafe_allow_html=True)
    st.markdown('<div class="report-row">', unsafe_allow_html=True)
    st.markdown('<div class="rep"><div class="rep-ico">📦</div><span>Inventory</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="rep"><div class="rep-ico">📈</div><span>Movement</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="rep"><div class="rep-ico">📜</div><span>History</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Row 3: Chat Assistant (left small) + Trend Performance (right long) ---
r3c1, r3c2 = st.columns([1.05, 1.55], gap="large")

with r3c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Chat Assistant</h3>", unsafe_allow_html=True)
    st.markdown('<div class="chat-input">Type your query…</div>', unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="chat-avatar">🤖</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="chat-bubble">
            <div style="color:#6b7a86; font-size:.88rem">
                <b>User:</b> “Check stock for SKU 789”<br/>
                <b>Bot:</b> SKU: 150 units available.<br/>
                Supplier: Acme Corp.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r3c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Trend Performance</h3>", unsafe_allow_html=True)
    st.plotly_chart(line_block(trend_df), use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)
