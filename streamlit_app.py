import re
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Inventory Management System",
    page_icon="📦",
    layout="wide"
)

# ──────────────────────────────────────────────────────────────────────────────
# Sky-blue theme + card styling
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* App background */
[data-testid="stAppViewContainer"]{
  background: linear-gradient(180deg, #d9edf7 0%, #c9e2f3 30%, #b9d6e8 100%);
}

/* Hide default top padding a bit */
.block-container{padding-top: 1.2rem; padding-bottom: 2rem;}

/* Cards */
.card{
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(0,0,0,.08);
  padding: 1.1rem 1.25rem;
}

/* Metric headline */
.kpi-title{
  color:#4b5b6a; font-weight:600; font-size:.95rem; margin-bottom:.35rem;
}
.kpi-value{
  font-size:2.0rem; font-weight:700; line-height:1; color:#1f2d3d;
}
.kpi-sub{
  font-size:.9rem; color:#6b7b8c;
}

/* Option menu tweaks */
div[data-testid="stSidebar"] {background: transparent;}
.nav-card{
  background: rgba(255,255,255,.85);
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0,0,0,.05);
  padding: .75rem .9rem;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file: str):
    if file.lower().endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)
    return df

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    # map flexible column names → canonical
    lc = {c.lower(): c for c in df.columns}
    rename = {}
    mapping = {
        'product_id': ['product_id','id','productid','prod_id'],
        'sku': ['sku','code'],
        'name': ['name','product','product_name','item'],
        'category': ['category','cat'],
        'quantity': ['quantity','qty','stock','onhand','on_hand'],
        'minstock': ['minstock','threshold','reorder_point','min_stock'],
        'unitprice': ['unitprice','price','unit_price','cost'],
        'supplier': ['supplier','vendor']
    }
    for target, alts in mapping.items():
        for a in alts:
            if a in lc:
                rename[lc[a]] = target
                break
    df = df.rename(columns=rename)
    # fill missing required fields if absent
    for req in ['product_id','sku','name','category','quantity','minstock','unitprice','supplier']:
        if req not in df.columns:
            df[req] = np.nan
    # types
    for c in ['quantity','minstock','unitprice']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    df['name'] = df['name'].astype(str)
    df['category'] = df['category'].astype(str)
    df['supplier'] = df['supplier'].astype(str)
    return df

def load_inventory():
    # Try default file names; else show uploader
    default = None
    for f in ("products.csv","products.xlsx"):
        try:
            df = normalize_cols(load_data(f))
            default = df
            break
        except Exception:
            pass
    up = st.sidebar.file_uploader("Upload inventory (CSV or Excel)", type=["csv","xlsx"], label_visibility="collapsed")
    if up is not None:
        df = normalize_cols(load_data(up.name)) if isinstance(up, str) else normalize_cols(pd.read_excel(up) if up.name.endswith(".xlsx") else pd.read_csv(up))
        return df
    if default is not None:
        return default
    # fallback sample
    sample = pd.DataFrame({
        "product_id":[101,102,103,104,105],
        "sku":["IPH-15","GS24","MBA-M3","LG-MSE","AP-PR2"],
        "name":["iPhone 15","Galaxy S24","MacBook Air M3","Logitech Mouse","AirPods Pro"],
        "category":["Mobile","Mobile","Laptop","Accessory","Accessory"],
        "quantity":[12,30,5,3,20],
        "minstock":[15,8,8,5,5],
        "unitprice":[999,899,1299,29,249],
        "supplier":["ACME","GX","ACME","ACC","ACME"]
    })
    return sample

df = load_inventory()

# derived flags
df['low_flag'] = (df['quantity'] < df['minstock'])
df['in_stock_flag'] = ~df['low_flag']

