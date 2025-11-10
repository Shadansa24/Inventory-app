# streamlit_app.py
# Inventory Dashboard — Streamlit (AI chat; no barcode/detailed reports/nav; no Inventory Snapshot)

import os
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat (dashboard still runs fine without it)
try:
    import openai
except Exception:
    openai = None


# =============================================================================
# PAGE CONFIGURATION & GLOBAL STYLES
# =============================================================================
st.set_page_config(
    page_title="Inventory Control Dashboard",
    page_icon="📦",
    layout="wide",
)

# New professional color palette
PRIMARY_COLOR = "#0077B6"  # Deep Sea Blue
ACCENT_COLOR = "#1EA97C"   # Vibrant Green for 'In Stock'
DARK_TEXT = "#1B4E4D"      # Dark Teal for titles
MUTED_TEXT = "#4A7D7B"     # Muted Teal for labels

PRIMARY_BG_GRADIENT = """
linear-gradient(145deg,
#F0F5F9 0%, 
#E3EAF0 50%, 
#D8E0E8 100%)
"""

CARD_STYLE = """
background: rgba(255,255,255,0.98);
backdrop-filter: blur(8px);
border-radius: 20px; /* أنعم وأكبر */
padding: 22px 22px 16px 22px; /* مساحة أكبر للراحة */
box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08); /* ظل أكثر احترافية */
border: 1px solid rgba(240, 240, 240, 0.5);
"""

LABEL_STYLE = f"color:{MUTED_TEXT}; font-weight:600; font-size:13px; letter-spacing:.3px;"
TITLE_STYLE = f"color:{DARK_TEXT}; font-weight:800; font-size:24px;"

