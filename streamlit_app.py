# Small Business Inventory Manager — Streamlit
# Pages: Dashboard • Inventory • Suppliers • Sales • Barcode • Reports • Settings
# Data: CSV-backed (products.csv, suppliers.csv, sales.csv)
# Features: low-stock alerts, barcode scanning, editing, and visual reports

import os, io, datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional rich table
AGGRID = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
except Exception:
    AGGRID = False

# Optional barcode via webcam
WEBRTC = True
try:
    from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
    import av
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:
    WEBRTC = False
    try:
        from pyzbar.pyzbar import decode as zbar_decode
    except Exception:
        zbar_decode = None

# -------------------- App Config & Theme --------------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")
PRIMARY  = "#5B8DEF"
SUCCESS  = "#22C55E"
DANGER   = "#EF4444"
WARNING  = "#F59E0B"
MUTED    = "#6b7280"
CARD_CSS = """
<style>
.block-container {padding-top:1.2rem;}
.metric {background:#111827; border:1px solid #1f2937; border-radius:16px; padding:16px;}
.metric h3 {margin:0 0 6px 0; font-weight:600; color:#e5e7eb}
.metric .v {font-size:28px; font-weight:800;}
.badge {padding:.3rem .6rem; border-radius:999px; font-size:.8rem; margin-left:.5rem;}
.badge.warn {background:rgba(245,158,11,.15); color:#f59e0b; border:1px solid #f59e0b22}
.badge.ok {background:rgba(34,197,94,.15); color:#22c55e; border:1px solid #22c55e22}
.section-title{display:flex; align-items:center; gap:.6rem}
hr{border:none; border-top:1px solid #1f2937; margin:1rem 0}
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

# -------------------- Data layer (CSV) --------------------
DATA_DIR = "data"
P_CSV    = os.path.join(DATA_DIR, "products.csv")
S_CSV    = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV    = os.path.join(DATA_DIR, "sales.csv")

def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_csv(path, required=None):
    if not os.path.exists(path):
        return pd.DataFrame(columns=required or [])
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

def save_csv(df, path):
    _ensure_dir()
    df.to_csv(path, index=False)

def schema_products(df: pd.DataFrame) -> pd.DataFrame:
    # Enforce columns / defaults
    cols = ["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"]
    for c in cols:
        if c not in df.columns:
            df[c] = "" if c in ["SKU","Name","Category","Supplier_ID"] else 0
    # types
    for c in ["Quantity","MinStock"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ["UnitPrice"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df[cols]

def schema_suppliers(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Supplier_ID","Supplier_Name","Email","Phone"]
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df[cols]

def schema_sales(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"]
    for c in cols:
        if c not in df.columns:
            df[c] = 0 if c in ["Qty","UnitPrice"] else ""
    df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0).astype(int)
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0.0)
    # parse time
    def _parse(ts):
        try: return pd.to_datetime(ts)
        except: return pd.Timestamp.utcnow()
    df["Timestamp"] = df["Timestamp"].apply(_parse)
    return df[cols]

if "products" not in st.session_state:
    _ensure_dir()
    st.session_state.products  = schema_products(load_csv(P_CSV,
        ["Product_ID","SKU","Name","Category","Quantity","MinStock","UnitPrice","Supplier_ID"]))
    st.session_state.suppliers = schema_suppliers(load_csv(S_CSV, ["Supplier_ID","Supplier_Name","Email","Phone"]))
    st.session_state.sales     = schema_sales(load_csv(T_CSV, ["Sale_ID","Product_ID","Qty","UnitPrice","Timestamp"]))

P = st.session_state.products
S = st.session_state.suppliers
T = st.session_state.sales

# Convenience
def low_stock(df): return df[df["Quantity"] < df["MinStock"]]

# -------------------- Sidebar / Navigation --------------------
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", [
    "📊 Dashboard", "📦 Inventory", "🏷️ Suppliers", "🧾 Sales", "🧪 Barcode", "📈 Reports", "⚙️ Settings"
])

# -------------------- Components --------------------
def metric_card(title, value, color):
    st.markdown(f"""
    <div class="metric">
      <h3>{title}</h3>
      <div class="v" style="color:{color}">{value}</div>
    </div>""", unsafe_allow_html=True)

def grid_table(df):
    if AGGRID:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)
        gb.configure_side_bar()
        AgGrid(df, gridOptions=gb.build(), height=430, theme="balham", fit_columns_on_grid_load=True)
    else:
        st.dataframe(df, use_container_width=True)

# -------------------- Pages --------------------
if page == "📊 Dashboard":
    st.title("📦 Inventory Manager")
    st.caption("Business control center — stock, suppliers, sales.")

    total_items   = int(P["Quantity"].sum()) if len(P) else 0
    items_in_cat  = P["Category"].nunique()
    low_count     = len(low_stock(P))
    total_value   = float((P["Quantity"] * P["UnitPrice"]).sum())

    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Stock Items", f"{total_items}", PRIMARY)
    with c2: metric_card("Categories", f"{items_in_cat}", "#a78bfa")
    with c3: metric_card("Low Stock", f"{low_count}", DANGER)
    with c4: metric_card("Inventory Value", f"${total_value:,.2f}", SUCCESS)

    st.markdown("---")

    colA, colB = st.columns([2,1])
    with colA:
        if len(P):
            fig = px.bar(P.sort_values("Quantity",ascending=False).head(20),
                         x="Name", y="Quantity", color="Category", title="Stock by Product (Top 20)")
            fig.update_layout(margin=dict(l=10,r=10,t=50,b=10), height=420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No products yet.")

    with colB:
        st.markdown('<div class="section-title"><h3>Alerts</h3></div>', unsafe_allow_html=True)
        low_df = low_stock(P)
        if low_df.empty:
            st.markdown(f'<span class="badge ok">All good</span>', unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {len(low_df)} products below minimum stock")
            st.dataframe(low_df[["Product_ID","Name","Quantity","MinStock"]], use_container_width=True, height=300)

    st.markdown("---")

    # Simple trend from sales
    if len(T):
        t = T.copy()
        t["Month"] = t["Timestamp"].dt.to_period("M").dt.to_timestamp()
        t["Revenue"] = t["Qty"] * t["UnitPrice"]
        g = t.groupby("Month").agg(Units=("Qty","sum"), Revenue=("Revenue","sum")).reset_index()
        fig2 = px.line(g, x="Month", y=["Units","Revenue"], title="Sales Trend", markers=True)
        fig2.update_layout(margin=dict(l=10,r=10,t=50,b=10), height=380)
        st.plotly_chart(fig2, use_container_width=True)

elif page == "📦 Inventory":
    st.title("Inventory")
    tabs = st.tabs(["Table", "Add / Edit Item", "Low Stock"])

    with tabs[0]:
        grid_table(P)

    with tabs[1]:
        st.subheader("Add / Edit")
        with st.form("item_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                pid = st.text_input("Product_ID")
                sku = st.text_input("SKU / Barcode")
                name = st.text_input("Name")
            with col2:
                cat  = st.text_input("Category")
                qty  = st.number_input("Quantity", 0, step=1)
                minq = st.number_input("MinStock", 0, step=1)
            with col3:
                price = st.number_input("UnitPrice ($)", 0.0, step=0.01, format="%.2f")
                supp  = st.text_input("Supplier_ID")
            submitted = st.form_submit_button("Save Item ✅")

        if submitted:
            # upsert
            idx = P.index[P["Product_ID"].astype(str) == str(pid)]
            row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,
                   "Quantity":int(qty),"MinStock":int(minq),"UnitPrice":float(price),
                   "Supplier_ID":supp}
            if len(idx):
                P.loc[idx[0]] = row
                st.success("Updated item.")
            else:
                P.loc[len(P)] = row
                st.success("Added item.")
            save_csv(P, P_CSV)

    with tabs[2]:
        st.subheader("Low Stock")
        ls = low_stock(P)
        if ls.empty:
            st.success("No low-stock items 🎉")
        else:
            grid_table(ls)

elif page == "🏷️ Suppliers":
    st.title("Suppliers")
    c1, c2 = st.columns([3,2])
    with c1:
        grid_table(S)
    with c2:
        st.subheader("Add / Edit Supplier")
        with st.form("supplier_form", clear_on_submit=True):
            sid = st.text_input("Supplier_ID")
            sname = st.text_input("Supplier_Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            ok = st.form_submit_button("Save Supplier ✅")
        if ok:
            idx = S.index[S["Supplier_ID"].astype(str) == str(sid)]
            row = {"Supplier_ID":sid,"Supplier_Name":sname,"Email":email,"Phone":phone}
            if len(idx):
                S.loc[idx[0]] = row; st.success("Updated supplier.")
            else:
                S.loc[len(S)] = row; st.success("Added supplier.")
            save_csv(S, S_CSV)

elif page == "🧾 Sales":
    st.title("Sales")
    st.caption("Record sales and auto-update inventory.")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            prod = st.selectbox("Product", options=P["Name"])
        with col2:
            qty  = st.number_input("Qty", 1, step=1)
        with col3:
            unit = st.number_input("UnitPrice ($)", 0.0, step=0.01, value=float(P.loc[P["Name"]==prod,"UnitPrice"].values[0]) if len(P) else 0.0)
        with col4:
            ts   = st.date_input("Date", dt.date.today())
        ok = st.form_submit_button("Record Sale 🧾")
    if ok:
        pid = P.loc[P["Name"]==prod,"Product_ID"].values[0]
        sale_id = f"S{int(pd.Timestamp.utcnow().timestamp())}"
        new = {"Sale_ID":sale_id,"Product_ID":pid,"Qty":int(qty),"UnitPrice":float(unit),
               "Timestamp":pd.to_datetime(ts)}
        T.loc[len(T)] = new
        # decrease stock
        idx = P.index[P["Product_ID"]==pid]
        if len(idx):
            P.loc[idx, "Quantity"] = (P.loc[idx, "Quantity"] - int(qty)).clip(lower=0)
        save_csv(T, T_CSV); save_csv(P, P_CSV)
        st.success("Sale recorded and stock updated.")

    st.markdown("### Recent Sales")
    if len(T):
        grid_table(T.sort_values("Timestamp", ascending=False).head(200))
    else:
        st.info("No sales yet.")

elif page == "🧪 Barcode":
    st.title("Barcode / QR Tools")
    st.caption("Scan SKU/Barcode via webcam or image to find items quickly.")

    if WEBRTC and zbar_decode:
        st.subheader("Webcam Scanner")
        class Scanner(VideoTransformerBase):
            def transform(self, frame):
                img = frame.to_ndarray(format="bgr24")
                # just pass through; decoding is done separately
                return img

        ctx = webrtc_streamer(key="scanner", video_transformer_factory=Scanner, media_stream_constraints={"video": True, "audio": False})
        if ctx and ctx.video_receiver:
            frm = ctx.video_receiver.get_frame(timeout=1)
            if frm is not None:
                img = frm.to_ndarray(format="bgr24")
                codes = zbar_decode(img)
                if codes:
                    code = codes[0].data.decode("utf-8")
                    st.success(f"Detected code: **{code}**")
                    hit = P[P["SKU"].astype(str)==code]
                    if len(hit):
                        st.write("Match:")
                        st.write(hit)
                    else:
                        st.info("No product with this SKU yet.")
    else:
        st.info("Webcam scanning requires `streamlit-webrtc` and `pyzbar`. Falling back to image upload.")

    st.subheader("Upload Image to Decode")
    if zbar_decode:
        f = st.file_uploader("Upload barcode/QR image", type=["png","jpg","jpeg"])
        if f:
            import numpy as np
            from PIL import Image
            img = Image.open(f).convert("RGB")
            st.image(img, caption="Uploaded")
            codes = zbar_decode(np.array(img))
            if codes:
                code = codes[0].data.decode("utf-8")
                st.success(f"Detected code: **{code}**")
                hit = P[P["SKU"].astype(str)==code]
                if len(hit):
                    st.write("Match:")
                    st.write(hit)
                else:
                    st.info("No product with this SKU yet.")
            else:
                st.error("No barcode/QR detected.")
    else:
        st.warning("Install `pyzbar` to enable image decoding.")

elif page == "📈 Reports":
    st.title("Reports")
    if len(P):
        st.subheader("Inventory Value by Category")
        P["Value"] = P["Quantity"] * P["UnitPrice"]
        cat = P.groupby("Category").agg(Total_Value=("Value","sum"), Items=("Product_ID","count")).reset_index()
        fig = px.bar(cat, x="Category", y="Total_Value", text_auto=".2s", title="Value by Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No products.")

    st.markdown("---")
    if len(T):
        st.subheader("Top Products by Revenue")
        T["Revenue"] = T["Qty"] * T["UnitPrice"]
        g = T.merge(P[["Product_ID","Name"]], on="Product_ID", how="left").groupby("Name").agg(Revenue=("Revenue","sum"), Units=("Qty","sum")).reset_index().sort_values("Revenue", ascending=False)
        st.dataframe(g.head(20), use_container_width=True)
    else:
        st.info("No sales to report.")

elif page == "⚙️ Settings":
    st.title("Settings")
    st.caption("Upload CSVs, export copies, and tweak low-stock rules.")

    st.subheader("Load / Replace Data")
    pu = st.file_uploader("Products CSV", type=["csv"], key="p_upload")
    su = st.file_uploader("Suppliers CSV", type=["csv"], key="s_upload")
    tu = st.file_uploader("Sales CSV", type=["csv"], key="t_upload")

    if st.button("Import Uploaded Files"):
        if pu:
            P_new = schema_products(pd.read_csv(pu))
            st.session_state.products = P_new; save_csv(P_new, P_CSV)
        if su:
            S_new = schema_suppliers(pd.read_csv(su))
            st.session_state.suppliers = S_new; save_csv(S_new, S_CSV)
        if tu:
            T_new = schema_sales(pd.read_csv(tu))
            st.session_state.sales = T_new; save_csv(T_new, T_CSV)
        st.success("Imported.")

    st.subheader("Export Current Data")
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ Products CSV", st.session_state.products.to_csv(index=False).encode("utf-8"), "products_export.csv", "text/csv")
    c2.download_button("⬇️ Suppliers CSV", st.session_state.suppliers.to_csv(index=False).encode("utf-8"), "suppliers_export.csv", "text/csv")
    c3.download_button("⬇️ Sales CSV", st.session_state.sales.to_csv(index=False).encode("utf-8"), "sales_export.csv", "text/csv")

    st.markdown("---")
    st.info("Next step: connect a real database (Postgres/Firebase) and auth if you want multi-user access.")