# KPIs
total_items = int(df['quantity'].sum())
low_count = int(df['low_flag'].sum())
reorder_count = low_count
in_stock_count = int(df['in_stock_flag'].sum())

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Inventory", "Suppliers", "Orders", "Settings", "Chat Assistant"],
        icons=["speedometer2","box-seam","people","receipt","gear","chat-dots"],
        default_index=0,
        styles={
            "container": {"padding":"0","background":"transparent"},
            "icon": {"color":"#3b4f66"},
            "nav-link": {"font-size":"15px","--hover-color":"#eaf2f9"},
            "nav-link-selected": {"background-color":"#d9e9f7", "font-weight":"600"},
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Reusable UI blocks
# ──────────────────────────────────────────────────────────────────────────────
def kpi_card(title, value, sub=""):
    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def stock_overview_cards(df):
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("Stock Items", f"{len(df):,}", "distinct products")
    with c2: kpi_card("Low Stock", f"{(df['low_flag']).sum():,}", "below minimum")
    with c3: kpi_card("Reorder Needed", f"{(df['low_flag']).sum():,}", "order these")
    with c4: kpi_card("In Stock", f"{(df['in_stock_flag']).sum():,}", "OK level")

def sales_by_category_chart(df):
    # proxy "value" = quantity * unitprice
    dcat = df.groupby("category", dropna=False).agg(
        Units=("quantity","sum"),
        Value=("unitprice", lambda s: float((s*0+1).sum())) # placeholder
    ).reset_index()
    dcat["Value"] = (df.groupby("category")["quantity"].sum() * df.groupby("category")["unitprice"].mean()).reindex(dcat["category"]).values
    fig = px.bar(dcat, x="Units", y="category", orientation="h",
                 color_discrete_sequence=["#1f77b4"])
    fig.update_layout(height=340, margin=dict(l=8,r=8,t=40,b=8),
                      xaxis_title="Units", yaxis_title="", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")
    return fig

def trend_chart(df):
    # fake monthly trend from totals (so chart always shows something)
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    base = df["quantity"].sum()
    series_a = np.linspace(base*0.2, base*0.5, 6).astype(int)
    series_b = np.linspace(base*0.15, base*0.45, 6).astype(int)
    tdf = pd.DataFrame({"Month":months,"Product A":series_a,"Product B":series_b})
    tdf = tdf.melt("Month", var_name="Product", value_name="Units")
    fig = px.line(tdf, x="Month", y="Units", color="Product",
                  color_discrete_sequence=["#1f77b4","#ff7f0e"])
    fig.update_traces(mode="lines+markers")
    fig.update_layout(height=380, margin=dict(l=8,r=8,t=30,b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# Chat Assistant (rule-based over your dataframe)
# ──────────────────────────────────────────────────────────────────────────────
def answer_question(q: str, df: pd.DataFrame) -> str:
    ql = q.lower().strip()

    # 1) list low stock
    if re.search(r"\blow stock\b|\bbelow (min|minimum)\b|\breorder\b", ql):
        lows = df[df["low_flag"]][["product_id","sku","name","quantity","minstock","supplier"]]
        if lows.empty:
            return "No items are currently below minimum stock."
        rows = [f"- {r.name}: qty {int(r.quantity)} / min {int(r.minstock)} (SKU {r.sku}, supplier {r.supplier})"
                for _, r in lows.set_index("name").iterrows()]
        return "Low stock items:\n" + "\n".join(rows)

    # 2) quantity / id for a given product name or SKU
    m = re.search(r"(qty|quantity|how many|stock) (for|of) ([\w\- ]+)", ql)
    if m:
        key = m.group(3).strip()
        hit = df[(df["name"].str.lower().str.contains(key)) | (df["sku"].str.lower()==key)]
        if hit.empty:
            return f"I couldn't find '{key}'. Try product name or exact SKU."
        r = hit.iloc[0]
        return f"{r['name']} (SKU {r['sku']}): quantity {int(r['quantity'])}, min {int(r['minstock'])}, supplier {r['supplier']}."
    
    # 3) supplier of X
    m = re.search(r"(supplier|vendor) (for|of) ([\w\- ]+)", ql)
    if m:
        key = m.group(3).strip()
        hit = df[df["name"].str.lower().str.contains(key)]
        if hit.empty:
            return f"No supplier found for '{key}'."
        r = hit.iloc[0]
        return f"Supplier for {r['name']} is {r['supplier']}."

    # 4) id / sku of X
    m = re.search(r"(id|sku) (for|of) ([\w\- ]+)", ql)
    if m:
        key = m.group(3).strip()
        hit = df[df["name"].str.lower().str.contains(key)]
        if hit.empty:
            return f"I can't find the SKU/ID for '{key}'."
        r = hit.iloc[0]
        return f"{r['name']} → SKU {r['sku']}, Product_ID {r['product_id']}."

    # 5) price of X
    m = re.search(r"(price|cost) (for|of) ([\w\- ]+)", ql)
    if m:
        key = m.group(3).strip()
        hit = df[df["name"].str.lower().str.contains(key)]
        if hit.empty:
            return f"No price info for '{key}'."
        r = hit.iloc[0]
        return f"{r['name']} unit price is ${float(r['unitprice']):,.2f}."

    return "I didn't understand. Try: 'low stock', 'quantity of iPhone', 'supplier of AirPods', 'price of MacBook', or 'sku for logitech mouse'."

# ──────────────────────────────────────────────────────────────────────────────
# PAGES
# ──────────────────────────────────────────────────────────────────────────────
if selected == "Dashboard":
    st.markdown("## Inventory Management Dashboard")
    # search bar (decorative spacer like your reference)
    st.markdown('<div class="card" style="height:22px; opacity:.65;"></div>', unsafe_allow_html=True)

    # Row 1: KPIs
    stock_overview_cards(df)

    # Row 2: charts + chat
    left, right = st.columns([2.1, 1], gap="large")
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Supplier & Sales Data")
        # stacked horiz by supplier per category
        # Build a long dataframe
        dd = df.groupby(['category','supplier'], dropna=False)['quantity'].sum().reset_index()
        fig = px.bar(dd, x="quantity", y="category", color="supplier",
                     orientation="h", text="quantity",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition="outside")
        fig.update_layout(height=360, margin=dict(l=8,r=8,t=40,b=8),
                          xaxis_title="Sales / Units", yaxis_title="",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card" style="margin-top:1rem;">', unsafe_allow_html=True)
        st.subheader("Trend Performance — Top-Selling Products")
        st.plotly_chart(trend_chart(df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Chat Assistant (functional)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Chat Assistant")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        q = st.text_input("Ask about stock, SKU, supplier, price…", key="chat_input")
        if q:
            st.session_state.chat_history.append(("You", q))
            st.session_state.chat_history.append(("Bot", answer_question(q, df)))
            st.rerun()
        for who, msg in st.session_state.chat_history[-8:]:
            st.markdown(f"**{who}:** {msg}")
        st.markdown('</div>', unsafe_allow_html=True)

elif selected == "Inventory":
    st.markdown("## Inventory")
    st.dataframe(
        df[['product_id','sku','name','category','quantity','minstock','unitprice','supplier','low_flag']]
        .rename(columns={'product_id':'Product_ID','sku':'SKU','name':'Name',
                         'category':'Category','quantity':'Quantity','minstock':'MinStock',
                         'unitprice':'UnitPrice','supplier':'Supplier','low_flag':'Low?'}),
        use_container_width=True, height=420
    )
    st.info("Tip: items with **Low? = True** need reordering.")

elif selected == "Suppliers":
    st.markdown("## Suppliers")
    s = (df.groupby('supplier', dropna=False)
           .agg(Products=('product_id','nunique'),
                Units=('quantity','sum'))
           .reset_index()
        )
    st.dataframe(s, use_container_width=True, height=360)

elif selected == "Orders":
    st.markdown("## Orders")
    st.info("Hook this to your orders table when ready.")

elif selected == "Settings":
    st.markdown("## Settings")
    st.info("Add your app options here.")

elif selected == "Chat Assistant":
    st.markdown("## Chat Assistant")
    if "chat_history_page" not in st.session_state:
        st.session_state.chat_history_page = []
    q2 = st.text_input("Type your question", key="chat_page_input")
    if q2:
        st.session_state.chat_history_page.append(("You", q2))
        st.session_state.chat_history_page.append(("Bot", answer_question(q2, df)))
        st.rerun()
    for who, msg in st.session_state.chat_history_page[-12:]:
        st.markdown(f"**{who}:** {msg}")
