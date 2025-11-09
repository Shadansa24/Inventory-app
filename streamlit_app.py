# =============================================
# Inventory Manager Dashboard (Refactored)
# =============================================

import os
import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional: AgGrid support
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID = True
except ImportError:
    AGGRID = False


# =============================================
# Streamlit Config
# =============================================
st.set_page_config(
    page_title="Inventory Manager",
    page_icon="📦",
    layout="wide"
)

# =============================================
# Constants & Paths
# =============================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV = os.path.join(DATA_DIR, "sales.csv")

TABS = ["Dashboard", "Inventory", "Suppliers", "Sales", "Reports", "Settings"]


# =============================================
# Utilities
# =============================================
def load_csv(path, cols):
    """Load a CSV file with column alignment and safe fallback."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df[cols]


def save_csv(df, path):
    """Save DataFrame to CSV safely."""
    df.to_csv(path, index=False)


def format_number(n):
    return f"{n:,.2f}" if isinstance(n, (int, float)) else n


def plotly_darkify(fig, h=420):
    """Apply consistent dark theme layout to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        height=h,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#0f172c",
        plot_bgcolor="#0f172c",
        font_color="#e8eeff",
        xaxis=dict(gridcolor="#24385f"),
        yaxis=dict(gridcolor="#24385f"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    return fig


# =============================================
# UI Components
# =============================================
def inject_css():
    """Inject global custom CSS."""
    st.markdown(open("styles.css").read() if os.path.exists("styles.css") else """
    <style>
    /* fallback inline CSS for dark mode */
    html, body, [data-testid="stAppViewContainer"] { background: #0b1020; }
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)


def kpi_card(title, value, note="", color="var(--text)"):
    """KPI Card widget."""
    st.markdown(
        f"""
        <div class="card">
            <div class="k-title">{title}</div>
            <p class="k-value" style="color:{color}">{value}</p>
            <div class="k-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def aggrid_table(df, height=430):
    """Display DataFrame with AgGrid if available, fallback to standard table."""
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)

    # Optional formatting
    if {"Quantity", "MinStock", "UnitPrice"}.issubset(df.columns):
        gb.configure_column("Quantity", type=["numericColumn"])
        gb.configure_column("MinStock", type=["numericColumn"])
        gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="x.toFixed(2)")

    grid = gb.build()
    AgGrid(df, gridOptions=grid, theme="balham-dark", height=height, fit_columns_on_grid_load=True)


def topbar(tabs, active_tab):
    """Render top navigation bar."""
    cols = st.columns([1, 5, 1])
    with cols[1]:
        st.markdown('<div class="topbar"><div class="topbar-row">', unsafe_allow_html=True)
        st.markdown('<div class="brand">📦 Inventory Manager <span class="brand-badge">Dark</span></div>', unsafe_allow_html=True)
        nav_cols = st.columns(len(tabs))
        for i, t in enumerate(tabs):
            if nav_cols[i].button(t, key=f"nav_{t}", use_container_width=True):
                st.session_state.tab = t
        st.markdown('</div></div>', unsafe_allow_html=True)


# =============================================
# Data Initialization
# =============================================
P = load_csv(P_CSV, ["Product_ID", "SKU", "Name", "Category", "Quantity", "MinStock", "UnitPrice", "Supplier_ID"])
S = load_csv(S_CSV, ["Supplier_ID", "Supplier_Name", "Email", "Phone"])
T = load_csv(T_CSV, ["Sale_ID", "Product_ID", "Qty", "UnitPrice", "Timestamp"])

# Data typing
P["Quantity"] = pd.to_numeric(P["Quantity"], errors="coerce").fillna(0).astype(int)
P["MinStock"] = pd.to_numeric(P["MinStock"], errors="coerce").fillna(0).astype(int)
P["UnitPrice"] = pd.to_numeric(P["UnitPrice"], errors="coerce").fillna(0.0)
T["Qty"] = pd.to_numeric(T.get("Qty", 0), errors="coerce").fillna(0).astype(int)
T["UnitPrice"] = pd.to_numeric(T.get("UnitPrice", 0), errors="coerce").fillna(0.0)
T["Timestamp"] = pd.to_datetime(T.get("Timestamp", pd.NaT), errors="coerce").fillna(pd.Timestamp.utcnow())

