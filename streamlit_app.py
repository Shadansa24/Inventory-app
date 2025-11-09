# PRO Inventory Manager (Streamlit)
# Look & feel: slate-dark, glass cards, top nav, pro KPIs, filters, charts, AgGrid
import os, datetime as dt
import numpy as np, pandas as pd, streamlit as st, plotly.express as px

# Optional rich grid
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID = False

# ---------- Setup ----------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

CSS = """
<style>
:root{
  --bg:#0b1020; --panel:#12182b; --card:#141b2f; --muted:#8b97b1;
  --txt:#e6ecff; --accent:#65b0ff; --success:#4ade80; --warn:#f59e0b; --danger:#ef4444;
  --ring: rgba(101,176,255,.25);
}
* {font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;}
.block-container{padding-top:1rem;}
.topnav{
  display:flex; gap:1rem; align-items:center; justify-content:space-between;
  background:linear-gradient(180deg, #0c1428 0%, #0b1020 100%);
  padding:12px 16px; border:1px solid #1d2741; border-radius:14px; box-shadow:0 10px 30px rgba(0,0,0,.35);
  position: sticky; top: 0; z-index: 50;
}
.brand{display:flex; gap:.6rem; align-items:center; color:var(--txt); font-weight:700; font-size:1.05rem}
.tabs{display:flex; gap:.5rem;}
.tab{
  padding:.45rem .8rem; border-radius:10px; color:#c9d6ff; border:1px solid transparent;
  background:transparent; cursor:pointer;
}
.tab.active{background:rgba(101,176,255,.12); border-color:#223154; color:#eaf2ff; box-shadow:0 0 0 3px var(--ring) inset}
.kpis{display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; margin:14px 0;}
.card{
  background:linear-gradient(180deg, #12182b 0%, #0f1526 100%);
  border:1px solid #1e3157; border-radius:16px; padding:16px; box-shadow:0 10px 26px rgba(0,0,0,.35);
}
.kpi-title{color:#c1cced; font-size:.9rem; font-weight:600; margin:0 0 .35rem 0}
.kpi-value{font-size:1.9rem; font-weight:800; margin:0}
.kpi-note{color:var(--muted); font-size:.8rem}
.row{display:grid; grid-template-columns:2fr 1.4fr; gap:16px; margin-top:8px}
.h3{color:#e8eeff; font-weight:700; margin:.2rem 0 .6rem}
.alert{
  border:1px dashed #3b2a16; background:linear-gradient(180deg,#20140a,#15100b);
  color:#f8d6a8; padding:10px 12px; border-radius:12px;
}
.filterbar{display:flex; gap:.6rem; align-items:center; margin:.2rem 0 10px}
input, select{border-radius:10px !important}
.status{padding:.2rem .55rem; border-radius:999px; font-size:.78rem; font-weight:600}
.status.ok{background:rgba(74,222,128,.12); color:var(--success); border:1px solid rgba(74,222,128,.25)}
.status.low{background:rgba(239,68,68,.12); color:var(--danger); border:1px solid rgba(239,68,68,.25)}
hr{border:none; border-top:1px solid #1b2744; margin:12px 0}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Data ----------
DATA_DIR = "data"
P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV = os.path.join(DATA_DIR, "sales.csv")
os.makedirs(DATA_DIR, exist_ok=True)

def load(path, cols):
    if not os.path.exists(path): return pd.DataFrame(columns=cols)
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    for c in cols:
        if c not in df.columns: df[c] = np.nan
    return df[cols]

def save(df, path): df.to_csv(path, index=False)

P = load(P_CSV, ["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"])
S = load(S_CSV, ["Supplier_ID","Supplier_Name","Email","Phone"])
T = load(T_CSV, ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"])

# Types
P["Quantity"] = pd.to_numeric(P["Quantity"], errors="coerce").fillna(0).astype(int)
P["MinStock"] = pd.to_numeric(P["MinStock"], errors="coerce").fillna(0).astype(int)
P["UnitPrice"] = pd.to_numeric(P["UnitPrice"], errors="coerce").fillna(0.0)
if len(T):
    T["Qty"] = pd.to_numeric(T["Qty"], errors="coerce").fillna(0).astype(int)
    T["UnitPrice"] = pd.to_numeric(T["UnitPrice"], errors="coerce").fillna(0.0)
    T["Timestamp"] = pd.to_datetime(T["Timestamp"], errors="coerce").fillna(pd.Timestamp.utcnow())

# ---------- Top nav ----------
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Settings"]
if "tab" not in st.session_state: st.session_state.tab = "Dashboard"
clicked = st.session_state.tab

col_nav = st.container()
with col_nav:
    st.markdown(
        f"""
        <div class="topnav">
          <div class="brand">📦 Inventory Manager</div>
          <div class="tabs">
            {''.join([f'<span class="tab {"active" if t==clicked else ""}" onclick="window.parent.postMessage({{"setTab":"{t}"}}, "*")">{t}</span>' for t in tabs])}
          </div>
        </div>
        """, unsafe_allow_html=True
    )

# handle tab switch (custom event)
st.components.v1.html("""
<script>
window.addEventListener("message", (e)=>{
  if(e.data && e.data.setTab){
    const s = e.data.setTab;
    const streamlitDoc = window.parent.document;
    const textarea = streamlitDoc.querySelector('textarea[data-testid="stMarkdownContainer"]');
    window.parent.PostStreamlitMessage && 0;
  }
});
</script>
""", height=0)

# Fallback: use selectbox in sidebar (reliable)
with st.sidebar:
    st.selectbox("Navigate", tabs, key="tab")

tab = st.session_state.tab

# ---------- Shared derived data ----------
P["Status"] = np.where(P["Quantity"] < P["MinStock"], "Low", "OK")
inventory_value = float((P["Quantity"] * P["UnitPrice"]).sum())
low_df = P[P["Status"]=="Low"]

# ---------- Dashboard ----------
if tab == "Dashboard":
    # Alerts
    if not low_df.empty:
        st.markdown(f'<div class="alert">⚠️ {len(low_df)} low-stock items need attention</div>', unsafe_allow_html=True)

    # KPIs
    total_items = int(P["Quantity"].sum())
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown('<div class="card"><div class="kpi-title">Stock Items</div><p class="kpi-value" style="color:#eaf2ff">'
                    f'{total_items}</p><div class="kpi-note">Units on hand</div></div>', unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown('<div class="card"><div class="kpi-title">Low Stock</div><p class="kpi-value" style="color:var(--danger)">'
                    f'{len(low_df)}</p><div class="kpi-note">Below minimum</div></div>', unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown('<div class="card"><div class="kpi-title">Inventory Value</div><p class="kpi-value" style="color:var(--accent)">'
                    f'${inventory_value:,.2f}</p><div class="kpi-note">Qty × unit price</div></div>', unsafe_allow_html=True)
    with kpi_cols[3]:
        mtd = 0.0
        if len(T):
            t = T[T["Timestamp"].dt.to_period("M")==pd.Timestamp.utcnow().to_period("M")].copy()
            mtd = float((t["Qty"]*t["UnitPrice"]).sum())
        st.markdown('<div class="card"><div class="kpi-title">Sales (MTD)</div><p class="kpi-value" style="color:var(--success)">'
                    f'${mtd:,.2f}</p><div class="kpi-note">Month to date</div></div>', unsafe_allow_html=True)

    # Filters bar
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fcol1, fcol2, fcol3, fcol4 = st.columns([2,1,1,1])
    with fcol1: q = st.text_input("Search name or SKU")
    with fcol2: cat = st.selectbox("Category", ["All"]+sorted([c for c in P["Category"].dropna().unique()]), index=0)
    with fcol3: status = st.selectbox("Status", ["All","OK","Low"], index=0)
    with fcol4: topn = st.selectbox("Top N", [10,20,50,100], index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    filt = P.copy()
    if q:     filt = filt[filt["Name"].str.contains(q, case=False, na=False) | filt["SKU"].astype(str).str.contains(q, case=False, na=False)]
    if cat!="All":    filt = filt[filt["Category"]==cat]
    if status!="All": filt = filt[filt["Status"]==status]

    # Charts
    st.markdown('<div class="row">', unsafe_allow_html=True)
    with st.container():
        left, right = st.columns([2,1.4], gap="large")
        with left:
            if len(filt):
                fig = px.bar(filt.sort_values("Quantity",ascending=False).head(topn),
                             x="Name", y="Quantity", color="Category",
                             title="Stock by Product (filtered)")
                fig.update_layout(template="plotly_dark", height=430, margin=dict(l=10,r=10,t=50,b=10),
                                  paper_bgcolor="#0f1526", plot_bgcolor="#0f1526", font_color="#e6ecff")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No items match filters.")
        with right:
            if len(P):
                agg = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum")).reset_index()
                fig2 = px.bar(agg, x="Category", y="Value", title="Inventory Value by Category", text_auto=".2s")
                fig2.update_layout(template="plotly_dark", height=430, margin=dict(l=10,r=10,t=50,b=10),
                                   paper_bgcolor="#0f1526", plot_bgcolor="#0f1526", font_color="#e6ecff")
                st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### Low-stock list")
    if low_df.empty:
        st.success("All good. No low-stock items.")
    else:
        show = low_df[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice"]].copy()
        show["Status"] = np.where(show["Quantity"]<show["MinStock"], "LOW", "OK")
        if AGGRID:
            gb = GridOptionsBuilder.from_dataframe(show)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(editable=False, filter=True, sortable=True)
            AgGrid(show, gridOptions=gb.build(), height=350, theme="balham")
        else:
            st.dataframe(show, use_container_width=True)

# ---------- Inventory ----------
elif tab == "Inventory":
    st.markdown('<div class="h3">Inventory</div>', unsafe_allow_html=True)

    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(P)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        grid = AgGrid(P, gridOptions=gb.build(), height=480, theme="balham", update_mode=GridUpdateMode.VALUE_CHANGED)
        edited = grid["data"]
        if st.button("💾 Save table"):
            save(pd.DataFrame(edited), P_CSV); st.success("Saved.")
    else:
        edited = st.data_editor(P, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save table"):
            save(edited, P_CSV); st.success("Saved.")

    st.markdown("---")
    st.subheader("Quick add item")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        pid = st.text_input("Product_ID")
        sku = st.text_input("SKU")
    with c2:
        name = st.text_input("Name")
        cat  = st.text_input("Category")
    with c3:
        qty  = st.number_input("Quantity", 0, step=1)
        minq = st.number_input("MinStock", 0, step=1)
    with c4:
        unit = st.number_input("UnitPrice ($)", 0.0, step=0.01, format="%.2f")
        sup  = st.text_input("Supplier_ID")
    if st.button("Add / Update"):
        row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,"Quantity":int(qty),"MinStock":int(minq),"UnitPrice":float(unit),"Supplier_ID":sup}
        idx = P.index[P["Product_ID"].astype(str)==str(pid)]
        if len(idx): P.loc[idx[0]] = row; msg="Updated"
        else: P.loc[len(P)] = row; msg="Added"
        save(P, P_CSV); st.success(f"{msg}.")

# ---------- Suppliers ----------
elif tab == "Suppliers":
    st.markdown('<div class="h3">Suppliers</div>', unsafe_allow_html=True)
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(S)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True)
        grid = AgGrid(S, gridOptions=gb.build(), height=460, theme="balham", update_mode=GridUpdateMode.VALUE_CHANGED)
        if st.button("💾 Save"):
            save(pd.DataFrame(grid["data"]), S_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(S, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save"): save(ed, S_CSV); st.success("Saved.")

# ---------- Sales ----------
elif tab == "Sales":
    st.markdown('<div class="h3">Record sale</div>', unsafe_allow_html=True)
    if len(P)==0:
        st.info("Add products first.")
    else:
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            product = st.selectbox("Product", options=P["Name"])
        with col2:
            qty  = st.number_input("Qty", 1, step=1)
        with col3:
            price = st.number_input("UnitPrice ($)", 0.0, step=0.01, value=float(P.loc[P["Name"]==product,"UnitPrice"].values[0]))
        with col4:
            date  = st.date_input("Date", dt.date.today())
        if st.button("Add sale 🧾"):
            pid = P.loc[P["Name"]==product,"Product_ID"].values[0]
            sid = f"S{int(pd.Timestamp.utcnow().timestamp())}"
            T.loc[len(T)] = [sid,pid,int(qty),float(price),pd.to_datetime(date)]
            # decrement stock
            idx = P.index[P["Product_ID"]==pid]
            if len(idx): P.loc[idx,"Quantity"] = (P.loc[idx,"Quantity"] - int(qty)).clip(lower=0)
            save(T, T_CSV); save(P, P_CSV); st.success("Recorded.")

    st.markdown("#### Recent")
    if len(T):
        show = T.sort_values("Timestamp", ascending=False).head(200)
        if AGGRID:
            gb = GridOptionsBuilder.from_dataframe(show)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(editable=False, filter=True, sortable=True)
            AgGrid(show, gridOptions=gb.build(), height=420, theme="balham")
        else:
            st.dataframe(show, use_container_width=True)
    else:
        st.info("No sales yet.")

# ---------- Reports ----------
elif tab == "Reports":
    st.markdown('<div class="h3">Reports</div>', unsafe_allow_html=True)
    if len(P):
        P2 = P.copy(); P2["Value"] = P2["Quantity"]*P2["UnitPrice"]
        g = P2.groupby("Category").agg(Value=("Value","sum"), Items=("Product_ID","count")).reset_index()
        fig = px.bar(g, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10,r=10,t=50,b=10),
                          paper_bgcolor="#0f1526", plot_bgcolor="#0f1526", font_color="#e6ecff")
        st.plotly_chart(fig, use_container_width=True)
    if len(T):
        T2 = T.copy(); T2["Revenue"] = T2["Qty"]*T2["UnitPrice"]; T2["Month"]=T2["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = T2.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        fig2.update_layout(template="plotly_dark", height=420, margin=dict(l=10,r=10,t=50,b=10),
                           paper_bgcolor="#0f1526", plot_bgcolor="#0f1526", font_color="#e6ecff")
        st.plotly_chart(fig2, use_container_width=True)
    if not len(P) and not len(T):
        st.info("No data yet.")

# ---------- Settings ----------
elif tab == "Settings":
    st.markdown('<div class="h3">Data</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Download products.csv"):
            st.download_button("Download products.csv", P.to_csv(index=False).encode(), "products.csv", "text/csv", key="pdl")
    with c2:
        st.file_uploader("Upload products.csv", type=["csv"], key="pup")
    with c3:
        if st.session_state.get("pup"):
            try:
                df = pd.read_csv(st.session_state["pup"])
                df.columns = df.columns.str.strip()
                save(df, P_CSV); st.success("Products uploaded.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
