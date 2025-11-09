import os
import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional (rich table for large datasets)
AGGRID_AVAILABLE = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
except Exception:
    AGGRID_AVAILABLE = False

# Optional (LLM assistant)
OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except Exception:
    OPENAI_AVAILABLE = False

# =============================
# Config & Styles
# =============================
st.set_page_config(page_title="Smart Inventory Dashboard", layout="wide", page_icon="📊")
st.markdown("""
<style>
:root { --card-bg:#ffffff; --muted:#6c757d; }
.block-container { padding-top: 1.5rem; }
.metric-card {
  background: var(--card-bg); padding: 1.2rem; border-radius: 1rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center; transition: .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
.metric-card h4 { margin: 0; font-weight: 600; color:#343a40; }
.metric-card h2 { margin: .25rem 0 0; }
.subtitle { color: var(--muted); margin-top: -8px; }
.section-title { margin-top: .5rem; }
hr { margin: 1.25rem 0; }
</style>
""", unsafe_allow_html=True)

DATA_PATH_DEFAULT = "data/products.csv"

# =============================
# Helpers
# =============================
def load_csv(source: str | io.BytesIO) -> pd.DataFrame:
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip()
    # Normalize common header variants (optional)
    rename_map = {
        "ProductId": "Product_ID", "Product Id": "Product_ID", "ID": "Product_ID",
        "Qty": "Quantity", "qty": "Quantity",
        "Thresh": "Threshold", "MinQty": "Threshold"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df

def require_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        st.error(f"❌ Missing required columns: {missing}")
        st.info("Required columns: 'Product_ID', 'Name', 'Category', 'Quantity', 'Threshold'")
        st.stop()

def kpi_card(title: str, value: str, color: str):
    st.markdown(
        f"""
        <div class="metric-card">
          <h4>{title}</h4>
          <h2 style="color:{color};">{value}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

def get_openai_client():
    if not OPENAI_AVAILABLE:
        st.warning("OpenAI SDK not installed. Add `openai>=1.0.0` to requirements.txt.")
        return None
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        st.warning("Add your OpenAI key in Streamlit Secrets or env (OPENAI_API_KEY).")
        return None
    return OpenAI(api_key=api_key)

# =============================
# State init
# =============================
if "df" not in st.session_state:
    # Load default CSV if present
    if os.path.exists(DATA_PATH_DEFAULT):
        try:
            st.session_state.df = load_csv(DATA_PATH_DEFAULT)
        except Exception as e:
            st.session_state.df = pd.DataFrame()
            st.warning(f"Could not load default CSV: {e}")
    else:
        st.session_state.df = pd.DataFrame()

# Ensure schema or explain requirement
if not st.session_state.df.empty:
    require_columns(st.session_state.df, ["Product_ID", "Name", "Category", "Quantity", "Threshold"])

# =============================
# Sidebar Navigation
# =============================
st.sidebar.title("⚙️ Menu")
page = st.sidebar.radio(
    "Go to",
    ["📊 Dashboard", "🧠 AI Assistant", "📦 Inventory Manager", "🗂️ Data Uploads", "🔧 Settings"],
)

# =============================
# Page: Dashboard
# =============================
if page == "📊 Dashboard":
    st.title("📊 Smart Inventory Dashboard")
    st.markdown('<p class="subtitle">Monitor product stock levels and detect low inventory in real time.</p>', unsafe_allow_html=True)

    if st.session_state.df.empty:
        st.info("Upload data in **Data Uploads** to see the dashboard.")
        st.stop()

    df = st.session_state.df.copy()

    # KPIs
    total_products = len(df)
    low_stock = (df["Quantity"] < df["Threshold"]).sum()
    sufficient = total_products - low_stock

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Total Products", f"{total_products}", "#007bff")
    with c2: kpi_card("Low Stock", f"{low_stock}", "#dc3545")
    with c3: kpi_card("Sufficient Stock", f"{sufficient}", "#28a745")

    st.markdown("---")

    # Charts
    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = px.bar(
            df.sort_values("Quantity", ascending=False),
            x="Name", y="Quantity", color="Category",
            title="Stock by Product", height=420
        )
        fig1.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        df["Status"] = np.where(df["Quantity"] < df["Threshold"], "Low", "OK")
        fig2 = px.pie(df, names="Status", title="Stock Health", hole=0.45,
                      color="Status", color_discrete_map={"OK": "#28a745", "Low": "#dc3545"})
        fig2.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("⚠️ Low Stock Products")
    low_df = df[df["Quantity"] < df["Threshold"]].copy()
    if low_df.empty:
        st.success("✅ All products are sufficiently stocked.")
    else:
        if AGGRID_AVAILABLE:
            gb = GridOptionsBuilder.from_dataframe(low_df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(editable=False, filter=True, sortable=True)
            gb.configure_side_bar()
            grid = gb.build()
            AgGrid(low_df, gridOptions=grid, height=420, theme="balham", fit_columns_on_grid_load=True)
        else:
            st.dataframe(low_df, use_container_width=True)

# =============================
# Page: AI Assistant
# =============================
elif page == "🧠 AI Assistant":
    st.title("🧠 Inventory Assistant")
    if st.session_state.df.empty:
        st.info("Upload data in **Data Uploads** first.")
        st.stop()

    df = st.session_state.df.copy()
    client = get_openai_client()

    # Lightweight structured query first, then LLM fallback
    q = st.text_input("Ask a question (e.g., 'Which items are low?', 'ID for iPhone 15', 'show accessories')")
    if q:
        q_lower = q.lower()

        # Simple structured intents
        if "low" in q_lower and ("show" in q_lower or "list" in q_lower):
            st.write("**Low stock items:**")
            st.write(df[df["Quantity"] < df["Threshold"]][["Product_ID", "Name", "Category", "Quantity", "Threshold"]])
        elif "category" in q_lower and ("show" in q_lower or "list" in q_lower):
            st.write("**Available categories:** ", ", ".join(sorted(df["Category"].unique())))
        else:
            if not client:
                st.stop()

            # Build compact context (truncate if huge)
            preview = df.head(200).to_dict(orient="records")  # keep token count sane
            prompt = (
                "You are an inventory analyst. Answer using the structured data provided.\n"
                f"Data (first 200 rows): {preview}\n\n"
                f"Question: {q}\n"
                "If the question asks for an ID, return the Product_ID. If it asks for quantities, return exact numbers. "
                "Be concise."
            )

            with st.spinner("Thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Be precise and use the provided data."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )
            answer = resp.choices[0].message.content.strip()
            st.success(answer)

# =============================
# Page: Inventory Manager
# =============================
elif page == "📦 Inventory Manager":
    st.title("📦 Inventory Manager")

    if st.session_state.df.empty:
        st.info("Upload data in **Data Uploads** first.")
        st.stop()

    df = st.session_state.df.copy()
    st.caption("Edit quantities or thresholds and save back to CSV.")

    edited = st.data_editor(
        df, use_container_width=True, num_rows="dynamic", key="editor_df"
    )

    save_col1, save_col2 = st.columns([1, 5])
    with save_col1:
        if st.button("💾 Save Changes"):
            # Persist locally if default path exists; otherwise allow download
            try:
                os.makedirs(os.path.dirname(DATA_PATH_DEFAULT), exist_ok=True)
                edited.to_csv(DATA_PATH_DEFAULT, index=False)
                st.session_state.df = edited
                st.success("Saved to data/products.csv")
            except Exception as e:
                st.error(f"Could not save to disk: {e}")

    with save_col2:
        csv = edited.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "inventory_export.csv", "text/csv")

# =============================
# Page: Data Uploads
# =============================
elif page == "🗂️ Data Uploads":
    st.title("🗂️ Data Uploads")
    st.caption("Upload a CSV with columns: Product_ID, Name, Category, Quantity, Threshold")

    file = st.file_uploader("Upload inventory CSV", type=["csv"])
    if file:
        try:
            df_new = load_csv(file)
            require_columns(df_new, ["Product_ID", "Name", "Category", "Quantity", "Threshold"])
            st.session_state.df = df_new
            st.success("✅ Data loaded into session. Switch to Dashboard.")
            st.write(df_new.head())
        except Exception as e:
            st.error(f"Could not read file: {e}")

# =============================
# Page: Settings
# =============================
elif page == "🔧 Settings":
    st.title("🔧 Settings")
    st.caption("Tweak thresholds and preview impact.")

    if st.session_state.df.empty:
        st.info("Upload data in **Data Uploads** first.")
        st.stop()

    df = st.session_state.df.copy()
    buffer = st.slider("Low-stock buffer (units)", 0, 10, 0)
    df["Status"] = np.where(df["Quantity"] < (df["Threshold"] + buffer), "Low", "OK")
    st.write("Preview with current buffer:")
    st.dataframe(df[["Product_ID", "Name", "Quantity", "Threshold", "Status"]], use_container_width=True)

    st.info("Tip: connect real DB (Postgres / Firebase) and add auth for production use.")