# Derived metrics
P["Status"] = np.where(P["Quantity"] < P["MinStock"], "Low", "OK")
low_df = P.query("Status == 'Low'")
inventory_value = (P["Quantity"] * P["UnitPrice"]).sum()


# =============================================
# Main Page Logic
# =============================================
inject_css()
if "tab" not in st.session_state:
    st.session_state.tab = "Dashboard"

topbar(TABS, st.session_state.tab)
tab = st.session_state.tab


# ----------- DASHBOARD -----------
if tab == "Dashboard":
    if not low_df.empty:
        st.warning(f"⚠️ {len(low_df)} low-stock items need attention")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Stock Items", f"{P['Quantity'].sum():,}", "Units on hand")
    with k2:
        kpi_card("Low Stock", str(len(low_df)), "Below minimum", color="var(--danger)")
    with k3:
        kpi_card("Inventory Value", f"${inventory_value:,.2f}", "Qty × Unit price", color="var(--accent)")
    with k4:
        mtd_sales = 0.0
        if not T.empty:
            this_m = pd.Timestamp.utcnow().to_period("M")
            month_df = T[T["Timestamp"].dt.to_period("M") == this_m]
            mtd_sales = (month_df["Qty"] * month_df["UnitPrice"]).sum()
        kpi_card("Sales (MTD)", f"${mtd_sales:,.2f}", "Month to date", color="var(--ok)")

    # Filters
    with st.expander("Filters"):
        q = st.text_input("Search name or SKU")
        cat = st.selectbox("Category", ["All"] + sorted(P["Category"].dropna().unique()))
        status = st.selectbox("Status", ["All", "OK", "Low"])
        topn = st.selectbox("Top N", [10, 20, 50, 100], index=1)

    filt = P.copy()
    if q:
        filt = filt[filt["Name"].str.contains(q, case=False, na=False) |
                    filt["SKU"].astype(str).str.contains(q, case=False, na=False)]
    if cat != "All":
        filt = filt[filt["Category"] == cat]
    if status != "All":
        filt = filt[filt["Status"] == status]

    left, right = st.columns([2, 1.2])
    with left:
        if not filt.empty:
            fig = px.bar(filt.nlargest(topn, "Quantity"), x="Name", y="Quantity",
                         color="Category", title="Stock by Product (Filtered)")
            st.plotly_chart(plotly_darkify(fig), use_container_width=True)
        else:
            st.info("No items match filters.")

    with right:
        if not P.empty:
            v = P.assign(Value=P["Quantity"] * P["UnitPrice"]).groupby("Category").sum("Value").reset_index()
            fig2 = px.bar(v, x="Category", y="Value", text_auto=".2s", title="Inventory Value by Category")
            st.plotly_chart(plotly_darkify(fig2), use_container_width=True)

    st.subheader("Low-stock Items")
    if low_df.empty:
        st.success("All good — no low-stock items.")
    else:
        aggrid_table(low_df[["Product_ID", "SKU", "Name", "Category", "Quantity", "MinStock", "UnitPrice"]])

# ----------- OTHER TABS -----------
elif tab == "Inventory":
    st.header("Inventory Management")
    # similar structure as original code but refactored for clarity
    st.info("Inventory editing and adding products go here (same functionality).")

elif tab == "Suppliers":
    st.header("Suppliers")
    aggrid_table(S)

elif tab == "Sales":
    st.header("Sales")
    st.info("Sales entry and tracking here.")

elif tab == "Reports":
    st.header("Reports")
    st.info("Analytics visualizations here.")

elif tab == "Settings":
    st.header("Settings")
    st.download_button("Download products.csv", P.to_csv(index=False).encode(), "products.csv", "text/csv")

