# streamlit_app.py
# Inventory Dashboard — Streamlit (clean nav + organized chat layout)

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Optional: OpenAI for AI chat
try:
    import openai
except Exception:
    openai = None

# =============================================================================
# PAGE CONFIGURATION & STYLES
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

PRIMARY_COLOR = "#0077B6"
ACCENT_COLOR = "#1EA97C"
DARK_TEXT = "#1B4E4D"
MUTED_TEXT = "#4A7D7B"

st.markdown(f"""
    <style>
        .main {{ background: linear-gradient(145deg,#F0F5F9 0%,#E3EAF0 50%,#D8E0E8 100%); }}
        .card {{
            background: rgba(255,255,255,0.98);
            backdrop-filter: blur(8px);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(240,240,240,0.5);
        }}
        .chat-message {{
            background: white;
            border-radius: 12px;
            padding: 10px 12px;
            margin-bottom: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }}
        .chat-user {{
            color: #333;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .chat-bot {{
            color: {DARK_TEXT};
            background: #E8F4F3;
            padding: 6px 10px;
            border-radius: 8px;
            display: inline-block;
        }}
        .modebar {{ visibility: hidden; }}
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADING
# =============================================================================
DATA_DIR = "data"

def read_csv_clean(path):
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
# FALLBACK DATA
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
# DERIVED METRICS
# =============================================================================
products["StockValue"] = products["Quantity"] * products["UnitPrice"]
supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)
sales_ext = sales.merge(products[["Product_ID", "Name", "Category"]], on="Product_ID", how="left")
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)

# =============================================================================
# AI FUNCTION
# =============================================================================
def df_preview_text(df, limit=5):
    cols = ", ".join(df.columns)
    return f"rows={len(df)}, cols=[{cols}]\npreview:\n{df.head(limit).to_csv(index=False)}"

def answer_query_llm(query):
    try:
        prod_ctx = df_preview_text(products)
        sales_ctx = df_preview_text(sales)
        supp_ctx = df_preview_text(suppliers)
        context = (
            "You are a precise data analyst.\n"
            f"[PRODUCTS]\n{prod_ctx}\n\n[SALES]\n{sales_ctx}\n\n[SUPPLIERS]\n{supp_ctx}"
        )
        if not (openai and st.secrets.get("OPENAI_API_KEY")):
            return "AI chat is disabled or missing API key."
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Be concise and factual."},
                {"role": "user", "content": f"{context}\n\nUser: {query}"},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# =============================================================================
# CHAT SECTION
# =============================================================================
bot_cols = st.columns([1.1, 2.3], gap="large")

if "chat_log" not in st.session_state:
    st.session_state.chat_log = [
        ("user", "Highest stock value supplier?"),
        ("bot", f"ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}.")
    ]

with bot_cols[0]:
    st.markdown(f"""
        <div class="card">
            <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
            <div class="small-muted">Ask questions about inventory, suppliers, or sales.</div>
            <hr/>
            <div style="max-height:300px; overflow-y:auto; padding-right:4px;">
    """, unsafe_allow_html=True)

    # عرض الرسائل داخل كروت صغيرة
    for role, msg in st.session_state.chat_log:
        if role == "user":
            st.markdown(f"<div class='chat-message'><div class='chat-user'>User:</div><div>{msg}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message'><div class='chat-bot'>Bot: {msg}</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # خانة إدخال السؤال
    with st.form("chat_form", clear_on_submit=True):
        user_q = st.text_input("", placeholder="Type your question here...", label_visibility="collapsed")
        send = st.form_submit_button("Send")

    if send and user_q.strip():
        q = user_q.strip()
        st.session_state.chat_log.append(("user", q))
        with st.spinner("Analyzing..."):
            ans = answer_query_llm(q)
        st.session_state.chat_log.append(("bot", ans))
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TREND PERFORMANCE (Single version only)
# =============================================================================
with bot_cols[1]:
    st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Trend Performance</div>", unsafe_allow_html=True)
    name_col = "Name"
    qty_col = "Qty"
    series_df = sales_ext.groupby(["Month", name_col], as_index=False)[qty_col].sum()
    months_sorted = sorted(series_df["Month"].unique(), key=lambda x: pd.to_datetime(x))

    fig = go.Figure()
    colors = ["#0077B6", "#FF9500", "#1EA97C", "#E74C3C"]
    for i, label in enumerate(series_df[name_col].unique()):
        sub = series_df[series_df[name_col] == label].set_index("Month").reindex(months_sorted).fillna(0)
        fig.add_trace(go.Scatter(x=months_sorted, y=sub[qty_col], mode="lines+markers",
                                 name=label, line=dict(color=colors[i % len(colors)], width=3)))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=6, r=6, t=8, b=6), font=dict(color=DARK_TEXT))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
