# -*- coding: utf-8 -*-
"""
Inventory Manager — Streamlit Cloud ready
- Low-stock alerts (UI + optional webhook/email)
- Barcode scanning (webcam via streamlit-webrtc + pyzbar, and keyboard-scanner fallback)
- Chat assistant (offline, intent-based over your CSVs)
- AgGrid editing, reports, CSV import/export
"""
import os, re, io, smtplib, json, datetime as dt
from email.message import EmailMessage

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional/soft deps
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID = False

WEBRTC = True
PYZBAR = True
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    import av
except Exception:
    WEBRTC = False
try:
    from pyzbar.pyzbar import decode as zbar_decode
    from PIL import Image
except Exception:
    PYZBAR = False

# Fuzzy matching for the chat assistant
RAPID = True
try:
    from rapidfuzz import process, fuzz
except Exception:
    RAPID = False

# ======== Config ========
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# ======== Dark theme & UI CSS ========
CSS = """
<style>
:root{
  --bg:#0b1020; --panel:#0f162b; --card:#121a33; --elev:#0e1529;
  --muted:#9aa6c1; --text:#e8eeff; --accent:#65b0ff; --ok:#22c55e; --warn:#f59e0b; --danger:#ef4444;
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg);}
.block-container{ padding-top: .6rem; }
.topbar{
  width:100%; position:sticky; top:0; z-index:100;
  background: linear-gradient(180deg, #111a33 0%, #0d152b 100%);
  border:1px solid #1b2a4a; border-radius:16px; padding:12px 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
.topbar-row{ display:flex; align-items:center; justify-content:space-between; gap:12px; }
.brand{ color:var(--text); font-weight:800; letter-spacing:.3px; display:flex; gap:.6rem; align-items:center}
.brand-badge{background:rgba(101,176,255,.15); color:#a7d1ff; padding:.25rem .5rem; border:1px solid #263a62; border-radius:999px; font-size:.75rem;}
.nav{ display:flex; gap:.4rem; }
.nav button{
  background: transparent; color:#cfe1ff; border:1px solid transparent;
  padding:.5rem .8rem; border-radius:10px; cursor:pointer; font-weight:600;
}
.nav button:hover{ background:rgba(101,176,255,.10); border-color:#263a62; }
.nav .active{ background:rgba(101,176,255,.18); border-color:#2a3f69; color:#eaf2ff; box-shadow:0 0 0 3px rgba(101,176,255,.25) inset; }
.banner{
  margin-top:.65rem; background:linear-gradient(180deg,#1c1409,#130f0a);
  color:#f7d9ac; border:1px dashed #3a2a14; border-radius:12px; padding:10px 12px;
}
.card{ background: linear-gradient(180deg, #121a33 0%, #0f172c 100%); border:1px solid #1e2b49; border-radius:16px; padding:16px; box-shadow:0 10px 26px rgba(0,0,0,.35); }
.k-title{ color:#c2cdee; font-size:.9rem; font-weight:700; margin:0 0 .35rem 0;}
.k-value{ margin:0; font-size:1.9rem; font-weight:900;}
.k-note{ color:var(--muted); font-size:.8rem; }
.panel{ background: var(--card); border:1px solid #1c2948; border-radius:16px; padding:14px; }
.row{ display:grid; grid-template-columns: 2fr 1.2fr; gap:14px; margin-top:10px;}
.filterbar{ display:flex; gap:10px; align-items:center; }
hr{ border:none; border-top:1px solid #1a2746; margin:12px 0; }
.caption{ color:var(--muted); font-size:.85rem; }
.status-chip{
  padding:.18rem .55rem; border-radius:999px; font-size:.78rem; font-weight:700; letter-spacing:.2px;
  border:1px solid; display:inline-block
}
.chip-ok{ color:var(--ok); border-color: rgba(34,197,94,.25); background: rgba(34,197,94,.10); }
.chip-low{ color:var(--danger); border-color: rgba(239,68,68,.25); background: rgba(239,68,68,.10); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ======== Data IO ========
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
        if c not in df.columns: df[c] = np.nan
    return df[cols]

def save(df, path):
    df.to_csv(path, index=False)

# Required columns
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
low_df = P[P["Status"] == "Low"].copy()
inventory_value = float((P["Quantity"] * P["UnitPrice"]).sum())

# ======== Helpers ========
def kpi_card(title, value, note="", color="#eaf2ff"):
    st.markdown(
        f'<div class="card"><div class="k-title">{title}</div>'
        f'<p class="k-value" style="color:{color}">{value}</p>'
        f'<div class="k-note">{note}</div></div>', unsafe_allow_html=True
    )

def plotly_darkify(fig, h=420):
    fig.update_layout(
        template="plotly_dark", height=h, margin=dict(l=10,r=10,t=50,b=10),
        paper_bgcolor="#0f172c", plot_bgcolor="#0f172c", font_color="#e8eeff",
        xaxis=dict(gridcolor="#24385f"), yaxis=dict(gridcolor="#24385f"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    return fig

def aggrid_table(df, height=430, editable=False, key="grid"):
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return {"data": df}
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=editable, filter=True, sortable=True, resizable=True)
    if set(["Quantity","MinStock","UnitPrice"]).issubset(df.columns):
        gb.configure_column("Quantity", type=["numericColumn"])
        gb.configure_column("MinStock", type=["numericColumn"])
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
    grid = gb.build()
    return AgGrid(df, gridOptions=grid, theme="balham-dark", height=height, fit_columns_on_grid_load=True, key=key)

def send_email_alert(subject, body):
    """Optional: SMTP alert when low stock is detected (configure in Settings)."""
    cfg = st.session_state.get("smtp_cfg")
    if not cfg or not cfg.get("enabled"): 
        return False, "Email alerts disabled"
    try:
        msg = EmailMessage()
        msg["From"] = cfg["from_addr"]; msg["To"] = cfg["to_addr"]; msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
            if cfg.get("tls", True): s.starttls()
            if cfg.get("user") and cfg.get("password"):
                s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
        return True, "Alert sent"
    except Exception as e:
        return False, f"Email failed: {e}"

def webhook_alert(url, payload):
    """Optional: POST webhook (e.g., Discord/Slack)."""
    try:
        import requests
        r = requests.post(url, json=payload, timeout=6)
        return r.ok, f"Webhook status {r.status_code}"
    except Exception as e:
        return False, f"Webhook failed: {e}"

# ======== Chat Assistant (offline, intent-based) ========
def fuzzy_one(query, choices, cutoff=70):
    if not RAPID:
        # naive fallback
        for c in choices:
            if str(query).lower() in str(c).lower():
                return c, 100
        return None, 0
    res = process.extractOne(str(query), list(choices), scorer=fuzz.WRatio)
    if not res: return None, 0
    val, score, _ = res
    return val if score>=cutoff else None, score

def assistant_answer(q: str, P: pd.DataFrame, S: pd.DataFrame, T: pd.DataFrame) -> dict:
    """
    Returns a dict with `text` (answer) and optional `table` (DataFrame).
    Supported intents (natural-language):
      - "stock of <name/SKU/id>"
      - "who is supplier of <product>"
      - "id/SKU of <product>"
      - "low stock", "reorder list"
      - "price of <product>"
      - "sales for <product> (this month|last month|all)"
    """
    ql = q.lower().strip()

    # low stock / reorder
    if re.search(r"(low stock|reorder|below min|need.*restock)", ql):
        rows = P[P["Quantity"] < P["MinStock"]][["Product_ID","SKU","Name","Quantity","MinStock","Supplier_ID","UnitPrice"]]
        if rows.empty:
            return {"text":"No items are below minimum stock."}
        return {"text": f"{len(rows)} item(s) below min. Showing list.", "table": rows.sort_values("Quantity")}

    # extract a token that looks like id or sku
    id_match = re.search(r"(product[_ ]?id|sku)\s*[:=]?\s*([A-Za-z0-9\-_/]+)", ql)
    name_token = None

    if id_match:
        token = id_match.group(2)
        df = P[(P["Product_ID"].astype(str).str.lower()==token) | (P["SKU"].astype(str).str.lower()==token)]
        if not df.empty:
            row = df.iloc[0]
            sup = S[S["Supplier_ID"].astype(str)==str(row["Supplier_ID"])]
            sup_name = sup["Supplier_Name"].values[0] if len(sup) else "N/A"
            return {"text": f"{row['Name']} | Stock {int(row['Quantity'])} (min {int(row['MinStock'])}) | Supplier: {sup_name} | Price ${float(row['UnitPrice']):.2f}"}

    # try to pull a quoted or trailing name
    m = re.search(r"(stock of|supplier of|price of|id of|sku of|sales for)\s+\"?([A-Za-z0-9\-() ._]+)\"?", ql)
    if m:
        name_token = m.group(2).strip()
    else:
        # fallback: last word chunk
        tokens = re.findall(r"[A-Za-z0-9\-()_]{3,}", ql)
        if len(tokens) >= 1:
            name_token = " ".join(tokens[-3:])

    # match by name/SKU
    target = None
    if name_token:
        # first exact-ish filters
        cand = P[
            P["Name"].str.contains(name_token, case=False, na=False) |
            P["SKU"].astype(str).str.contains(name_token, case=False, na=False)
        ]
        if len(cand)==1:
            target = cand.iloc[0]
        elif len(cand)>1:
            # choose closest by fuzzy
            winner, _ = fuzzy_one(name_token, cand["Name"].tolist())
            if winner is not None:
                target = cand[cand["Name"]==winner].iloc[0]
        else:
            # fuzzy over all names
            winner, _ = fuzzy_one(name_token, P["Name"].dropna().tolist())
            if winner is not None:
                target = P[P["Name"]==winner].iloc[0]

    # intent routing
    if "stock of" in ql or "how many" in ql or "in stock" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} stock: {int(target['Quantity'])} (min {int(target['MinStock'])})."}

    if "supplier" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        sup = S[S["Supplier_ID"].astype(str)==str(target["Supplier_ID"])]
        sup_name = sup["Supplier_Name"].values[0] if len(sup) else "N/A"
        return {"text": f"Supplier of {target['Name']}: {sup_name} (ID {target['Supplier_ID']})."}

    if "id of" in ql or re.search(r"\bwhat.*id\b", ql):
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — Product_ID: {target['Product_ID']}, SKU: {target['SKU']}"}

    if "sku of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — SKU: {target['SKU']}"}

    if "price of" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        return {"text": f"{target['Name']} — Unit price ${float(target['UnitPrice']):.2f}"}

    if "sales for" in ql:
        if target is None: return {"text":"Couldn't match a product."}
        df = T[T["Product_ID"].astype(str)==str(target["Product_ID"])].copy()
        if df.empty: return {"text": f"No sales recorded for {target['Name']}."}
        # timeframe
        now = pd.Timestamp.utcnow()
        if "this month" in ql:
            df = df[df["Timestamp"].dt.to_period("M")==now.to_period("M")]
        elif "last month" in ql:
            lm = (now.to_period("M") - 1).to_timestamp()
            df = df[df["Timestamp"].dt.to_period("M")==lm.to_period("M")]
        df["Revenue"] = df["Qty"]*df["UnitPrice"]
        return {"text": f"Sales for {target['Name']}: {int(df['Qty'].sum())} units, ${float(df['Revenue'].sum()):.2f} revenue.", "table": df.sort_values("Timestamp", ascending=False)}

    # default help
    return {"text": "Try: 'stock of USB-C Hub', 'supplier of Wireless Mouse', 'id of Monitor 27-inch', 'low stock', 'sales for ... this month'."}

# ======== Navigation ========
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Scanner","Assistant","Settings"]
if "tab" not in st.session_state: st.session_state.tab = "Dashboard"

# Top nav
c = st.container()
with c:
    cols = st.columns([1,5,1])
    with cols[1]:
        st.markdown('<div class="topbar"><div class="topbar-row">', unsafe_allow_html=True)
        st.markdown('<div class="brand">📦 Inventory Manager <span class="brand-badge">Pro</span></div>', unsafe_allow_html=True)
        nav_cols = st.columns(len(tabs))
        for i, t in enumerate(tabs):
            if nav_cols[i].button(t, key=f"nav_{t}", use_container_width=True):
                st.session_state.tab = t
        st.markdown('</div></div>', unsafe_allow_html=True)

tab = st.session_state.tab

# ======== Pages ========

# 1) Dashboard
if tab == "Dashboard":
    if not low_df.empty:
        st.markdown(f'<div class="banner">⚠️ {len(low_df)} low-stock items need attention</div>', unsafe_allow_html=True)
        st.toast(f"{len(low_df)} low-stock items detected", icon="⚠️")

    k1,k2,k3,k4 = st.columns(4)
    with k1: kpi_card("Stock Items", f"{int(P['Quantity'].sum())}", "Units on hand")
    with k2: kpi_card("Low Stock", f"{len(low_df)}", "Below minimum", color="var(--danger)")
    with k3: kpi_card("Inventory Value", f"${inventory_value:,.2f}", "Qty × unit price", color="var(--accent)")
    with k4:
        mtd = 0.0
        if len(T):
            this_m = pd.Timestamp.utcnow().to_period("M")
            m = T[T["Timestamp"].dt.to_period("M")==this_m]
            mtd = float((m["Qty"]*m["UnitPrice"]).sum())
        kpi_card("Sales (MTD)", f"${mtd:,.2f}", "Month to date", color="var(--ok)")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    f1,f2,f3,f4 = st.columns([2,1,1,1])
    with f1: q = st.text_input("Search name or SKU", label_visibility="collapsed", placeholder="Search name or SKU")
    with f2: cat = st.selectbox("Category", ["All"]+sorted(P["Category"].dropna().unique()), index=0)
    with f3: status = st.selectbox("Status", ["All","OK","Low"], index=0)
    with f4: topn = st.selectbox("Top N", [10,20,50,100], index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    filt = P.copy()
    if q:
        filt = filt[filt["Name"].str.contains(q, case=False, na=False) | filt["SKU"].astype(str).str.contains(q, case=False, na=False)]
    if cat!="All": filt = filt[filt["Category"]==cat]
    if status!="All": filt = filt[filt["Status"]==status]

    left,right = st.columns([2,1.2])
    with left:
        if len(filt):
            fig = px.bar(filt.sort_values("Quantity", ascending=False).head(topn),
                         x="Name", y="Quantity", color="Category", title="Stock by Product (filtered)")
            st.plotly_chart(plotly_darkify(fig, 430), use_container_width=True)
        else:
            st.info("No items match filters.")
    with right:
        if len(P):
            v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum")).reset_index()
            fig2 = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory Value by Category")
            st.plotly_chart(plotly_darkify(fig2, 430), use_container_width=True)

    st.markdown("#### Low-stock list")
    if low_df.empty:
        st.success("All good — no low-stock items.")
    else:
        show = low_df[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice"]].copy()
        aggrid_table(show, height=360, key="dash_low")

# 2) Inventory
elif tab == "Inventory":
    st.markdown("### Inventory")
    preview = P.copy()
    preview["Status"] = np.where(preview["Quantity"] < preview["MinStock"],
                                 '<span class="status-chip chip-low">LOW</span>',
                                 '<span class="status-chip chip-ok">OK</span>')
    st.markdown('<div class="caption">Click headers to sort • Filter rows • Pagination</div>', unsafe_allow_html=True)

    if AGGRID:
        df_show = preview[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID","Status"]]
        gb = GridOptionsBuilder.from_dataframe(df_show)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
        gb.configure_column("Status", editable=False, cellRenderer="agGroupCellRenderer",
                            cellRendererParams={"innerRenderer": "function(p){return p.value}"})
        grid = AgGrid(df_show, gridOptions=gb.build(), theme="balham-dark", height=520,
                      allow_unsafe_jscode=True, update_mode=GridUpdateMode.VALUE_CHANGED, key="inv_grid")
        if st.button("💾 Save table", use_container_width=True):
            out = pd.DataFrame(grid["data"]).drop(columns=["Status"])
            save(out, P_CSV); st.success("Saved.")
    else:
        st.dataframe(preview, use_container_width=True, height=520)

    st.markdown("---")
    st.subheader("Quick add / update")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        pid = st.text_input("Product_ID")
        sku = st.text_input("SKU / Barcode")
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
        row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,"Quantity":int(qty),
               "MinStock":int(minq),"UnitPrice":float(unit),"Supplier_ID":sup}
        idx = P.index[P["Product_ID"].astype(str)==str(pid)]
        if len(idx): P.loc[idx[0]] = row; msg="Updated"
        else: P.loc[len(P)] = row; msg="Added"
        save(P, P_CSV); st.success(f"{msg} item.")

# 3) Suppliers
elif tab == "Suppliers":
    st.markdown("### Suppliers")
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(S)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        grid = AgGrid(S, gridOptions=gb.build(), theme="balham-dark", height=480,
                      update_mode=GridUpdateMode.VALUE_CHANGED, key="sup_grid")
        if st.button("💾 Save", use_container_width=True):
            save(pd.DataFrame(grid["data"]), S_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(S, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save"): save(ed, S_CSV); st.success("Saved.")

# 4) Sales
elif tab == "Sales":
    st.markdown("### Record Sale")
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

    st.markdown("#### Recent Sales")
    if len(T):
        show = T.sort_values("Timestamp", ascending=False).head(250)
        aggrid_table(show, height=420, key="sales_recent")
    else:
        st.info("No sales yet.")

# 5) Reports
elif tab == "Reports":
    st.markdown("### Reports")
    if len(P):
        v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(
            Value=("Value","sum"), Items=("Product_ID","count")).reset_index()
        fig = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        st.plotly_chart(plotly_darkify(fig, 430), use_container_width=True)
        st.dataframe(v.rename(columns={"Items":"# Items"}), use_container_width=True)
    if len(T):
        t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        st.plotly_chart(plotly_darkify(fig2, 410), use_container_width=True)

        # Top sellers
        top = t.groupby("Product_ID").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        top = top.merge(P[["Product_ID","Name","Category"]], on="Product_ID", how="left").sort_values("Units", ascending=False).head(15)
        fig3 = px.bar(top, x="Name", y="Units", color="Category", title="Top Selling Products")
        st.plotly_chart(plotly_darkify(fig3, 400), use_container_width=True)
        st.dataframe(top, use_container_width=True)
    if not len(P) and not len(T):
        st.info("No data yet.")

# 6) Scanner (Barcode)
elif tab == "Scanner":
    st.subheader("Barcode Scanner")
    st.caption("Use a USB barcode reader (acts like keyboard) **or** webcam scanner below.")

    # Keyboard/USB scanner fallback
    code_in = st.text_input("Scan or paste barcode / SKU")
    if st.button("Lookup", type="primary"):
        res = P[(P["SKU"].astype(str).str.lower()==str(code_in).lower()) | (P["Product_ID"].astype(str).str.lower()==str(code_in).lower())]
        if res.empty:
            res = P[P["SKU"].astype(str).str.contains(str(code_in), case=False, na=False)]
        if res.empty:
            st.error("No match.")
        else:
            st.success(f"Found {len(res)} item(s).")
            st.dataframe(res, use_container_width=True)

    st.markdown("---")
    if WEBRTC and PYZBAR:
        st.caption("Webcam scanner (HTTPS/localhost only). Hold the barcode inside the frame.")
        class ZBarProcessor:
            def __init__(self):
                self.last = None
            def recv(self, frame):
                frm = frame.to_ndarray(format="bgr24")
                # Convert to PIL and decode
                pil = Image.fromarray(frm[:, :, ::-1])
                codes = zbar_decode(pil)
                if codes:
                    self.last = codes[0].data.decode("utf-8", errors="ignore")
                return av.VideoFrame.from_ndarray(frm, format="bgr24")

        state = webrtc_streamer(key="scanner", mode=WebRtcMode.SENDRECV,
                                video_processor_factory=ZBarProcessor,
                                media_stream_constraints={"video": True, "audio": False})
        if state and state.video_processor and state.video_processor.last:
            st.info(f"Scanned: **{state.video_processor.last}**")
            scanned = state.video_processor.last
            res = P[(P["SKU"].astype(str)==scanned) | (P["Product_ID"].astype(str)==scanned)]
            if res.empty:
                res = P[P["SKU"].astype(str).str.contains(scanned, na=False)]
            if not res.empty:
                st.dataframe(res, use_container_width=True)
    else:
        if not WEBRTC:
            st.warning("`streamlit-webrtc` unavailable (optional). Use the text box above or add the package.")
        if not PYZBAR:
            st.warning("`pyzbar`/Pillow unavailable (optional). Add them to requirements to enable webcam scanning.")

# 7) Assistant
elif tab == "Assistant":
    st.subheader("Inventory Assistant")
    st.caption("Ask things like: *stock of USB-C Hub*, *supplier of Wireless Mouse*, *id of Monitor*, *low stock*, *sales for Printer Paper this month*.")
    q = st.text_input("Ask a question")
    if st.button("Ask", type="primary") or q:
        ans = assistant_answer(q, P, S, T) if q else {"text":"Type a question."}
        st.success(ans["text"])
        if "table" in ans and isinstance(ans["table"], pd.DataFrame) and len(ans["table"]):
            aggrid_table(ans["table"], height=360, key="asst_tbl")

# 8) Settings
elif tab == "Settings":
    st.markdown("### Data")
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

    st.markdown("---")
    st.markdown("### Alerts (optional)")
    if "smtp_cfg" not in st.session_state:
        st.session_state.smtp_cfg = {"enabled": False}
    with st.expander("Email alerts"):
        on = st.checkbox("Enable email alerts", value=st.session_state.smtp_cfg.get("enabled", False))
        host = st.text_input("SMTP host", value=st.session_state.smtp_cfg.get("host",""))
        port = st.number_input("SMTP port", value=int(st.session_state.smtp_cfg.get("port",587)))
        user = st.text_input("SMTP username", value=st.session_state.smtp_cfg.get("user",""))
        pwd  = st.text_input("SMTP password", value=st.session_state.smtp_cfg.get("password",""), type="password")
        from_addr = st.text_input("From email", value=st.session_state.smtp_cfg.get("from_addr",""))
        to_addr   = st.text_input("To email", value=st.session_state.smtp_cfg.get("to_addr",""))
        tls = st.checkbox("Use STARTTLS", value=st.session_state.smtp_cfg.get("tls", True))
        if st.button("Save email settings"):
            st.session_state.smtp_cfg = {"enabled": on,"host":host,"port":int(port),"user":user,"password":pwd,
                                         "from_addr":from_addr,"to_addr":to_addr,"tls":tls}
            st.success("Saved.")
        if st.button("Test low-stock email now"):
            if len(low_df)==0:
                st.info("No low-stock items to include.")
            subject = f"[Inventory] {len(low_df)} low-stock items"
            body = "Low stock:\n" + low_df[["SKU","Name","Quantity","MinStock"]].to_string(index=False)
            ok, msg = send_email_alert(subject, body)
            st.write(msg)

    with st.expander("Webhook (optional)"):
        webhook_url = st.text_input("Webhook URL (Slack/Discord/your API)")
        if st.button("Send webhook test"):
            payload = {"type":"low_stock","count":int(len(low_df))}
            ok, msg = webhook_alert(webhook_url, payload)
            st.write(msg)
import os, datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# ======== Config ========
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# Ag-Grid (pro table)
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID = False

# ======== Dark theme & UI CSS ========
CSS = """
<style>
:root{
  --bg:#0b1020; --panel:#0f162b; --card:#121a33; --elev:#0e1529;
  --muted:#9aa6c1; --text:#e8eeff; --accent:#65b0ff; --ok:#22c55e; --warn:#f59e0b; --danger:#ef4444;
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg);}
.block-container{ padding-top: 1rem; }
.topbar{
  width:100%; position:sticky; top:0; z-index:100;
  background: linear-gradient(180deg, #111a33 0%, #0d152b 100%);
  border:1px solid #1b2a4a; border-radius:16px; padding:12px 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
.topbar-row{ display:flex; align-items:center; justify-content:space-between; gap:12px; }
.brand{ color:var(--text); font-weight:800; letter-spacing:.3px; display:flex; gap:.6rem; align-items:center}
.brand-badge{background:rgba(101,176,255,.15); color:#a7d1ff; padding:.25rem .5rem; border:1px solid #263a62; border-radius:999px; font-size:.75rem;}
.nav{ display:flex; gap:.4rem; }
.nav button{
  background: transparent; color:#cfe1ff; border:1px solid transparent;
  padding:.5rem .8rem; border-radius:10px; cursor:pointer; font-weight:600;
}
.nav button:hover{ background:rgba(101,176,255,.10); border-color:#263a62; }
.nav .active{ background:rgba(101,176,255,.18); border-color:#2a3f69; color:#eaf2ff; box-shadow:0 0 0 3px rgba(101,176,255,.25) inset; }
.banner{
  margin-top:.65rem; background:linear-gradient(180deg,#1c1409,#130f0a);
  color:#f7d9ac; border:1px dashed #3a2a14; border-radius:12px; padding:10px 12px;
}
.grid-4{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:12px;}
.card{ background: linear-gradient(180deg, #121a33 0%, #0f172c 100%); border:1px solid #1e2b49; border-radius:16px; padding:16px; box-shadow:0 10px 26px rgba(0,0,0,.35); }
.k-title{ color:#c2cdee; font-size:.9rem; font-weight:700; margin:0 0 .35rem 0;}
.k-value{ margin:0; font-size:1.9rem; font-weight:900;}
.k-note{ color:var(--muted); font-size:.8rem; }
.panel{ background: var(--card); border:1px solid #1c2948; border-radius:16px; padding:14px; }
.row{ display:grid; grid-template-columns: 2fr 1.2fr; gap:14px; margin-top:10px;}
.filterbar{ display:flex; gap:10px; align-items:center; }
hr{ border:none; border-top:1px solid #1a2746; margin:12px 0; }
.caption{ color:var(--muted); font-size:.85rem; }
.status-chip{
  padding:.18rem .55rem; border-radius:999px; font-size:.78rem; font-weight:700; letter-spacing:.2px;
  border:1px solid; display:inline-block
}
.chip-ok{ color:var(--ok); border-color: rgba(34,197,94,.25); background: rgba(34,197,94,.10); }
.chip-low{ color:var(--danger); border-color: rgba(239,68,68,.25); background: rgba(239,68,68,.10); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ======== Data IO ========
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
        if c not in df.columns: df[c] = np.nan
    return df[cols]

def save(df, path):
    df.to_csv(path, index=False)

# Required columns
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
low_df = P[P["Status"] == "Low"].copy()
inventory_value = float((P["Quantity"] * P["UnitPrice"]).sum())

# ======== Navigation ========
tabs = ["Dashboard","Inventory","Suppliers","Sales","Reports","Settings"]
if "tab" not in st.session_state: st.session_state.tab = "Dashboard"

# top nav
c = st.container()
with c:
    cols = st.columns([1,5,1])  # center nav bar
    with cols[1]:
        st.markdown('<div class="topbar"><div class="topbar-row">', unsafe_allow_html=True)
        st.markdown('<div class="brand">📦 Inventory Manager <span class="brand-badge">Dark</span></div>', unsafe_allow_html=True)
        # horizontal nav buttons
        nav_cols = st.columns(len(tabs))
        for i, t in enumerate(tabs):
            if nav_cols[i].button(t, key=f"nav_{t}", use_container_width=True):
                st.session_state.tab = t
        st.markdown('</div></div>', unsafe_allow_html=True)

tab = st.session_state.tab

# ======== Shared widgets ========
def kpi_card(title, value, note="", color="#eaf2ff"):
    st.markdown(
        f'<div class="card"><div class="k-title">{title}</div>'
        f'<p class="k-value" style="color:{color}">{value}</p>'
        f'<div class="k-note">{note}</div></div>', unsafe_allow_html=True
    )

def plotly_darkify(fig, h=420):
    fig.update_layout(
        template="plotly_dark", height=h, margin=dict(l=10,r=10,t=50,b=10),
        paper_bgcolor="#0f172c", plot_bgcolor="#0f172c", font_color="#e8eeff",
        xaxis=dict(gridcolor="#24385f"), yaxis=dict(gridcolor="#24385f"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    return fig

def aggrid_table(df, height=430):
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)
    # column groups + formatting examples
    if set(["Quantity","MinStock","UnitPrice"]).issubset(df.columns):
        gb.configure_column("Quantity", type=["numericColumn"])
        gb.configure_column("MinStock", type=["numericColumn"])
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
    grid = gb.build()
    AgGrid(df, gridOptions=grid, theme="balham-dark", height=height, fit_columns_on_grid_load=True)

# ======== PAGES ========

# 1) Dashboard
if tab == "Dashboard":
    if not low_df.empty:
        st.markdown(f'<div class="banner">⚠️ {len(low_df)} low-stock items need attention</div>', unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    with k1: kpi_card("Stock Items", f"{int(P['Quantity'].sum())}", "Units on hand")
    with k2: kpi_card("Low Stock", f"{len(low_df)}", "Below minimum", color="var(--danger)")
    with k3: kpi_card("Inventory Value", f"${inventory_value:,.2f}", "Qty × unit price", color="var(--accent)")
    with k4:
        mtd = 0.0
        if len(T):
            this_m = pd.Timestamp.utcnow().to_period("M")
            m = T[T["Timestamp"].dt.to_period("M")==this_m]
            mtd = float((m["Qty"]*m["UnitPrice"]).sum())
        kpi_card("Sales (MTD)", f"${mtd:,.2f}", "Month to date", color="var(--ok)")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    f1,f2,f3,f4 = st.columns([2,1,1,1])
    with f1: q = st.text_input("Search name or SKU", label_visibility="collapsed", placeholder="Search name or SKU")
    with f2: cat = st.selectbox("Category", ["All"]+sorted(P["Category"].dropna().unique()), index=0)
    with f3: status = st.selectbox("Status", ["All","OK","Low"], index=0)
    with f4: topn = st.selectbox("Top N", [10,20,50,100], index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    filt = P.copy()
    if q:
        filt = filt[filt["Name"].str.contains(q, case=False, na=False) | filt["SKU"].astype(str).str.contains(q, case=False, na=False)]
    if cat!="All": filt = filt[filt["Category"]==cat]
    if status!="All": filt = filt[filt["Status"]==status]

    left,right = st.columns([2,1.2])
    with left:
        if len(filt):
            fig = px.bar(filt.sort_values("Quantity", ascending=False).head(topn),
                         x="Name", y="Quantity", color="Category", title="Stock by Product (filtered)")
            st.plotly_chart(plotly_darkify(fig, 430), use_container_width=True)
        else:
            st.info("No items match filters.")
    with right:
        if len(P):
            v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum")).reset_index()
            fig2 = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory Value by Category")
            st.plotly_chart(plotly_darkify(fig2, 430), use_container_width=True)

    st.markdown("#### Low-stock list")
    if low_df.empty:
        st.success("All good — no low-stock items.")
    else:
        show = low_df[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice"]].copy()
        aggrid_table(show, height=360)

# 2) Inventory
elif tab == "Inventory":
    st.markdown("### Inventory")
    # status chips for preview
    preview = P.copy()
    preview["StatusChip"] = np.where(preview["Quantity"] < preview["MinStock"],
                                     '<span class="status-chip chip-low">LOW</span>',
                                     '<span class="status-chip chip-ok">OK</span>')
    st.markdown('<div class="caption">Click column headers to sort • Use filter rows in the table • Pagination enabled</div>', unsafe_allow_html=True)
    if AGGRID:
        df_show = preview[["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID","StatusChip"]].rename(columns={"StatusChip":"Status"})
        gb = GridOptionsBuilder.from_dataframe(df_show)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")
        gb.configure_column("Status", editable=False, cellRenderer="agGroupCellRenderer", cellRendererParams={"innerRenderer": "function(params){return params.value}"})
        grid = AgGrid(df_show, gridOptions=gb.build(), theme="balham-dark", height=520, allow_unsafe_jscode=True, update_mode=GridUpdateMode.VALUE_CHANGED)
        if st.button("💾 Save table", use_container_width=True):
            out = pd.DataFrame(grid["data"]).drop(columns=["Status"])
            save(out, P_CSV); st.success("Saved.")
    else:
        st.dataframe(preview, use_container_width=True, height=520)

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
        row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,"Quantity":int(qty),
               "MinStock":int(minq),"UnitPrice":float(unit),"Supplier_ID":sup}
        idx = P.index[P["Product_ID"].astype(str)==str(pid)]
        if len(idx): P.loc[idx[0]] = row; msg="Updated"
        else: P.loc[len(P)] = row; msg="Added"
        save(P, P_CSV); st.success(f"{msg} item.")

# 3) Suppliers
elif tab == "Suppliers":
    st.markdown("### Suppliers")
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(S)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
        grid = AgGrid(S, gridOptions=gb.build(), theme="balham-dark", height=480, update_mode=GridUpdateMode.VALUE_CHANGED)
        if st.button("💾 Save", use_container_width=True):
            save(pd.DataFrame(grid["data"]), S_CSV); st.success("Saved.")
    else:
        ed = st.data_editor(S, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save"): save(ed, S_CSV); st.success("Saved.")

# 4) Sales
elif tab == "Sales":
    st.markdown("### Record Sale")
    if len(P)==0:
        st.info("Add products first.")
    else:
        col1,col2,col3,col4 = st.columns(4)
        with col1: product = st.selectbox("Product", options=P["Name"])
        with col2: qty  = st.number_input("Qty", 1, step=1)
        with col3: price = st.number_input("UnitPrice ($)", 0.0, step=0.01, value=float(P.loc[P["Name"]==product,"UnitPrice"].values[0]))
        with col4: date  = st.date_input("Date", dt.date.today())
        if st.button("Add sale 🧾", use_container_width=True):
            pid = P.loc[P["Name"]==product,"Product_ID"].values[0]
            sid = f"S{int(pd.Timestamp.utcnow().timestamp())}"
            T.loc[len(T)] = [sid,pid,int(qty),float(price),pd.to_datetime(date)]
            idx = P.index[P["Product_ID"]==pid]
            if len(idx): P.loc[idx,"Quantity"] = (P.loc[idx,"Quantity"] - int(qty)).clip(lower=0)
            save(T, T_CSV); save(P, P_CSV); st.success("Recorded.")

    st.markdown("#### Recent Sales")
    if len(T):
        show = T.sort_values("Timestamp", ascending=False).head(250)
        aggrid_table(show, height=420)
    else:
        st.info("No sales yet.")

# 5) Reports
elif tab == "Reports":
    st.markdown("### Reports")
    if len(P):
        v = P.assign(Value=P["Quantity"]*P["UnitPrice"]).groupby("Category").agg(Value=("Value","sum"), Items=("Product_ID","count")).reset_index()
        fig = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory value by category")
        st.plotly_chart(plotly_darkify(fig, 430), use_container_width=True)
    if len(T):
        t = T.copy(); t["Revenue"]=t["Qty"]*t["UnitPrice"]; t["Month"]=t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        trend = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(trend, x="Month", y=["Units","Revenue"], markers=True, title="Sales trend")
        st.plotly_chart(plotly_darkify(fig2, 410), use_container_width=True)
    if not len(P) and not len(T):
        st.info("No data yet.")

# 6) Settings
elif tab == "Settings":
    st.markdown("### Data")
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
