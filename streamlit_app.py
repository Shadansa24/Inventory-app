# -*- coding: utf-8 -*-
"""
Inventory Manager — Dashboard UI clone (no QR/scanner)
- Sidebar navigation with icons
- EXACT card-style dashboard layout
- Uses your CSV schema: products.csv, suppliers.csv, sales.csv
"""

import os, re, datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Optional fuzzy search for chat
try:
    from rapidfuzz import process, fuzz
    RAPID = True
except Exception:
    RAPID = False

# Optional AgGrid
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID = True
except Exception:
    AGGRID = False

# ------------------------------------------------------------------
# Streamlit Config
# ------------------------------------------------------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# ------------------------------------------------------------------
# CSS Styling
# ------------------------------------------------------------------
CSS = """
<style>
:root{
  --bg: linear-gradient(180deg,#7aa0a8 0%, #5c7a86 55%, #4c6572 100%);
  --card:rgba(255,255,255,.68);
  --border:rgba(255,255,255,.55);
  --ring-red:#ea5455; --ring-amber:#f19f38; --ring-green:#34c38f;
}
html, body, [data-testid="stAppViewContainer"]{ background: var(--bg); }
.block-container{ padding-top: .6rem; }
.glass{ background: var(--card); border:1px solid var(--border); border-radius:16px; box-shadow:0 8px 28px rgba(0,0,0,.18); backdrop-filter: blur(8px); }
.sb{ background:rgba(255,255,255,.35); border-radius:16px; box-shadow:0 6px 20px rgba(0,0,0,.15); padding:14px; }
.sb-item{ display:flex; align-items:center; gap:.6rem; padding:.55rem .6rem; margin:.18rem 0; border-radius:12px; font-weight:600; color:#234; }
.sb-item:hover{ background:rgba(255,255,255,.55); }
.sb-active{ background:white; }
.card{ padding:14px; }
.sub{ color:#66778a; font-size:.82rem; }
.chart{ padding:4px 8px 0 0; }
.chat-box{ padding:12px; display:flex; flex-direction:column; gap:.6rem; }
.chat-msg{ background:rgba(255,255,255,.7); padding:.55rem .7rem; border-radius:10px; border:1px solid #dfe7ee; }
.footer-note{ color:#29414f; font-size:.8rem; margin-top:.25rem }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Data IO
# ------------------------------------------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV = os.path.join(DATA_DIR, "sales.csv")

def load(path, cols):
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df[cols]

def save(df, path):
    df.to_csv(path, index=False)

# Load datasets
P = load(P_CSV, ["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"])
S = load(S_CSV, ["Supplier_ID","Supplier_Name","Email","Phone"])
T = load(T_CSV, ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"])

# Sanitize numeric types
for col in ["Quantity","MinStock"]:
    P[col] = pd.to_numeric(P[col], errors="coerce").fillna(0).astype(int)
P["UnitPrice"] = pd.to_numeric(P["UnitPrice"], errors="coerce").fillna(0.0)

if len(T):
    T["Qty"] = pd.to_numeric(T["Qty"], errors="coerce").fillna(0).astype(int)
    T["UnitPrice"] = pd.to_numeric(T["UnitPrice"], errors="coerce").fillna(0.0)
    T["Timestamp"] = pd.to_datetime(T["Timestamp"], errors="coerce").fillna(pd.Timestamp.utcnow())

P["Status"] = np.where(P["Quantity"] < P["MinStock"], "Low", "OK")
LOW = P[P["Status"]=="Low"]
REORDER = P[P["Quantity"]<=P["MinStock"]]
IN_STOCK = P[P["Quantity"]>0]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def pie_gauge(value, total, title, color, suffix=" Items"):
    val = int(value)
    tot = int(total) if total else max(1, int(value))
    remain = max(tot - val, 0)
    fig = go.Figure(data=[go.Pie(values=[val, remain], hole=0.7,
                                 marker_colors=[color, "rgba(0,0,0,0)"],
                                 textinfo="none", sort=False)])
    fig.update_layout(showlegend=False, height=220, margin=dict(l=0,r=0,t=10,b=10),
                      paper_bgcolor="rgba(0,0,0,0)",
                      annotations=[dict(text=f"<b>{val}</b><br><span style='font-size:12px;color:#6b7f8e'>{suffix}</span>",
                                        x=0.5,y=0.5,showarrow=False)])
    return fig

def plotly_light(fig, h=260):
    fig.update_layout(template="plotly_white", height=h,
                      margin=dict(l=10,r=10,t=28,b=10),
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e6eef3")
    return fig

def assistant_answer(q: str) -> dict:
    ql = q.strip().lower()
    if not ql:
        return {"text":"Type a query like: stock of USB hub, supplier of Mouse, low stock, sales for Printer."}
    if any(k in ql for k in ["low stock","reorder","below min"]):
        rows = LOW[["Product_ID","SKU","Name","Quantity","MinStock","Supplier_ID"]]
        return {"text": f"{len(rows)} low-stock items." if not rows.empty else "No low-stock items.", "table": rows}
    return {"text":"Try: stock of <name>, supplier of <name>, id of <name>, low stock."}

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Settings"]
with st.sidebar:
    st.markdown('<div class="sb">', unsafe_allow_html=True)
    tab = st.radio("Navigation", tabs, index=0, label_visibility="collapsed")
    for t in tabs:
        active = "sb-item sb-active" if t==tab else "sb-item"
        st.markdown(f'<div class="{active}">{t}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Dashboard Page
# ------------------------------------------------------------------
if tab == "Dashboard":
    c_left, c_right = st.columns([2.1, 1.1])

    # Stock Overview
    with c_left:
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Stock Overview</h4>", unsafe_allow_html=True)
        g1,g2,g3 = st.columns(3)
        with g1:
            st.plotly_chart(pie_gauge(len(LOW), len(P), "Low Stock", "var(--ring-red)"), use_container_width=True)
            st.markdown(f"<div class='sub'>Low Stock<br><b>{len(LOW)}</b> Items</div>", unsafe_allow_html=True)
        with g2:
            st.plotly_chart(pie_gauge(len(REORDER), len(P), "Reorder", "var(--ring-amber)"), use_container_width=True)
            st.markdown(f"<div class='sub'>Reorder<br><b>{len(REORDER)}</b> Items</div>", unsafe_allow_html=True)
        with g3:
            st.plotly_chart(pie_gauge(len(IN_STOCK), len(P), "In Stock", "var(--ring-green)"), use_container_width=True)
            st.markdown(f"<div class='sub'>In Stock<br><b>{len(IN_STOCK)}</b> Items</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Supplier & Sales Data
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Supplier & Sales Data</h4>", unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            if len(S) and len(P):
                top_sup = P.groupby("Supplier_ID").agg(Items=("Product_ID","count")).reset_index()
                top_sup = top_sup.merge(S[["Supplier_ID","Supplier_Name"]], on="Supplier_ID", how="left").sort_values("Items", ascending=False).head(5)
                fig = px.bar(top_sup, x="Items", y="Supplier_Name", orientation="h", text="Items")
                plotly_light(fig, 220)
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("No supplier data.")
        with s2:
            if len(T):
                t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]
                df = t.merge(P[["Product_ID","Category"]], on="Product_ID", how="left")
                cat = df.groupby("Category").agg(Revenue=("Revenue","sum")).reset_index()
                fig = px.bar(cat, x="Revenue", y="Category", orientation="h", text_auto=".2s")
                plotly_light(fig, 220)
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("No sales yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Right column: Reports quick links
    with c_right:
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Detailed Reports</h4>", unsafe_allow_html=True)
        st.button("Inventory History", use_container_width=True)
        st.button("Movement History", use_container_width=True)
        st.button("Top Performing Products", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Row 2: Chat + Trend
    r2_left, r2_right = st.columns([1.05, 2.05])
    with r2_left:
        st.markdown('<div class="glass card chat-box">', unsafe_allow_html=True)
        st.markdown("<h4>Chat Assistant</h4>", unsafe_allow_html=True)
        q = st.text_input("Type your query…", key="dash_chat")
        if q:
            ans = assistant_answer(q)
            st.markdown(f"<div class='chat-msg'><b>Bot</b>: {ans['text']}</div>", unsafe_allow_html=True)
            if isinstance(ans.get("table"), pd.DataFrame) and len(ans["table"]):
                st.dataframe(ans["table"], use_container_width=True, height=220)
        else:
            st.markdown("<div class='chat-msg'>User: 'Check stock for SKU 789'<br>Bot: 'SKU 789 – 150 units available. Supplier: Acme Corp.'</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2_right:
        st.markdown('<div class="glass card chart">', unsafe_allow_html=True)
        st.markdown("<h4>Trend Performance</h4>", unsafe_allow_html=True)
        if len(T):
            t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
            top = t.groupby("Product_ID")["Qty"].sum().sort_values(ascending=False).head(3).index.tolist()
            t = t[t["Product_ID"].isin(top)].merge(P[["Product_ID","Name"]], on="Product_ID", how="left")
            fig = px.line(t, x="Month", y="Qty", color="Name", markers=True)
            plotly_light(fig, 260)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Inventory
# ------------------------------------------------------------------
elif tab == "Inventory":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Inventory", unsafe_allow_html=True)
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(P)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True)
        grid = AgGrid(P, gridOptions=gb.build(), theme="balham", height=520,
                      update_mode=GridUpdateMode.VALUE_CHANGED, key="inv_grid")
        if st.button("💾 Save Changes", use_container_width=True):
            save(pd.DataFrame(grid["data"]), P_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(P, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save", use_container_width=True): save(ed, P_CSV); st.success("Saved.")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Suppliers
# ------------------------------------------------------------------
elif tab == "Suppliers":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Suppliers", unsafe_allow_html=True)
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(S)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True)
        grid = AgGrid(S, gridOptions=gb.build(), theme="balham", height=520,
                      update_mode=GridUpdateMode.VALUE_CHANGED, key="sup_grid")
        if st.button("💾 Save", use_container_width=True): save(pd.DataFrame(grid["data"]), S_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(S, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save"): save(ed, S_CSV); st.success("Saved.")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Sales
# ------------------------------------------------------------------
elif tab == "Sales":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Record Sale", unsafe_allow_html=True)
    if len(P)==0:
        st.info("Add products first.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        with c1: product = st.selectbox("Product", options=P["Name"])
        with c2: qty = st.number_input("Qty", 1, step=1)
        with c3: price = st.number_input("UnitPrice ($)", 0.0, step=0.01, value=float(P.loc[P["Name"]==product,"UnitPrice"].values[0]))
        with c4: date = st.date_input("Date", dt.date.today())

        if st.button("Add sale 🧾", use_container_width=True):
            global T, P
            pid = P.loc[P["Name"]==product, "Product_ID"].values[0]
            sid = f"S{int(pd.Timestamp.utcnow().timestamp())}"
            if "T" not in globals() or T is None or len(T)==0:
                T = pd.DataFrame(columns=["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"])
            T.loc[len(T)] = [sid, pid, int(qty), float(price), pd.to_datetime(date)]
            idx = P.index[P["Product_ID"]==pid]
            if len(idx): P.loc[idx, "Quantity"] = (P.loc[idx, "Quantity"] - int(qty)).clip(lower=0)
            save(T, T_CSV); save(P, P_CSV)
            st.success("Recorded.")

    st.markdown("#### Recent Sales", unsafe_allow_html=True)
    if len(T): st.dataframe(T.sort_values("Timestamp", ascending=False).head(300), use_container_width=True, height=420)
    else: st.info("No sales yet.")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Reports
# ------------------------------------------------------------------
elif tab == "Reports":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Reports", unsafe_allow_html=True)
    if len(P):
        v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum")).reset_index()
        fig = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        st.plotly_chart(plotly_light(fig, 320), use_container_width=True)
    if len(T):
        t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        st.plotly_chart(plotly_light(fig2, 320), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
elif tab == "Settings":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Data", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download products.csv", P.to_csv(index=False).encode(), "products.csv", "text/csv", use_container_width=True)
    with c2:
        up = st.file_uploader("Upload products.csv", type=["csv"])
    with c3:
        if up is not None:
            try:
                df = pd.read_csv(up); save(df, P_CSV); st.success("Uploaded.")
            except Exception as e:
                st.error(f"Failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
