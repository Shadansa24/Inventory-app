import os, datetime as dt
import numpy as np, pandas as pd, streamlit as st, plotly.express as px

# ---------- Config ----------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# AgGrid (community features only)
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID = False

# ---------- Professional dark theme ----------
CSS = """
<style>
:root{
  --bg:#111418; --surface:#171b22; --card:#1a1f27; --muted:#9aa5b1; --txt:#e9edf3;
  --accent:#2aa3ff; --ok:#00c896; --warn:#f59e0b; --danger:#ff4d4d; --stroke:#222833;
}
html, body, [data-testid="stAppViewContainer"]{ background:var(--bg); color:var(--txt); }
.block-container{ padding-top: 1rem; }

.topbar{
  position: sticky; top: 0; z-index: 100;
  background: rgba(17,20,24,.85); backdrop-filter: blur(8px);
  border:1px solid var(--stroke); border-radius:16px; padding:10px 14px;
  box-shadow: 0 10px 26px rgba(0,0,0,.35);
}
.topbar-row{ display:flex; align-items:center; justify-content:space-between; gap:12px; }
.brand{ font-weight:800; letter-spacing:.2px; display:flex; gap:.6rem; align-items:center }
.nav{ display:flex; gap:.5rem; }
.nav .btn{
  background:var(--surface); color:#cfe1ff; border:1px solid var(--stroke);
  padding:.5rem .9rem; border-radius:10px; font-weight:600; cursor:pointer;
}
.nav .btn:hover{ border-color:#2e3948; background:#1c222b; }
.nav .active{ background:#1f2834; color:#eaf3ff; box-shadow:0 0 0 3px rgba(42,163,255,.20) inset; }

.banner{
  margin-top:.75rem; background:linear-gradient(180deg,#2a1e0c,#1b150b);
  color:#f7dbad; border:1px dashed #3f301a; border-radius:12px; padding:10px 12px;
}

.card{
  background:var(--card); border:1px solid var(--stroke); border-radius:16px; padding:16px;
  box-shadow:0 10px 26px rgba(0,0,0,.35);
}
.k-title{ color:#c6d0de; font-size:.9rem; font-weight:700; margin:0 0 .35rem 0;}
.k-value{ margin:0; font-size:1.9rem; font-weight:900;}
.k-note{ color:var(--muted); font-size:.82rem; }
.grid-4{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:12px 0; }

.panel{ background:var(--surface); border:1px solid var(--stroke); border-radius:14px; padding:12px; }
.filters{ display:grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap:10px; }  /* one clean row */

h1,h2,h3,h4,h5{ color:var(--txt); }
.subtitle{ color:var(--muted); font-size:.92rem; }

hr{ border:none; border-top:1px solid var(--stroke); margin:14px 0; }

.table-title{ color:#e9edf3; font-weight:800; font-size:1.1rem; margin:.4rem 0 .6rem; }
.caption{ color:var(--muted); font-size:.85rem; }

.badge{padding:.2rem .6rem;border-radius:999px;border:1px solid;display:inline-block;font-weight:700;font-size:.78rem;}
.badge-ok{color:var(--ok);border-color:rgba(0,200,150,.3);background:rgba(0,200,150,.08);}
.badge-low{color:var(--danger);border-color:rgba(255,77,77,.3);background:rgba(255,77,77,.08);}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Data IO ----------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV = os.path.join(DATA_DIR, "sales.csv")

def load(path, cols):
    if not os.path.exists(path): return pd.DataFrame(columns=cols)
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    for c in cols:
        if c not in df.columns: df[c] = np.nan
    return df[cols]

def save(df, path): df.to_csv(path, index=False)

# Seedframes
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
low_df = P[P["Status"]=="Low"].copy()
inventory_value = float((P["Quantity"]*P["UnitPrice"]).sum())

# ---------- Navigation ----------
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Settings"]
if "tab" not in st.session_state: st.session_state.tab = "Dashboard"

# Sticky top nav
nav = st.container()
with nav:
    st.markdown('<div class="topbar"><div class="topbar-row">', unsafe_allow_html=True)
    left, right = st.columns([6,6])
    with left:
        st.markdown('<div class="brand">📦 Inventory Manager</div>', unsafe_allow_html=True)
    with right:
        nav_cols = st.columns(len(tabs))
        for i, t in enumerate(tabs):
            active = " active" if st.session_state.tab == t else ""
            if nav_cols[i].button(t, key=f"nav_{t}", use_container_width=True):
                st.session_state.tab = t
            nav_cols[i].markdown(f'<span class="nav btn{active}"></span>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

tab = st.session_state.tab

# ---------- Helpers ----------
def kpi(title, value, note="", color="var(--txt)"):
    st.markdown(f'''
      <div class="card">
        <div class="k-title">{title}</div>
        <p class="k-value" style="color:{color}">{value}</p>
        <div class="k-note">{note}</div>
      </div>''', unsafe_allow_html=True)

def plotly_dark(fig, height=420):
    fig.update_layout(template="plotly_dark",
        paper_bgcolor="#171b22", plot_bgcolor="#171b22", font_color="#e9edf3",
        xaxis=dict(gridcolor="#263143"), yaxis=dict(gridcolor="#263143"),
        height=height, margin=dict(l=10,r=10,t=50,b=10))
    return fig

def aggrid(df, height=430, editable=False):
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return df
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=editable, filter=True, sortable=True, resizable=True)
    # No enterprise-only renderers. Keep it community-safe.
    if "UnitPrice" in df.columns:
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x?.toFixed(2):'-'")
    grid = AgGrid(df, gridOptions=gb.build(), theme="balham-dark",
                  height=height, fit_columns_on_grid_load=True,
                  update_mode=GridUpdateMode.VALUE_CHANGED)
    return pd.DataFrame(grid["data"])

# ---------- PAGES ----------

# Dashboard
if tab == "Dashboard":
    if not low_df.empty:
        st.markdown(f'<div class="banner">⚠️ {len(low_df)} low-stock items need attention</div>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("Stock Items", f"{int(P['Quantity'].sum())}", "Units on hand")
    with c2: kpi("Low Stock", f"{len(low_df)}", "Below minimum", color="var(--danger)")
    with c3: kpi("Inventory Value", f"${inventory_value:,.2f}", "Qty × unit price", color="var(--accent)")
    with c4:
        mtd = 0.0
        if len(T):
            m = T[T["Timestamp"].dt.to_period("M") == pd.Timestamp.utcnow().to_period("M")]
            mtd = float((m["Qty"]*m["UnitPrice"]).sum())
        kpi("Sales (MTD)", f"${mtd:,.2f}", "Month to date", color="var(--ok)")

    st.markdown('<div class="panel"><div class="filters">', unsafe_allow_html=True)
    q = st.text_input("Search name or SKU", placeholder="Search name or SKU", label_visibility="collapsed")
    cat = st.selectbox("Category", ["All"]+sorted(P["Category"].dropna().unique()), index=0)
    status = st.selectbox("Status", ["All","OK","Low"], index=0)
    topn = st.selectbox("Top N", [10,20,50,100], index=1)
    st.markdown('</div></div>', unsafe_allow_html=True)

    filt = P.copy()
    if q:
        filt = filt[filt["Name"].str.contains(q, case=False, na=False) |
                    filt["SKU"].astype(str).str.contains(q, case=False, na=False)]
    if cat!="All": filt = filt[filt["Category"]==cat]
    if status!="All": filt = filt[filt["Status"]==status]

    left,right = st.columns([2,1.2])
    with left:
        if len(filt):
            fig = px.bar(filt.sort_values("Quantity", ascending=False).head(topn),
                         x="Name", y="Quantity", color="Category", title="Stock by Product (filtered)")
            st.plotly_chart(plotly_dark(fig, 430), use_container_width=True)
        else:
            st.info("No items match filters.")
    with right:
        if len(P):
            v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum")).reset_index()
            fig2 = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory Value by Category")
            st.plotly_chart(plotly_dark(fig2, 430), use_container_width=True)

    st.markdown('<div class="table-title">Low-stock list</div>', unsafe_allow_html=True)
    if low_df.empty:
        st.success("All good — no low-stock items.")
    else:
        show = low_df[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice"]]
        aggrid(show, height=360, editable=False)

# Inventory
elif tab == "Inventory":
    st.markdown("## Inventory")
    st.markdown('<div class="caption">Sort, filter, paginate. Click “Save table” to persist.</div>', unsafe_allow_html=True)

    editable = P[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"]].copy()
    out = aggrid(editable, height=520, editable=True)

    if st.button("💾 Save table", use_container_width=True):
        save(out, P_CSV); st.success("Saved.")

    st.markdown("---")
    st.subheader("Quick add / update")
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
    if st.button("Add / Update", use_container_width=True):
        row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,
               "Quantity":int(qty),"MinStock":int(minq),"UnitPrice":float(unit),"Supplier_ID":sup}
        idx = P.index[P["Product_ID"].astype(str)==str(pid)]
        if len(idx): P.loc[idx[0]] = row; msg="Updated"
        else: P.loc[len(P)] = row; msg="Added"
        save(P, P_CSV); st.success(f"{msg} item.")

# Suppliers
elif tab == "Suppliers":
    st.markdown("## Suppliers")
    ed = aggrid(S, height=480, editable=True)
    if st.button("💾 Save", use_container_width=True):
        save(ed, S_CSV); st.success("Saved.")

# Sales
elif tab == "Sales":
    st.markdown("## Record Sale")
    if len(P)==0:
        st.info("Add products first.")
    else:
        col1,col2,col3,col4 = st.columns(4)
        with col1: product = st.selectbox("Product", options=P["Name"])
        with col2: qty  = st.number_input("Qty", 1, step=1)
        with col3: price = st.number_input("UnitPrice ($)", 0.0, step=0.01,
                                           value=float(P.loc[P["Name"]==product,"UnitPrice"].values[0]))
        with col4: date  = st.date_input("Date", dt.date.today())
        if st.button("Add sale 🧾", use_container_width=True):
            pid = P.loc[P["Name"]==product,"Product_ID"].values[0]
            sid = f"S{int(pd.Timestamp.utcnow().timestamp())}"
            T.loc[len(T)] = [sid,pid,int(qty),float(price),pd.to_datetime(date)]
            idx = P.index[P["Product_ID"]==pid]
            if len(idx): P.loc[idx,"Quantity"] = (P.loc[idx,"Quantity"] - int(qty)).clip(lower=0)
            save(T, T_CSV); save(P, P_CSV); st.success("Recorded.")

    st.markdown("### Recent Sales")
    show = T.sort_values("Timestamp", ascending=False).head(250) if len(T) else T
    aggrid(show, height=420, editable=False)

# Reports
elif tab == "Reports":
    st.markdown("## Reports")
    if len(P):
        v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum"), Items=("Product_ID","count")).reset_index()
        fig = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        st.plotly_chart(plotly_dark(fig, 430), use_container_width=True)
    if len(T):
        t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        st.plotly_chart(plotly_dark(fig2, 410), use_container_width=True)
    if not len(P) and not len(T):
        st.info("No data yet.")

# Settings
elif tab == "Settings":
    st.markdown("## Data")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download products.csv", P.to_csv(index=False).encode(),
                           "products.csv", "text/csv", use_container_width=True)
    with c2:
        up = st.file_uploader("Upload products.csv", type=["csv"])
    with c3:
        if up is not None:
            try:
                df = pd.read_csv(up); df.columns = df.columns.str.strip()
                save(df, P_CSV); st.success("Products uploaded.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
