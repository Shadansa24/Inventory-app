# -*- coding: utf-8 -*-
"""
Inventory Manager — Dashboard UI clone (no QR/scanner)
- Sidebar navigation with icons
- EXACT card-style dashboard: gauges, supplier & sales bars, trend line, reports shortcuts, chat assistant
- Keeps Inventory / Suppliers / Sales / Reports / Settings tabs
- Uses your CSV schema in ./data
"""
import os, re, datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Optional (nice-to-have) dependency for fuzzy matching in the chat box
RAPID = True
try:
    from rapidfuzz import process, fuzz
except Exception:
    RAPID = False

# AgGrid is optional for editing tables
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID = False

# ------------------------------------------------------------------
# Streamlit config
# ------------------------------------------------------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# ------------------------------------------------------------------
# CSS: glassy cards + soft sidebar like the screenshot
# ------------------------------------------------------------------
CSS = """
<style>
:root{
  --bg: linear-gradient(180deg,#7aa0a8 0%, #5c7a86 55%, #4c6572 100%);
  --panel:#eef4f7;
  --card:rgba(255,255,255,.68);
  --muted:#66778a; --text:#1d2a36;
  --ring-red:#ea5455; --ring-amber:#f19f38; --ring-green:#34c38f;
  --border:rgba(255,255,255,.55);
}

html, body, [data-testid="stAppViewContainer"]{
  background: var(--bg);
}
.block-container{ padding-top: .6rem; }

.glass{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 8px 28px rgba(0,0,0,.18);
  backdrop-filter: blur(8px);
}

.sidebar .sidebar-content{ padding-top: 0 !important; }
[data-testid="stSidebar"]{
  background: transparent;
}
.sb{
  background: rgba(255,255,255,.35);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,.15);
  padding: 14px 14px 10px 14px;
}
.sb-title{
  font-weight: 800; font-size: 1.05rem; color: #123; margin: 4px 0 10px 0;
}
.sb-item{
  display:flex; align-items:center; gap:.6rem;
  padding:.55rem .6rem; margin:.18rem 0;
  border-radius: 12px; font-weight:600; color:#234;
}
.sb-item:hover{ background: rgba(255,255,255,.55) }
.sb-active{ background: white; }
.sb-icon{ width:22px; text-align:center; opacity:.9}

.card{ padding: 14px; }
.card h4{ margin: 0 0 6px 0; color:#1c2b35}
.sub{ color: var(--muted); font-size:.82rem; }

.kpi{
  display:flex; align-items:center; gap:14px;
}
.k-val{ font-size: 1.6rem; font-weight: 900; color:#0f2530}
.k-cap{ color:#3a4b58; font-size:.85rem }

.btn-link{
  display:inline-flex; align-items:center; gap:.45rem; padding:.5rem .7rem;
  border:1px solid #dfe7ee; border-radius:10px; background:white; color:#1b2a35; font-weight:600;
}
.chart{ padding: 4px 8px 0 0; }

.chat-box{
  padding: 12px; display:flex; flex-direction:column; gap:.6rem;
}
.chat-prompt input{ background:white !important; }
.chat-msg{
  background: rgba(255,255,255,.7); padding:.55rem .7rem; border-radius:10px; color:#22323d; border:1px solid #dfe7ee;
}
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

# Required tables
P = load(P_CSV, ["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"])
S = load(S_CSV, ["Supplier_ID","Supplier_Name","Email","Phone"])
T = load(T_CSV, ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"])

# Types & derived
P["Quantity"] = pd.to_numeric(P["Quantity"], errors="coerce").fillna(0).astype(int)
P["MinStock"] = pd.to_numeric(P["MinStock"], errors="coerce").fillna(0).astype(int)
P["UnitPrice"] = pd.to_numeric(P["UnitPrice"], errors="coerce").fillna(0.0)
if len(T):
    T["Qty"] = pd.to_numeric(T["Qty"], errors="coerce").fillna(0).astype(int)
    T["UnitPrice"] = pd.to_numeric(T["UnitPrice"], errors="coerce").fillna(0.0)
    T["Timestamp"] = pd.to_datetime(T["Timestamp"], errors="coerce").fillna(pd.Timestamp.utcnow())

P["Status"] = np.where(P["Quantity"] < P["MinStock"], "Low", "OK")
LOW = P[P["Status"]=="Low"]
REORDER = P[P["Quantity"]<=P["MinStock"]]   # same bucket for now
IN_STOCK = P[P["Quantity"]>0]
INV_VALUE = float((P["Quantity"]*P["UnitPrice"]).sum())

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def pie_gauge(value, total, title, color, suffix=" Items"):
    val = int(value)
    tot = int(total) if total else max(1, int(value))
    remain = max(tot - val, 0)
    fig = go.Figure(data=[go.Pie(
        values=[val, remain],
        labels=[title, ""],
        hole=0.7,
        marker_colors=[color, "rgba(0,0,0,0)"],
        textinfo="none",
        sort=False
    )])
    fig.update_layout(
        showlegend=False, height=220, margin=dict(l=0,r=0,t=10,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(text=f"<b>{val}</b><br><span style='font-size:12px;color:#6b7f8e'>{suffix}</span>",
                          x=0.5,y=0.5,showarrow=False)]
    )
    return fig

def plotly_light(fig, h=260):
    fig.update_layout(
        template="plotly_white", height=h,
        margin=dict(l=10,r=10,t=28,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e6eef3")
    return fig

def aggrid(df, key="grid", height=420, editable=True):
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return None
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=editable, filter=True, sortable=True, resizable=True)
    if "UnitPrice" in df.columns: gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
    return AgGrid(df, gridOptions=gb.build(), theme="balham", height=height, key=key, update_mode=GridUpdateMode.VALUE_CHANGED)

def fuzzy_one(query, choices, cutoff=70):
    if not RAPID:
        for c in choices:
            if str(query).lower() in str(c).lower(): return c, 100
        return None, 0
    res = process.extractOne(str(query), list(choices), scorer=fuzz.WRatio)
    if not res: return None, 0
    val, score, _ = res
    return val if score>=cutoff else None, score

def assistant_answer(q: str) -> dict:
    ql = q.strip().lower()
    if not ql: return {"text":"Type a query like: stock of USB hub, supplier of Mouse, id of Monitor, low stock, sales for Printer last month."}

    if any(k in ql for k in ["low stock","reorder","below min"]):
        rows = LOW[["Product_ID","SKU","Name","Quantity","MinStock","Supplier_ID"]]
        return {"text":"No low-stock items."} if rows.empty else {"text":f"{len(rows)} low-stock items.", "table":rows}

    m = re.search(r"(stock of|supplier of|price of|id of|sku of|sales for)\s+(.+)", ql)
    target_name = None
    if m: target_name = m.group(2).strip()
    if not target_name:
        toks = [t for t in re.findall(r"[A-Za-z0-9\-()_]{3,}", ql)]
        if toks: target_name = " ".join(toks[-3:])

    target = None
    if target_name:
        cand = P[P["Name"].str.contains(target_name, case=False, na=False)]
        if len(cand)==1: target = cand.iloc[0]
        elif len(cand)>1:
            w,_ = fuzzy_one(target_name, cand["Name"].tolist()); 
            if w is not None: target = cand[cand["Name"]==w].iloc[0]
        else:
            w,_ = fuzzy_one(target_name, P["Name"].dropna().tolist())
            if w is not None: target = P[P["Name"]==w].iloc[0]

    if "stock of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — {int(target['Quantity'])} in stock (min {int(target['MinStock'])})."}

    if "supplier of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        sup = S[S["Supplier_ID"].astype(str)==str(target["Supplier_ID"])]["Supplier_Name"]
        return {"text": f"Supplier: {sup.values[0] if len(sup) else 'N/A'} (ID {target['Supplier_ID']})."}

    if "price of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — ${float(target['UnitPrice']):.2f} unit price."}

    if "id of" in ql or "sku of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — Product_ID: {target['Product_ID']} | SKU: {target['SKU']}"}

    if "sales for" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        df = T[T["Product_ID"].astype(str)==str(target["Product_ID"])]
        if df.empty: return {"text": f"No sales for {target['Name']}."}
        now = pd.Timestamp.utcnow()
        if "this month" in ql: df = df[df["Timestamp"].dt.to_period("M")==now.to_period("M")]
        if "last month" in ql:
            lm = (now.to_period("M")-1).to_timestamp()
            df = df[df["Timestamp"].dt.to_period("M")==lm.to_period("M")]
        df = df.copy(); df["Revenue"]=df["Qty"]*df["UnitPrice"]
        return {"text": f"Sales: {int(df['Qty'].sum())} units, ${float(df['Revenue'].sum()):.2f} revenue.", "table": df.sort_values('Timestamp', ascending=False)}
    return {"text":"Try: stock of <name>, supplier of <name>, id of <name>, low stock, sales for <name> this month."}

# ------------------------------------------------------------------
# Sidebar (exact left menu)
# ------------------------------------------------------------------
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Settings"]
with st.sidebar:
    st.markdown('<div class="sb">', unsafe_allow_html=True)
    st.markdown('<div class="sb-title">Inventory Manager</div>', unsafe_allow_html=True)

    def sb_item(label, icon, active):
        cls = "sb-item sb-active" if active else "sb-item"
        st.markdown(f'<div class="{cls}"><div class="sb-icon">{icon}</div>{label}</div>', unsafe_allow_html=True)

    # radio control (hidden) to set tab, items render like screenshot
    tab = st.radio("Navigation", tabs, index=tabs.index(st.session_state.get("tab","Dashboard")), label_visibility="collapsed")
    st.session_state.tab = tab

    sb_item("Dashboard", "🏠", tab=="Dashboard")
    sb_item("Inventory", "📦", tab=="Inventory")
    sb_item("Suppliers", "🏢", tab=="Suppliers")
    sb_item("Sales", "🧾", tab=="Sales")
    sb_item("Reports", "📊", tab=="Reports")
    sb_item("Settings", "⚙️", tab=="Settings")
    sb_item("Chat Assistant", "💬", False)  # purely visual per screenshot
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Dashboard (exact layout)
# ------------------------------------------------------------------
if tab == "Dashboard":
    # --- grid: we emulate the screenshot with carefully sized columns/rows ---
    # Row 1: Stock Overview gauges + Barcode card placeholder (without scanner)
    c_left, c_right = st.columns([2.1, 1.1])

    with c_left:
        card = st.container()
        with card:
            st.markdown('<div class="glass card">', unsafe_allow_html=True)
            st.markdown("<h4>Stock Overview</h4>", unsafe_allow_html=True)
            g1,g2,g3 = st.columns(3)
            with g1:
                fig = pie_gauge(len(LOW), len(P), "Low Stock", "var(--ring-red)", "Items")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f"<div class='sub'>Low Stock<br><b>{len(LOW)}</b> Items</div>", unsafe_allow_html=True)
            with g2:
                fig = pie_gauge(len(REORDER), len(P), "Reorder", "var(--ring-amber)", "Items")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f"<div class='sub'>Reorder<br><b>{len(REORDER)}</b> Items</div>", unsafe_allow_html=True)
            with g3:
                fig = pie_gauge(len(IN_STOCK), len(P), "In Stock", "var(--ring-green)", "Items")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f"<div class='sub'>In Stock<br><b>{len(IN_STOCK)}</b> Items</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")  # spacing

        # Supplier & Sales Data card (two mini charts)
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Supplier & Sales Data</h4>", unsafe_allow_html=True)
        s1, s2 = st.columns(2)

        # Top suppliers by count of products
        with s1:
            if len(S) and len(P):
                top_sup = P.groupby("Supplier_ID").agg(Items=("Product_ID","count")).reset_index()
                top_sup = top_sup.merge(S[["Supplier_ID","Supplier_Name"]], on="Supplier_ID", how="left").sort_values("Items", ascending=False).head(5)
                fig = px.bar(top_sup, x="Items", y="Supplier_Name", orientation="h", text="Items")
                plotly_light(fig, 220)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No supplier/product data.")
        # Sales by Category (this quarter)
        with s2:
            if len(T):
                t = T.copy()
                t["Revenue"] = t["Qty"]*t["UnitPrice"]
                df = t.merge(P[["Product_ID","Category"]], on="Product_ID", how="left")
                quarter = pd.Timestamp.utcnow().quarter
                df["Q"] = df["Timestamp"].dt.quarter
                df = df[df["Q"]==quarter]
                cat = df.groupby("Category").agg(Revenue=("Revenue","sum")).reset_index().sort_values("Revenue", ascending=False)
                fig = px.bar(cat, x="Revenue", y="Category", orientation="h", text_auto=".2s")
                plotly_light(fig, 220)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No sales yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        # Barcode Scan card placeholder (no scanner per request)
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Barcode Scan</h4>", unsafe_allow_html=True)
        st.markdown("<div class='sub'>Scanner disabled</div>", unsafe_allow_html=True)
        st.image("https://dummyimage.com/300x150/ffffff/cccccc.png&text=Barcode+Preview", use_column_width=True)
        st.markdown("<div class='footer-note'>Use keyboard barcode reader in Inventory → Search.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        # Detailed Reports quick links
        st.markdown('<div class="glass card">', unsafe_allow_html=True)
        st.markdown("<h4>Detailed Reports</h4>", unsafe_allow_html=True)
        col = st.columns(1)[0]
        col.button("Inventory History", use_container_width=True)
        col.button("Movement History", use_container_width=True)
        col.button("Top Performing Products", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")  # row spacing

    # Row 2: Chat Assistant + Trend Performance
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
            st.markdown("<div class='chat-msg'>User: “Check stock for SKU 789”<br/>Bot: “SKU… 150 units available. Supplier: Acme Corp.”</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2_right:
        st.markdown('<div class="glass card chart">', unsafe_allow_html=True)
        st.markdown("<h4>Trend Performance</h4>", unsafe_allow_html=True)
        if len(T):
            t = T.copy(); t["Revenue"] = t["Qty"]*t["UnitPrice"]; t["Month"] = t["Timestamp"].dt.to_period("M").dt.to_timestamp()
            # Top-selling products (units) — show last 6 months
            last6 = t["Month"].max() - pd.offsets.MonthBegin(6) if len(t) else None
            if last6 is not None:
                t = t[t["Month"] >= last6]
            top = (t.groupby(["Product_ID"])["Qty"].sum().sort_values(ascending=False).head(3).index.tolist()
                   if len(t) else [])
            t = t[t["Product_ID"].isin(top)]
            t = t.merge(P[["Product_ID","Name"]], on="Product_ID", how="left")
            fig = px.line(t, x="Month", y="Qty", color="Name", markers=True, title=None)
            plotly_light(fig, 260)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No sales to plot.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Other pages (kept functional, simple layout)
# ------------------------------------------------------------------
elif tab == "Inventory":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Inventory", unsafe_allow_html=True)
    show = P.copy()
    show["Status"] = np.where(show["Quantity"]<show["MinStock"], "Low","OK")
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(show)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
        grid = AgGrid(show, gridOptions=gb.build(), theme="balham", height=520,
                      update_mode=GridUpdateMode.VALUE_CHANGED, key="inv_grid")
        if st.button("💾 Save Changes", use_container_width=True):
            save(pd.DataFrame(grid["data"]), P_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(show, use_container_width=True, num_rows="dynamic", height=520)
        if st.button("💾 Save Changes", use_container_width=True):
            save(ed, P_CSV); st.success("Saved.")
    st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Suppliers":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Suppliers", unsafe_allow_html=True)
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(S)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        grid = AgGrid(S, gridOptions=gb.build(), theme="balham", height=520,
                      update_mode=GridUpdateMode.VALUE_CHANGED, key="sup_grid")
        if st.button("💾 Save", use_container_width=True):
            save(pd.DataFrame(grid["data"]), S_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(S, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save"): save(ed, S_CSV); st.success("Saved.")
    st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Sales":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Record Sale", unsafe_allow_html=True)
    if len(P)==0:
        st.info("Add products first.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        with c1: product = st.selectbox("Product", options=P["Name"])
        with c2: qty = st.number_input("Qty", 1, step=1)
        with c3: price = st.number_input("UnitPrice ($)", 0.0, step=0.01,
                                         value=float(P.loc[P["Name"]==product,"UnitPrice"].values[0]))
        with c4: date = st.date_input("Date", dt.date.today())
        if st.button("Add sale 🧾", use_container_width=True):
            pid = P.loc[P["Name"]==product, "Product_ID"].values[0]
            sid = f"S{int(pd.Timestamp.utcnow().timestamp())}"
            if len(T)==0:
                # build columns if missing
                cols = ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"]
                global T; T = pd.DataFrame(columns=cols)
            T.loc[len(T)] = [sid, pid, int(qty), float(price), pd.to_datetime(date)]
            idx = P.index[P["Product_ID"]==pid]
            if len(idx): P.loc[idx, "Quantity"] = (P.loc[idx, "Quantity"] - int(qty)).clip(lower=0)
            save(T, T_CSV); save(P, P_CSV); st.success("Recorded.")
    st.markdown("#### Recent Sales", unsafe_allow_html=True)
    if len(T):
        st.dataframe(T.sort_values("Timestamp", ascending=False).head(300), use_container_width=True, height=420)
    else:
        st.info("No sales yet.")
    st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Reports":
    st.markdown('<div class="glass card">', unsafe_allow_html=True)
    st.markdown("### Reports", unsafe_allow_html=True)
    if len(P):
        v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum"),
                                                                                 Items=("Product_ID","count")).reset_index()
        fig = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        st.plotly_chart(plotly_light(fig, 320), use_container_width=True)
        st.dataframe(v.rename(columns={"Items":"# Items"}), use_container_width=True)
    if len(T):
        t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        st.plotly_chart(plotly_light(fig2, 320), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
                df = pd.read_csv(up); df.columns = df.columns.str.strip()
                save(df, P_CSV); st.success("Products uploaded.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