# Inject global CSS
st.markdown(
    f"""
    <style>
        .main {{ background: {PRIMARY_BG_GRADIENT}; }}
        .small-muted {{ color:#718b89; font-size:12px; }}
        .card {{ {CARD_STYLE} }}
        
        /* --- تحديث تصميم الـ Chip ليصبح مثل عناصر قائمة (Nav Items) --- */
        .chip {{
            display:flex;
            align-items:center;
            padding:10px 15px; /* زيادة التباعد */
            font-size:14px; /* حجم أكبر */
            border-radius:12px;
            background:#E8F4F3; /* لون خلفية ناعم */
            color:{MUTED_TEXT};
            margin-bottom:6px;
            font-weight:600;
            cursor:pointer;
            transition: background 0.2s, color 0.2s;
        }}
        .chip:hover {{
            background: #D5EBEA;
            color: #005691;
        }}
        /* حالة نشطة لعنصر الـ Dashboard */
        .chip.active {{
             background: #D5EBEA; 
             color: {PRIMARY_COLOR};
             border-left: 4px solid {PRIMARY_COLOR}; 
             padding-left: 11px;
        }}
        
        hr {{ margin: 12px 0 10px 0; border-color:#e7eeed; }}
        
        /* إخفاء شريط الأدوات في Plotly ليعطي مظهرًا أكثر نظافة */
        .modebar {{ visibility: hidden; }}
        .js-plotly-plot {{ background-color: rgba(0,0,0,0) !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# DATA LOADING (Logic unchanged)
# =============================================================================
DATA_DIR = "data"


def read_csv_clean(path: str):
    """Load CSV safely with stripped headers."""
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return None


products = read_csv_clean(os.path.join(DATA_DIR, "products.csv"))
sales = read_csv_clean(os.path.join(DATA_DIR, "sales.csv"))
suppliers = read_csv_clean(os.path.join(DATA_DIR, "suppliers.csv"))


# =============================================================================
# FALLBACK DEMO DATA (Logic unchanged)
# =============================================================================
if products is None:
    products = pd.DataFrame({
        "Product_ID": [101, 102, 103, 104, 105],
        "SKU": ["IPH-15", "GS24", "MB-Air-M3", "LG-MSE", "AP-PR2"],
        "Name": ["iPhone 15", "Galaxy S24", "MacBook Air M3", "Logitech Mouse", "AirPods Pro"],
        "Category": ["Mobile", "Mobile", "Laptop", "Accessory", "Accessory"],
        "Quantity": [12, 30, 5, 3, 20],
        "MinStock": [15, 10, 8, 5, 10],
        "UnitPrice": [999, 899, 1299, 29, 249],
        "Supplier_ID": ["ACME", "GX", "ACME", "ACC", "ACME"],
    })

if suppliers is None:
    suppliers = pd.DataFrame({
        "Supplier_ID": ["ACME", "GX", "ACC"],
        "Supplier_Name": ["ACME Distribution", "GX Mobile", "Accessory House"],
        "Email": ["orders@acme.com", "gx@mobile.com", "hello@acc.com"],
        "Phone": ["+1-555-0100", "+1-555-0111", "+1-555-0122"],
    })

if sales is None:
    sales = pd.DataFrame({
        "Sale_ID": ["S-1001", "S-1002", "S-1003", "S-1004"],
        "Product_ID": [104, 101, 105, 102],
        "Qty": [2, 1, 3, 5],
        "UnitPrice": [29, 999, 249, 899],
        "Timestamp": ["2025-01-10", "2025-02-01", "2025-02-15", "2025-03-12"],
    })


# =============================================================================
# DATA CLEANING & DERIVED METRICS (Logic unchanged)
# =============================================================================
# Normalize column names
for df in (products, sales, suppliers):
    df.columns = [c.strip() for c in df.columns]

sales.rename(columns={"ProductId": "Product_ID", "product_id": "Product_ID", "Units": "Qty"}, inplace=True)

# Fill missing columns
if "Name" not in products.columns:
    products["Name"] = products["SKU"]

# Derived values
products["StockValue"] = products["Quantity"] * products["UnitPrice"]

# --- Stock counts
low_stock_items_count = int((products["Quantity"] < products["MinStock"]).sum())
low_stock_qty_total = int(products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum())
reorder_qty_total = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_qty_total = int(products["Quantity"].sum())

# --- Supplier totals
supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

# --- Sales extensions
sales_ext = sales.merge(products[["Product_ID", "Name", "Category", "SKU"]], on="Product_ID", how="left").copy()
if "Qty" not in sales_ext.columns:
    sales_ext["Qty"] = 1

sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum().sort_values("Qty", ascending=False)
sales_ext["Month"] = pd.to_datetime(sales_ext.get("Timestamp", datetime.now())).dt.to_period("M").astype(str)


# =============================================================================
# HELPER FUNCTIONS (Gauge style updated)
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    """Reusable gauge indicator with updated professional style."""
    max_value = max(max_value, 1)
    
    BG_COLOR = "rgba(0,0,0,0)"
    STEP_COLOR = "rgba(47,94,89,0.06)" 
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b><br><span style='font-size:14px; color:{MUTED_TEXT};'>{subtitle}</span>"},
        gauge={
            "axis": {"range": [0, max_value], "tickwidth": 0},
            "bar": {"color": color, "thickness": 0.5}, # Increased thickness
            "bgcolor": BG_COLOR,
            "steps": [{"range": [0, max_value], "color": STEP_COLOR}],
        },
        number={"font": {"size": 32, "color": DARK_TEXT, "family": "Arial"}}, # Larger, darker number
    ))
    fig.update_layout(
        margin=dict(l=6, r=6, t=40, b=6), 
        paper_bgcolor=BG_COLOR
    )
    return fig


def df_preview_text(df: pd.DataFrame, limit: int = 5) -> str:
    """Compact CSV-like preview for safe LLM context."""
    cols = ", ".join(map(str, df.columns))
    sample = df.head(limit).to_csv(index=False)
    return f"rows={len(df)}, cols=[{cols}]\npreview:\n{sample}"


# =============================================================================
# LAYOUT — TOP SECTION (Structural and Style changes)
# =============================================================================
top_cols = st.columns([1.0, 2.0, 1.4], gap="large")

# --- Menu (Updated to look like a clean navigation sidebar)
with top_cols[0]:
    st.markdown(f"""
        <div class="card" style="height:255px;">
            <div style="{TITLE_STYLE}; font-size:18px; margin-bottom:15px; font-weight:700;">Navigation</div>
            <div style="display:flex; flex-direction:column; gap:4px;">
                <div class='chip active'>📊 Dashboard</div>
                <div class='chip'>📦 Inventory</div>
                <div class='chip'>🚚 Suppliers</div>
                <div class='chip'>🛒 Orders</div>
                <div class='chip'>⚙️ Settings</div>
                <hr style="border-color:#e7eeed; margin: 8px 0;"/>
                <div class='chip'>💬 Chat Assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Stock Overview
with top_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px; margin-bottom:10px;'>Stock Overview</div>", unsafe_allow_html=True)
    gcols = st.columns(3)
    max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)

    with gcols[0]:
        # Using default Red for Low Stock
        st.plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#E74C3C", max_kpi),
                         use_container_width=True, config={"displayModeBar": False})
    with gcols[1]:
        # Using default Yellow/Orange for Reorder
        st.plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#F39C12", max_kpi),
                         use_container_width=True, config={"displayModeBar": False})
    with gcols[2]:
        # Using ACCENT_COLOR (Vibrant Green) for In Stock
        st.plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR, max_kpi),
                         use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# --- Quick Stats (Height adjusted to match the new nav bar height)
