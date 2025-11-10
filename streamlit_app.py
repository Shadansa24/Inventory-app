# streamlit_app.py
# Inventory Dashboard — Streamlit (clean layout + unified chat container)
import os
from datetime import datetime
import io
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
# PAGE CONFIGURATION & GLOBAL STYLES
# =============================================================================
st.set_page_config(page_title="Inventory Control Dashboard", page_icon="📦", layout="wide")

PRIMARY_COLOR = "#0077B6"
ACCENT_COLOR = "#1EA97C"
DARK_TEXT = "#1B4E4D"
MUTED_TEXT = "#4A7D7B"

PRIMARY_BG_GRADIENT = """
linear-gradient(145deg,
#F0F5F9 0%, 
#E3EAF0 50%, 
#D8E0E8 100%)
"""

CARD_STYLE = """
background: rgba(255,255,255,0.98);
backdrop-filter: blur(8px);
border-radius: 20px; 
padding: 22px 22px 16px 22px; 
box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08); 
border: 1px solid rgba(240, 240, 240, 0.5);
"""

LABEL_STYLE = f"color:{MUTED_TEXT}; font-weight:600; font-size:13px;"
TITLE_STYLE = f"color:{DARK_TEXT}; font-weight:800; font-size:24px;"

st.markdown(
    f"""
    <style>
        .main {{ background: {PRIMARY_BG_GRADIENT}; }}
        .small-muted {{ color:#718b89; font-size:12px; }}
        .card {{ {CARD_STYLE} }}
        .chip {{
            display:flex;
            align-items:center;
            padding:10px 15px;
            font-size:14px;
            border-radius:12px;
            background:#E8F4F3;
            color:{MUTED_TEXT};
            margin-bottom:6px;
            font-weight:600;
            cursor:pointer;
            transition: background 0.2s, color 0.2s;
        }}
        .chip:hover {{ background:#D5EBEA; color:#005691; }}
        .chip.active {{
            background:#D5EBEA; 
            color:{PRIMARY_COLOR};
            border-left:4px solid {PRIMARY_COLOR};
            padding-left:11px;
        }}
        hr {{ margin:12px 0 10px 0; border-color:#e7eeed; }}
        .modebar {{ visibility:hidden; }}
        /* Hide helper link underlines in nav */
        .nav-link {{ text-decoration: none; color: inherit; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# LOAD DATA
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
# FALLBACK DEMO DATA
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
# SESSION STATE FOR EDITS (kept separate from original data to avoid breaking current dashboard)
# =============================================================================
if "products_edit" not in st.session_state:
    st.session_state.products_edit = products.copy()
if "suppliers_edit" not in st.session_state:
    st.session_state.suppliers_edit = suppliers.copy()
if "sales_edit" not in st.session_state:
    st.session_state.sales_edit = sales.copy()

# =============================================================================
# DERIVED METRICS (based on original data so your dashboard visuals don't change)
# =============================================================================
products["StockValue"] = products["Quantity"] * products["UnitPrice"]
low_stock_items_count = (products["Quantity"] < products["MinStock"]).sum()
low_stock_qty_total = int(products.loc[products["Quantity"] < products["MinStock"], "Quantity"].sum())
reorder_qty_total = int((products["MinStock"] - products["Quantity"]).clip(lower=0).sum())
in_stock_qty_total = int(products["Quantity"].sum())

supplier_totals = (
    products.merge(suppliers, on="Supplier_ID", how="left")
    .groupby("Supplier_Name", as_index=False)["StockValue"]
    .sum()
    .sort_values("StockValue", ascending=False)
)

sales_ext = sales.merge(products[["Product_ID", "Name", "Category", "SKU"]], on="Product_ID", how="left")
sales_ext["Month"] = pd.to_datetime(sales_ext["Timestamp"]).dt.to_period("M").astype(str)
sales_by_cat = sales_ext.groupby("Category", as_index=False)["Qty"].sum()

# =============================================================================
# HELPERS
# =============================================================================
def gauge(title, value, subtitle, color, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b><br><span style='font-size:14px; color:{MUTED_TEXT};'>{subtitle}</span>"},
        gauge={
            "axis": {"range": [0, max(max_value, 1)], "tickwidth": 0},
            "bar": {"color": color, "thickness": 0.5},
            "steps": [{"range": [0, max(max_value, 1)], "color": "rgba(47,94,89,0.06)"}],
        },
        number={"font": {"size": 32, "color": DARK_TEXT}},
    ))
    fig.update_layout(margin=dict(l=6, r=6, t=30, b=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def df_preview_text(df, limit=5):
    cols = ", ".join(df.columns)
    return f"rows={len(df)}, cols=[{cols}]\npreview:\n{df.head(limit).to_csv(index=False)}"

# =============================================================================
# ROUTING VIA QUERY PARAMS (keeps your nav design; makes chips clickable)
# =============================================================================
DEFAULT_PAGE = "Dashboard"
qp = st.query_params
current_page = qp.get("page", DEFAULT_PAGE)

def _chip(label, icon, active):
    # Wrap chip in a hyperlink that sets the query param (?page=...)
    act = "active" if active else ""
    href = f"?page={label.replace(' ', '%20')}"
    return f"<a class='nav-link' href='{href}'><div class='chip {act}'>{icon} {label}</div></a>"

# =============================================================================
# LAYOUT — TOP SECTION
# =============================================================================
top_cols = st.columns([0.8, 2.0, 1.5], gap="large")

# --- NAVIGATION (DESIGN UNCHANGED; NOW CLICKABLE)
with top_cols[0]:
    st.markdown(f"""
        <div class="card" style="padding:20px;">
            <div style="{TITLE_STYLE}; font-size:18px;">Navigation</div>
            <div style="display:flex; flex-direction:column; gap:8px; margin-top:10px;">
                {_chip("Dashboard", "📊", current_page=="Dashboard")}
                {_chip("Inventory", "📦", current_page=="Inventory")}
                {_chip("Suppliers", "🚚", current_page=="Suppliers")}
                {_chip("Orders", "🛒", current_page=="Orders")}
                {_chip("Chat Assistant", "💬", current_page=="Chat Assistant")}
                {_chip("Settings", "⚙️", current_page=="Settings")}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- STOCK OVERVIEW (Dashboard only)
if current_page == "Dashboard":
    with top_cols[1]:
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:20px;'>Stock Overview</div>", unsafe_allow_html=True)
        gcols = st.columns(3)
        max_kpi = max(in_stock_qty_total, reorder_qty_total, low_stock_qty_total, 1)
        gcols[0].plotly_chart(gauge("Low Stock", low_stock_qty_total, f"{low_stock_items_count} items", "#E74C3C", max_kpi), use_container_width=True)
        gcols[1].plotly_chart(gauge("Reorder", reorder_qty_total, f"{reorder_qty_total} items", "#F39C12", max_kpi), use_container_width=True)
        gcols[2].plotly_chart(gauge("In Stock", in_stock_qty_total, f"{in_stock_qty_total} items", ACCENT_COLOR, max_kpi), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with top_cols[2]:
        st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="{LABEL_STYLE}">Quick Stats</div>
                <div style="font-size:32px; color:{DARK_TEXT}; font-weight:800;">{products['SKU'].nunique()} SKUs</div>
                <div class="small-muted">Total Stock Value: ${products['StockValue'].sum():,.0f}</div>
                <hr/>
                <div style="{LABEL_STYLE}">Suppliers</div>
                <div style="font-size:24px; color:{DARK_TEXT}; font-weight:700;">{len(suppliers)} Active</div>
            </div>
        """, unsafe_allow_html=True)

# =============================================================================
# MIDDLE SECTION (Dashboard only)
# =============================================================================
if current_page == "Dashboard":
    mid_cols = st.columns([2.0, 1.3], gap="large")

    with mid_cols[0]:
        st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>Supplier & Sales Data</div>", unsafe_allow_html=True)
        subcols = st.columns(2)
        subcols[0].plotly_chart(px.bar(supplier_totals, x="StockValue", y="Supplier_Name", orientation="h",
                                       color_discrete_sequence=[PRIMARY_COLOR]), use_container_width=True)
        subcols[1].plotly_chart(px.bar(sales_by_cat, x="Category", y="Qty", color_discrete_sequence=[ACCENT_COLOR]),
                                use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with mid_cols[1]:
        st.markdown(f"""
            <div class="card">
                <div style="{TITLE_STYLE}; font-size:18px;">Data Snapshot</div>
                <div class="small-muted">Updated: {datetime.now().strftime('%b %d, %Y %H:%M')}</div>
                <hr/>
                <ul style="font-size:14px; color:{DARK_TEXT}; line-height:1.6;">
                    <li>{low_stock_items_count} products below min stock</li>
                    <li>{len(suppliers)} active suppliers</li>
                    <li>{int(sales_ext['Qty'].sum()):,} units sold YTD</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# =============================================================================
# AI ANSWER FUNCTION (unchanged)
# =============================================================================
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
# BOTTOM SECTION (Dashboard only)
# =============================================================================
if current_page == "Dashboard":
    bot_cols = st.columns([1.1, 2.3], gap="large")

    OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
    if openai and OPENAI_KEY:
        openai.api_key = OPENAI_KEY

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = [
            ("user", "Which supplier has the highest stock value?"),
            ("bot", f"ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}."),
        ]

    def render_chat_messages():
        html = []
        for role, text in st.session_state.chat_log:
            if role == "user":
                html.append(f"<p style='text-align:right; font-size:13px; margin:4px 0;'>🧍‍♂️ <b>You:</b> {text}</p>")
            else:
                html.append(f"<p style='font-size:13px; background:#E8F4F3; color:{DARK_TEXT}; "
                            f"padding:6px 10px; border-radius:8px; display:inline-block; margin:4px 0;'>🤖 {text}</p>")
        return "\n".join(html)

    # --- CHAT CARD
    with bot_cols[0]:
        st.markdown(f"""
            <div class="card" style="padding:18px; height:430px; display:flex; flex-direction:column;">
                <div style="{TITLE_STYLE}; font-size:18px;">Chat Assistant</div>
                <div class="small-muted" style="margin-bottom:8px;">Ask questions about inventory, suppliers, or sales.</div>
                <hr style="margin:8px 0 10px 0;"/>
                <div id="chat-container" style="flex-grow:1; overflow-y:auto; background:#f9fbfc;
                    border:1px solid #eef1f5; padding:10px 12px; border-radius:10px;
                    display:flex; flex-direction:column; justify-content:space-between;">
                    <div id="chat-messages">
                        {render_chat_messages()}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Streamlit input (works)
        with st.form("chat_form", clear_on_submit=True):
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                user_q = st.text_input("", placeholder="Type your question...", label_visibility="collapsed", key="chat_input")
            with cols[1]:
                send = st.form_submit_button("Send")

        if send and user_q.strip():
            q = user_q.strip()
            st.session_state.chat_log.append(("user", q))
            if not (openai and OPENAI_KEY):
                ans = "AI chat is disabled: missing OpenAI package or API key."
            else:
                with st.spinner("Analyzing data..."):
                    ans = answer_query_llm(q)
            st.session_state.chat_log.append(("bot", ans))
            st.rerun()

    # --- TREND PERFORMANCE
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
            fig.add_trace(go.Scatter(x=months_sorted, y=sub[qty_col], mode="lines+markers", name=label,
                                     line=dict(color=colors[i % len(colors)], width=3)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=6, r=6, t=8, b=6))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

# --- KEEP EVERYTHING ABOVE UNCHANGED UNTIL THE SECTION BELOW ---
# (We start applying fixes from the "OTHER PAGES" section.)

# --- KEEP EVERYTHING ABOVE UNCHANGED UNTIL THE SECTION BELOW ---

# --- KEEP EVERYTHING ABOVE UNCHANGED UNTIL THE SECTION BELOW ---

# =============================================================================
# OTHER PAGES (FIXED — SAME LAYOUT + CHAT STYLE)
# =============================================================================
def _download_csv_button(df: pd.DataFrame, label: str, filename: str):
    df = df.copy()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv_bytes, file_name=filename, mime="text/csv")


# ✅ Use same column layout structure for non-dashboard pages
if current_page != "Dashboard":
    page_cols = st.columns([0.8, 3.2], gap="large")

    # left column = navigation (same as dashboard)
    with page_cols[0]:
        st.markdown(f"""
            <div class="card" style="padding:20px;">
                <div style="{TITLE_STYLE}; font-size:18px;">Navigation</div>
                <div style="display:flex; flex-direction:column; gap:8px; margin-top:10px;">
                    {_chip("Dashboard", "📊", current_page=="Dashboard")}
                    {_chip("Inventory", "📦", current_page=="Inventory")}
                    {_chip("Suppliers", "🚚", current_page=="Suppliers")}
                    {_chip("Orders", "🛒", current_page=="Orders")}
                    {_chip("Chat Assistant", "💬", current_page=="Chat Assistant")}
                    {_chip("Settings", "⚙️", current_page=="Settings")}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # right column = page content
    with page_cols[1]:
        if current_page == "Inventory":
            st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>📦 Inventory (Editable)</div>", unsafe_allow_html=True)
            edited = st.data_editor(st.session_state.products_edit, num_rows="dynamic", use_container_width=True)
            st.session_state.products_edit = edited
            st.markdown("</div>", unsafe_allow_html=True)

        elif current_page == "Suppliers":
            st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>🚚 Suppliers (Editable)</div>", unsafe_allow_html=True)
            edited = st.data_editor(st.session_state.suppliers_edit, num_rows="dynamic", use_container_width=True)
            st.session_state.suppliers_edit = edited
            st.markdown("</div>", unsafe_allow_html=True)

        elif current_page == "Orders":
            st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>🛒 Orders / Sales (Editable)</div>", unsafe_allow_html=True)
            edited = st.data_editor(st.session_state.sales_edit, num_rows="dynamic", use_container_width=True)
            st.session_state.sales_edit = edited
            st.markdown("</div>", unsafe_allow_html=True)

        elif current_page == "Chat Assistant":
            if "chat_log" not in st.session_state:
                st.session_state.chat_log = [
                    ("user", "Which supplier has the highest stock value?"),
                    ("bot", f"ACME Distribution has the highest stock value at ${supplier_totals.iloc[0]['StockValue']:,.0f}."),
                ]

            def render_chat_messages():
                html = []
                for role, text in st.session_state.chat_log:
                    if role == "user":
                        html.append(f"<p style='text-align:right; font-size:13px; margin:4px 0;'>🧍‍♂️ <b>You:</b> {text}</p>")
                    else:
                        html.append(f"<p style='font-size:13px; background:#E8F4F3; color:{DARK_TEXT}; "
                                    f"padding:6px 10px; border-radius:8px; display:inline-block; margin:4px 0;'>🤖 {text}</p>")
                return "\n".join(html)

            st.markdown(f"""
                <div class="card" style="padding:18px; height:430px; display:flex; flex-direction:column;">
                    <div style="{TITLE_STYLE}; font-size:18px;">💬 Chat Assistant</div>
                    <div class="small-muted" style="margin-bottom:8px;">Ask questions about inventory, suppliers, or sales.</div>
                    <hr style="margin:8px 0 10px 0;"/>
                    <div id="chat-container" style="flex-grow:1; overflow-y:auto; background:#f9fbfc;
                        border:1px solid #eef1f5; padding:10px 12px; border-radius:10px;
                        display:flex; flex-direction:column; justify-content:space-between;">
                        <div id="chat-messages">
                            {render_chat_messages()}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.form("chat_form_page", clear_on_submit=True):
                cols = st.columns([0.8, 0.2])
                user_q = cols[0].text_input("", placeholder="Type your question...", label_visibility="collapsed")
                send = cols[1].form_submit_button("Send")

            OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
            if openai and OPENAI_KEY:
                openai.api_key = OPENAI_KEY

            if send and user_q.strip():
                q = user_q.strip()
                st.session_state.chat_log.append(("user", q))
                if not (openai and OPENAI_KEY):
                    ans = "AI chat is disabled: missing OpenAI package or API key."
                else:
                    with st.spinner("Analyzing data..."):
                        ans = answer_query_llm(q)
                st.session_state.chat_log.append(("bot", ans))
                st.rerun()

        elif current_page == "Settings":
            st.markdown(f"<div class='card'><div style='{TITLE_STYLE}; font-size:18px;'>⚙️ Settings</div>", unsafe_allow_html=True)
            st.write("Download your edited tables as CSV:")
            _download_csv_button(st.session_state.products_edit, "⬇️ Download Inventory (CSV)", "inventory_edited.csv")
            _download_csv_button(st.session_state.suppliers_edit, "⬇️ Download Suppliers (CSV)", "suppliers_edited.csv")
            _download_csv_button(st.session_state.sales_edit, "⬇️ Download Orders (CSV)", "orders_edited.csv")
            st.markdown("</div>", unsafe_allow_html=True)
