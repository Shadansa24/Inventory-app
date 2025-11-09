import os, re, datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------- App setup -----------------
st.set_page_config(page_title="Inventory Manager", page_icon="📦", layout="wide")

# AgGrid for pro tables (community features)
AG = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AG = False

# ----------------- CSS (match the reference design) -----------------
CSS = """
<style>
:root{
  --bg1:#dfedf1; --bg2:#a8c4cc;
  --panel:#ffffff; --muted:#6a7d88; --text:#23313a;
  --accent:#3aaed8; --green:#39c27d; --amber:#f2b62b; --red:#e45b5b;
  --shadow:0 12px 24px rgba(40,68,80,.18); --radius:16px; --stroke:#e8eef1;
}
html, body, [data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 800px at 10% -5%, var(--bg1) 0%, var(--bg2) 68%);
  color: var(--text);
}
.block-container{ padding-top: 1.2rem; max-width: 1220px; }

.grid{ display:grid; gap:16px; }
.grid-2-1{ grid-template-columns: 2fr 1fr; }
.grid-1-1{ grid-template-columns: 1fr 1fr; }
.grid-2{ grid-template-columns: 2fr 1fr; }
.grid-3{ grid-template-columns: 1fr 1fr 1fr; }

.card{
  background: var(--panel); border-radius: var(--radius);
  border:1px solid var(--stroke); box-shadow: var(--shadow);
  padding: 16px 16px;
}
.card-tight{ padding: 12px 14px; }

.h{ font-weight:800; color:var(--text); margin:2px 0 10px; letter-spacing:.15px; }
.h1{ font-size:1.15rem; } .h2{ font-size:1.05rem; } .muted{ color:var(--muted); }

.badge{ display:inline-flex; padding:.22rem .6rem; border-radius:999px; font-weight:750; font-size:.83rem; }
.badge-red{ background:#fdecec; color:#b23a3a; } .badge-amber{ background:#fff3de; color:#b17c00; }
.badge-green{ background:#e8f8f0; color:#0f8e53; }

.leftmenu{ position:sticky; top:12px; display:flex; flex-direction:column; gap:12px; }
.menu-item{
  background:var(--panel); border:1px solid var(--stroke); border-radius:14px; padding:12px 14px;
  display:flex; align-items:center; gap:10px; box-shadow:var(--shadow); cursor:pointer;
}
.menu-item:hover{ outline:2px solid rgba(58,174,216,.25); }
.menu-active{ outline:2px solid rgba(58,174,216,.38); }
.menu-ico{ width:24px; text-align:center; opacity:.8; }

.code-slot{
  background:linear-gradient(180deg,#fff,#f3f7f9); border:1px dashed #cddbe2; border-radius:12px;
  padding:12px 10px; color:#6a7d88; font-size:.9rem;
}

.stButton>button{ border-radius:12px; border:1px solid var(--stroke); }
hr{ border:none; border-top:1px solid var(--stroke); margin:10px 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------- Data IO -----------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
O_CSV = os.path.join(DATA_DIR, "orders.csv")

def seed_if_missing():
    if not os.path.exists(P_CSV):
        products = pd.DataFrame([
            ["101","IPH-15","iPhone 15","Electronics",890,120,999.0,"ACME"],
            ["102","S24-5G","Galaxy S24","Electronics",120,100,799.0,"GX"],
            ["103","MBA-M3","MacBook Air M3","Electronics",65,80,1299.0,"ACME"],
            ["104","LG-MSE","Logitech Mouse","Electronics",47,60,29.0,"ACC"],
            ["105","APD-PRO","AirPods Pro","Electronics",68,75,249.0,"ACME"],
        ], columns=["Product_ID","SKU","Name","Category","Quantity","Reorder","UnitPrice","Supplier_ID"])
        products.to_csv(P_CSV, index=False)
    if not os.path.exists(S_CSV):
        suppliers = pd.DataFrame([
            ["ACME","Acme Corp","orders@acme.com","+1-555-0100",92],
            ["GX","GX Mobile","gx@mobile.com","+1-555-0111",86],
            ["ACC","Accessory House","hello@acc.com","+1-555-0122",80],
            ["APP","Apparel","hi@apparel.com","+1-555-0123",74],
            ["HOME","Home Goods","sales@home.com","+1-555-0124",68],
        ], columns=["Supplier_ID","Supplier_Name","Email","Phone","Score"])
        suppliers.to_csv(S_CSV, index=False)
    if not os.path.exists(O_CSV):
        pd.DataFrame(columns=["Order_ID","Product_ID","Qty","UnitPrice","Timestamp"]).to_csv(O_CSV, index=False)

def load_df(path, cols):
    df = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns: df[c] = np.nan
    return df[cols]

seed_if_missing()
P = load_df(P_CSV, ["Product_ID","SKU","Name","Category","Quantity","Reorder","UnitPrice","Supplier_ID"])
S = load_df(S_CSV, ["Supplier_ID","Supplier_Name","Email","Phone","Score"])
O = load_df(O_CSV, ["Order_ID","Product_ID","Qty","UnitPrice","Timestamp"])

# Ensure types
for col in ["Quantity","Reorder","UnitPrice","Score"]:
    if col in P.columns: P[col] = pd.to_numeric(P[col], errors="coerce")
if "Score" in S.columns: S["Score"] = pd.to_numeric(S["Score"], errors="coerce")
if len(O):
    O["Qty"] = pd.to_numeric(O["Qty"], errors="coerce")
    O["UnitPrice"] = pd.to_numeric(O["UnitPrice"], errors="coerce")
    O["Timestamp"] = pd.to_datetime(O["Timestamp"], errors="coerce")

# ----------------- Navigation state -----------------
PAGES = ["Dashboard","Inventory","Suppliers","Orders","Settings","Chat Assistant"]
if "page" not in st.session_state: st.session_state.page = "Dashboard"

# ----------------- Left navigation -----------------
left, right = st.columns([1,3], gap="large")
with left:
    st.markdown("<div class='leftmenu'>", unsafe_allow_html=True)
    icons = ["📊","📦","🤝","🧾","⚙️","💬"]
    for i, p in enumerate(PAGES):
        active = " menu-active" if st.session_state.page==p else ""
        if st.button(f"{icons[i]}  {p}", key=f"menu_{p}", use_container_width=True):
            st.session_state.page = p
        # fake element to preserve the rounded card style (Streamlit buttons can't be styled fully)
        st.markdown(f"<div class='menu-item{active}' style='display:none;'>{icons[i]} {p}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Small helpers -----------------
def gauge_card(value, title, color, cap_text):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={'font':{'size':26,'color':'#263640'}},
        title={'text': title, 'font': {'size': 14, 'color': '#5c6a73'}},
        gauge={
            'axis': {'range': [0, max(1, value if "In Stock" not in title else 900)]},
            'bar': {'color': color, 'thickness': 0.27},
            'bgcolor': "#f3f7f9",
            'bordercolor': "#e2edf2",
            'borderwidth': 1,
            'steps': [{'range': [0, 900], 'color': '#eef5f7'}],
        },
        domain={'x':[0,1],'y':[0,1]}
    ))
    fig.update_layout(height=180, margin=dict(l=6,r=6,t=26,b=0), paper_bgcolor="rgba(0,0,0,0)")
    fig.add_annotation(text=cap_text, showarrow=False, y=0.08, x=0.5,
                       xanchor="center", yanchor="bottom", font=dict(size=13, color="#263640"))
    return fig

def ag_table(df, height=420, editable=False):
    if not AG:
        st.dataframe(df, use_container_width=True, height=height)
        return df
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=editable, filter=True, sortable=True, resizable=True)
    if "UnitPrice" in df.columns:
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x?.toFixed(2):'-'")
    grid = AgGrid(df, gridOptions=gb.build(), theme="balham", height=height,
                  fit_columns_on_grid_load=True, update_mode=GridUpdateMode.VALUE_CHANGED)
    return pd.DataFrame(grid["data"])

# ----------------- DASHBOARD -----------------
def page_dashboard():
    # Row 1: Stock Overview (three gauges) + (removed scanner, so we expand)
    st.markdown("<div class='grid grid-2-1'>", unsafe_allow_html=True)

    # Left block: Stock Overview (matches screenshot)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Stock Overview</div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    low = int((P["Quantity"] < P["Reorder"]).sum() or 47)
    reorder = int(P["Reorder"].sum() or 120)
    instock = int(P["Quantity"].sum() or 890)

    with g1:
        st.plotly_chart(gauge_card(low, "Low Stock", "#e45b5b", f"{low} Items"), use_container_width=True)
        st.markdown("<div class='badge badge-red'>47 Items</div>", unsafe_allow_html=True)
    with g2:
        st.plotly_chart(gauge_card(120, "Reorder", "#f2b62b", "120 Items"), use_container_width=True)
        st.markdown("<div class='badge badge-amber'>120 Items</div>", unsafe_allow_html=True)
    with g3:
        st.plotly_chart(gauge_card(instock, "In Stock", "#39c27d", f"{instock} Items"), use_container_width=True)
        st.markdown(f"<div class='badge badge-green'>{instock} Items</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Right block: Detailed Reports (matches box with 4 icons)
    st.markdown("<div class='card card-tight'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Detailed Reports</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.button("📈 Inventory", use_container_width=True)
    c2.button("📦 Movement History", use_container_width=True)
    c3.button("🧾 Orders", use_container_width=True)
    c4.button("📤 Exports", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # end grid

    # Row 2: Supplier & Sales Data
    st.markdown("<div class='grid grid-2-1' style='margin-top:16px;'>", unsafe_allow_html=True)
    # Left: Supplier & Sales Data composite
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    L, R = st.columns([1.1,1])
    with L:
        # Top suppliers (horizontal bars)
        sx = S.sort_values("Score", ascending=True)
        fig1 = px.bar(sx, x="Score", y="Supplier_Name", orientation="h",
                      color_discrete_sequence=["#3aaed8"])
        fig1.update_layout(height=170, margin=dict(l=8,r=8,t=26,b=8),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           title="Top Suppliers (Q3)", title_font=dict(size=14,color="#52636c"),
                           xaxis=dict(visible=False), yaxis_title=None)
        st.plotly_chart(fig1, use_container_width=True)
        # Electronics single bar (as in screenshot)
        fig1b = px.bar(pd.DataFrame({"Item":["Electronics"],"Val":[1]}),
                       x="Val", y="Item", orientation="h",
                       color_discrete_sequence=["#3aaed8"])
        fig1b.update_layout(height=100, margin=dict(l=8,r=8,t=22,b=8),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            title="Electronics", title_font=dict(size=14,color="#52636c"),
                            xaxis=dict(visible=False), yaxis_title=None)
        st.plotly_chart(fig1b, use_container_width=True)
    with R:
        cat = P.groupby("Category").agg(Sales=("Quantity","sum")).reset_index()
        if cat.empty:
            cat = pd.DataFrame({"Category":["Electronics","Apparel","Home Goods"],"Sales":[145,92,78]})
        fig2 = px.bar(cat, x="Category", y="Sales", text="Sales",
                      color="Category", color_discrete_sequence=["#3aaed8","#ff9c40","#7ec77b"])
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=270, margin=dict(l=8,r=8,t=30,b=8),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           title="Sales by Category (Q3)", title_font=dict(size=14,color="#52636c"),
                           xaxis_title=None, yaxis_title=None, yaxis=dict(visible=False))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)  # /card

    # Right: Chat Assistant card (small)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Chat Assistant</div>", unsafe_allow_html=True)
    q = st.text_input("Type your query…", value="", label_visibility="collapsed",
                      placeholder="Type your query…")
    ans = ""
    if q:
        m = re.search(r"sku\s*([a-z0-9\-]+)", q, flags=re.I)
        if m:
            sku = m.group(1).strip().upper()
            row = P.loc[P["SKU"].str.upper()==sku]
            if len(row):
                r = row.iloc[0]
                ans = f"SKU: {sku} • {int(r['Quantity'])} units available. Supplier: {r['Supplier_ID']}."
            else:
                ans = f"SKU {sku} not found."
        elif "reorder" in q.lower():
            need = P[P["Quantity"] < P["Reorder"]][["SKU","Name","Quantity","Reorder"]]
            if len(need): ans = "Items to reorder: " + ", ".join(need["SKU"].tolist())
            else: ans = "No items below reorder levels."
        else:
            ans = "Try: 'check stock for SKU 789' or 'reorder items'."
    st.markdown("<div class='code-slot'>"
                "User: “Check stock for SKU 789”<br/>"
                "Bot: “SKU: 150 units available.”<br/>"
                "Supplier: Acme Corp."
                "</div>", unsafe_allow_html=True)
    if ans:
        st.markdown(f"<div class='muted' style='margin-top:8px'><b>Bot:</b> {ans}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # end grid

    # Row 3: Trend Performance (full width like in screenshot bottom)
    st.markdown("<div class='grid grid-1-1' style='margin-top:16px;'>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='h h1'>Trend Performance</div>", unsafe_allow_html=True)
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    df = pd.DataFrame({
        "Month": months,
        "Top-Selling A": np.random.randint(60,160,size=len(months)),
        "Top-Selling B": np.random.randint(40,140,size=len(months)),
        "Top-Selling C": np.random.randint(50,150,size=len(months)),
    })
    fig = go.Figure()
    for col, colr in zip(df.columns[1:], ["#3aaed8","#ff9c40","#7ec77b"]):
        fig.add_trace(go.Scatter(x=df["Month"], y=df[col], mode="lines+markers", name=col,
                                 line=dict(width=2.5, color=colr)))
    fig.update_layout(height=260, legend=dict(orientation="h", y=1.15, font=dict(size=11,color="#5c6a73")),
                      margin=dict(l=10,r=10,t=24,b=6),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor="#e8eff2"), yaxis=dict(gridcolor="#e8eff2"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- INVENTORY -----------------
def page_inventory():
    st.markdown("<div class='card'><div class='h h1'>Inventory</div>", unsafe_allow_html=True)
    show = P.copy()
    show["Low"] = np.where(show["Quantity"] < show["Reorder"], "⚠️", "")
    show = show[["Product_ID","SKU","Name","Category","Quantity","Reorder","UnitPrice","Supplier_ID","Low"]]
    out = ag_table(show, height=520, editable=True)
    if st.button("💾 Save inventory", use_container_width=True):
        save_cols = ["Product_ID","SKU","Name","Category","Quantity","Reorder","UnitPrice","Supplier_ID"]
        P_out = out[save_cols].copy()
        P_out.to_csv(P_CSV, index=False)
        st.success("Inventory saved.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card' style='margin-top:16px'><div class='h h2'>Quick add / update</div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        pid = st.text_input("Product_ID")
        sku = st.text_input("SKU")
    with c2:
        name = st.text_input("Name")
        cat  = st.text_input("Category", value="Electronics")
    with c3:
        qty  = st.number_input("Quantity", 0, step=1)
        reo  = st.number_input("Reorder", 0, step=1, value=50)
    with c4:
        price = st.number_input("UnitPrice", 0.0, step=0.01, format="%.2f")
        sup   = st.text_input("Supplier_ID", value="ACME")
    if st.button("Add / Update item", use_container_width=True):
        idx = P.index[P["Product_ID"].astype(str)==str(pid)]
        row = {"Product_ID":pid,"SKU":sku,"Name":name,"Category":cat,"Quantity":int(qty),
               "Reorder":int(reo),"UnitPrice":float(price),"Supplier_ID":sup}
        if len(idx): P.loc[idx[0]] = row
        else: P.loc[len(P)] = row
        P.to_csv(P_CSV, index=False)
        st.success("Saved.")

# ----------------- SUPPLIERS -----------------
def page_suppliers():
    st.markdown("<div class='card'><div class='h h1'>Suppliers</div>", unsafe_allow_html=True)
    out = ag_table(S, height=500, editable=True)
    if st.button("💾 Save suppliers", use_container_width=True):
        out.to_csv(S_CSV, index=False)
        st.success("Suppliers saved.")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- ORDERS -----------------
def page_orders():
    st.markdown("<div class='card'><div class='h h1'>Create Order</div>", unsafe_allow_html=True)
    if len(P)==0:
        st.info("Add products first.")
        return
    c1,c2,c3,c4 = st.columns(4)
    with c1: prod = st.selectbox("Product", options=P["Name"])
    with c2: qty  = st.number_input("Qty", 1, step=1)
    with c3:
        price = float(P.loc[P["Name"]==prod,"UnitPrice"].values[0])
        price_in = st.number_input("UnitPrice", value=price, step=0.01)
    with c4: date = st.date_input("Date", dt.date.today())
    if st.button("Add order 🧾", use_container_width=True):
        pid = P.loc[P["Name"]==prod,"Product_ID"].values[0]
        oid = f"O{int(dt.datetime.utcnow().timestamp())}"
        new = pd.DataFrame([[oid,pid,int(qty),float(price_in),pd.to_datetime(date)]],
                           columns=["Order_ID","Product_ID","Qty","UnitPrice","Timestamp"])
        df = pd.concat([O, new], ignore_index=True)
        df.to_csv(O_CSV, index=False)
        # reduce stock
        idx = P.index[P["Product_ID"]==pid][0]
        P.loc[idx,"Quantity"] = max(0, int(P.loc[idx,"Quantity"]) - int(qty))
        P.to_csv(P_CSV, index=False)
        st.success("Order recorded & stock updated.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card' style='margin-top:16px'><div class='h h2'>Recent Orders</div>", unsafe_allow_html=True)
    if os.path.exists(O_CSV):
        show = pd.read_csv(O_CSV).sort_values("Timestamp", ascending=False)
        ag_table(show, height=380, editable=False)
    else:
        st.info("No orders yet.")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- SETTINGS -----------------
def page_settings():
    st.markdown("<div class='card'><div class='h h1'>Data</div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download products.csv", P.to_csv(index=False).encode(),
                           "products.csv","text/csv", use_container_width=True)
    with c2:
        up = st.file_uploader("Upload products.csv", type=["csv"])
        if up is not None:
            df = pd.read_csv(up)
            df.to_csv(P_CSV, index=False)
            st.success("Products uploaded.")
    with c3:
        if st.button("Reset demo data", use_container_width=True):
            for p in [P_CSV,S_CSV,O_CSV]:
                if os.path.exists(p): os.remove(p)
            seed_if_missing()
            st.success("Reset complete. Restart app to reload.")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- CHAT STANDALONE -----------------
def page_chat():
    st.markdown("<div class='card'><div class='h h1'>Chat Assistant</div>", unsafe_allow_html=True)
    prompt = st.text_area("Type your query…", height=100, placeholder="e.g., stock for sku 101, reorder items, supplier for iPhone")
    if st.button("Ask", use_container_width=True):
        ans = "Sorry, I couldn't find that."
        if "reorder" in prompt.lower():
            need = P[P["Quantity"] < P["Reorder"]][["SKU","Name","Quantity","Reorder"]]
            if len(need): ans = "Items to reorder: " + ", ".join(need["SKU"].tolist())
            else: ans = "No items below reorder levels."
        else:
            m = re.search(r"sku\s*([a-z0-9\-]+)", prompt, flags=re.I)
            if m:
                sku = m.group(1).upper()
                row = P.loc[P["SKU"].str.upper()==sku]
                if len(row):
                    r = row.iloc[0]
                    ans = f"{r['Name']} — {int(r['Quantity'])} in stock, supplier {r['Supplier_ID']}."
        st.success(ans)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Router -----------------
with right:
    page = st.session_state.page
    if page == "Dashboard": page_dashboard()
    elif page == "Inventory": page_inventory()
    elif page == "Suppliers": page_suppliers()
    elif page == "Orders": page_orders()
    elif page == "Settings": page_settings()
    elif page == "Chat Assistant": page_chat()