with top_cols[2]:
    st.markdown(f"""
        <div class="card" style="min-height:255px; display:flex; align-items:center; justify-content:center;">
            <div style="text-align:center;">
                <div style="{LABEL_STYLE}">Quick Stats</div>
                <div style="font-size:32px; color:{DARK_TEXT}; font-weight:800; margin-top:5px;">{products['SKU'].nunique()} SKUs</div>
                <div class="small-muted">Total Stock Value: **${products['StockValue'].sum():,.0f}**</div>
                <hr style="border-color:#d0d7e0;"/>
                 <div style="{LABEL_STYLE}">Supplier Base</div>
                <div style="font-size:24px; color:{DARK_TEXT}; font-weight:700;">{len(suppliers)} Active</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# LAYOUT — MIDDLE SECTION
# =============================================================================
mid_cols = st.columns([2.0, 1.3], gap="large")

# --- Supplier & Sales Charts
with mid_cols[0]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Supplier & Sales Data</div>", unsafe_allow_html=True)
    subcols = st.columns(2)

    # Supplier bar
    with subcols[0]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:8px;'>Top Suppliers (by stock value)</div>", unsafe_allow_html=True)
        fig_sup = px.bar(supplier_totals.head(4), x="StockValue", y="Supplier_Name",
                         orientation="h", text="StockValue",
                         color_discrete_sequence=[PRIMARY_COLOR]) 
        fig_sup.update_traces(texttemplate="$%{text:,}", textposition="outside", marker_opacity=0.85)
        fig_sup.update_layout(margin=dict(l=0, r=6, t=4, b=6),
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              xaxis_visible=False, yaxis_title=None)
        st.plotly_chart(fig_sup, use_container_width=True, config={"displayModeBar": False})

    # Sales bar
    with subcols[1]:
        st.markdown(f"<div style='{LABEL_STYLE}; margin-bottom:8px;'>Sales by Category (Qty)</div>", unsafe_allow_html=True)
        fig_cat = px.bar(sales_by_cat, x="Category", y="Qty", text="Qty",
                         color_discrete_sequence=[ACCENT_COLOR]) 
        fig_cat.update_traces(textposition="outside", marker_opacity=0.85)
        fig_cat.update_layout(margin=dict(l=6, r=6, t=4, b=6),
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<hr style='margin-top:0px;'>", unsafe_allow_html=True)
    legends = ["Acme Corp", "Innovate Ltd", "Global Goods", "Electronics", "Apparel", "Home Goods"]
    # Simple legend items, not chips
    st.markdown("<div style='display:flex; flex-wrap:wrap; gap:10px 15px;'>" + "".join(f"<span style='font-size:12px; color:{MUTED_TEXT};'>{l}</span>" for l in legends) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Snapshot card
with mid_cols[1]:
    st.markdown(f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Data Snapshots</div>
            <div class="small-muted">Updated: {datetime.now().strftime('%b %d, %Y - %H:%M')}</div>
            <hr/>
            <div style="{LABEL_STYLE}">Key Highlights</div>
            <ul style="margin-top:8px; color:{DARK_TEXT}; font-size:14px; padding-left:20px; line-height:1.6;">
                <li>**{low_stock_items_count} products** below min stock (Action needed)</li>
                <li>**{len(suppliers)} active suppliers** in the system</li>
                <li>**{int(sales_ext['Qty'].sum()):,} units sold** YTD</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# LAYOUT — BOTTOM SECTION
# =============================================================================
bot_cols = st.columns([1.1, 2.3], gap="large")

# --- Chat Assistant
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
if openai and OPENAI_KEY:
    openai.api_key = OPENAI_KEY


def answer_query_llm(query: str) -> str:
    """LLM-powered query handler (Logic unchanged)."""
    prod_ctx = df_preview_text(products)
    sales_ctx = df_preview_text(sales)
    supp_ctx = df_preview_text(suppliers)
    context = (
        "You are a precise data analyst. ONLY use the CSV context provided.\n"
        f"[PRODUCTS]\n{prod_ctx}\n\n[SALES]\n{sales_ctx}\n\n[SUPPLIERS]\n{supp_ctx}\n\n"
        "If a figure is not derivable from the data above, say you cannot confirm it."
    )
    prompt = f"{context}\n\nUser question: {query}\nGive a concise, factual answer."
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise, no-nonsense data analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Chat error: {e}"


with bot_cols[0]:
    st.markdown(f"""
        <div class="card" style="height:350px;">
            <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
            <div class="small-muted">Ask questions about inventory, suppliers, or sales.</div>
            <hr/>
            <div style="flex-grow:1; height:150px; overflow-y:auto; border-radius:10px; padding:10px; background:#f9fbfc; border:1px solid #eef1f5; margin-bottom:10px;">
                <p style="font-size:12px; color:#555; text-align:right; margin-bottom:5px;">User: Highest stock value supplier?</p>
                <p style="font-size:12px; color:{DARK_TEXT}; padding:4px 8px; border-radius:8px; background:#E8F4F3; display:inline-block;">Bot: ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    user_q = st.text_input("Type your question here:", key="chat_input", label_visibility="collapsed", placeholder="Enter your query...")
    # Chat logic remains unchanged
    if user_q:
        if not openai or not OPENAI_KEY:
            st.warning("AI chat is disabled: missing OpenAI package or OPENAI_API_KEY secret.")
        else:
            with st.spinner("Analyzing data..."):
                st.success(answer_query_llm(user_q))
    else:
        st.info("Try: “Which supplier has the highest stock value?”")

# --- Trend Performance
with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    name_col = "Name" if "Name" in sales_ext.columns else "Category"
    qty_col = "Qty"
    series_df = sales_ext.groupby(["Month", name_col], as_index=False)[qty_col].sum()
    months_sorted = sorted(series_df["Month"].unique(), key=lambda x: pd.to_datetime(x))

    fig_trend = go.Figure()
    # Define professional color sequence for trends
    trend_colors = ["#0077B6", "#FF9500", "#1EA97C", "#E74C3C"] 
    
    for i, label in enumerate(series_df[name_col].unique()):
        sub = series_df[series_df[name_col] == label].set_index("Month").reindex(months_sorted).fillna(0)
        fig_trend.add_trace(go.Scatter(x=months_sorted, y=sub[qty_col], mode="lines+markers", name=label, 
                                        line=dict(color=trend_colors[i % len(trend_colors)], width=3)))

    fig_trend.update_layout(
        margin=dict(l=6, r=6, t=8, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title=None,
        legend_title_text="Top-Selling Products",
        font=dict(color=DARK_TEXT)
    )

    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
