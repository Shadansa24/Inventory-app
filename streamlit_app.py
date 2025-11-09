import os
import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
# Install this dependency: pip install streamlit-extras
try:
    from streamlit_extras.stylable_container import stylable_container 
except ImportError:
    st.warning("Please install 'streamlit-extras' for enhanced UI: pip install streamlit-extras")
    
# Optional: AgGrid support
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID = True
except ImportError:
    AGGRID = False
    print("AgGrid not found. Install with 'pip install streamlit-aggrid' for better tables.")


# =============================================
# Streamlit Config & CSS Injection
# =============================================
st.set_page_config(
    page_title="Small Business Inventory Manager",
    page_icon="📦",
    layout="wide"
)

# --- Custom CSS Block ---
def inject_css():
    """Inject global custom CSS for the dark theme and layout."""
    
    # CSS content as a Python string
    css = """
    /* Custom CSS for a dark, modern look inspired by the image */

    :root {
        /* Define colors for reuse */
        --background: #0b1020;
        --card-background: #1e2439;
        --text: #e8eeff;
        --accent: #ff4b4b; /* Primary color (red/pink from image) */
        --danger: #ff5722; /* Low stock alert */
        --ok: #4CAF50; /* Green for success/OK status */
        
        --blue: #2196F3;
        --red: #F44336;
        --green: #4CAF50;
        --yellow: #FFC107;
    }

    /* Global Background and Text */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background);
        color: var(--text);
    }

    /* Main Content Area Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    /* --- Top Navigation Bar --- */
    .nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #24385f;
    }

    .brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--accent);
    }

    .nav-links {
        display: flex;
        gap: 1.5rem;
        margin-left: 2rem;
    }

    .nav-link {
        color: #aeb5c2;
        text-decoration: none;
        font-size: 1rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        transition: all 0.2s;
        cursor: pointer; /* Ensure it looks clickable */
    }

    .nav-link:hover {
        color: var(--text);
    }

    .nav-link-active {
        color: var(--text) !important;
        background-color: rgba(255, 75, 75, 0.2); /* Light transparent background for active tab */
        border-bottom: 3px solid var(--accent);
        border-radius: 0;
    }

    .settings-area .stButton > button {
        background-color: transparent !important;
        border: 1px solid #4a546c;
        color: var(--text);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .settings-area .stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
    }


    /* --- KPI Cards --- */
    .kpi-card {
        background-color: var(--card-background);
        border-radius: 12px;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .kpi-icon-container {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .kpi-icon {
        font-size: 1.5rem;
        color: var(--text); /* Icon color */
    }

    .kpi-title {
        font-size: 0.9rem;
        color: #aeb5c2;
        text-transform: uppercase;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text);
    }

    /* --- Low Stock Alert --- */
    .alert-low {
        background-color: #3b1014; /* Dark red background */
        color: #ff5722;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #ff5722;
        margin-bottom: 2rem;
    }

    /* --- Inventory Table/Filters --- */
    /* Customize the radio buttons to look like the image's filter buttons (Low Stock, High Value) */
    [data-testid="stRadio"] label {
        background-color: #24385f; /* Darker background for non-selected buttons */
        color: #aeb5c2;
        border-radius: 20px;
        padding: 5px 15px;
        margin-right: 10px;
        transition: all 0.2s;
    }

    [data-testid="stRadio"] input:checked + div {
        background-color: var(--accent) !important;
        color: var(--text) !important;
    }

    /* Customizing Streamlit widgets for dark theme */
    div.stSelectbox > div[data-baseweb="select"] > div {
        background-color: var(--card-background);
        border-color: #24385f;
    }

    div.stTextInput > div[data-baseweb="input"] > div {
        background-color: var(--card-background);
        border-color: #24385f;
        color: var(--text);
    }
    .stTextInput input {
        color: var(--text);
    }


    /* AgGrid Customizations for Status Tags (requires allow_unsafe_jscode=True) */
    .status-low {
        background-color: var(--danger);
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .category-tag {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        color: #fff !important;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# =============================================
# Constants & Paths
# =============================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

P_CSV = os.path.join(DATA_DIR, "products.csv")
S_CSV = os.path.join(DATA_DIR, "suppliers.csv")
T_CSV = os.path.join(DATA_DIR, "sales.csv")

TABS = ["Dashboard", "Inventory", "Reports", "Settings"]
if "tab" not in st.session_state:
    st.session_state.tab = "Dashboard"

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


def plotly_darkify(fig, h=420):
    """Apply consistent dark theme layout to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        height=h,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font_color="#e8eeff",
        xaxis=dict(gridcolor="#24385f"),
        yaxis=dict(gridcolor="#24385f"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    return fig


# =============================================
# UI Components
# =============================================

def kpi_card(title, value, icon, color="var(--text)"):
    """KPI Card widget with icon."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon-container" style="background-color: {color};">
                <span class="kpi-icon">{icon}</span>
            </div>
            <div class="kpi-content">
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{value}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def action_button(label, key, icon=""):
    """Custom button for top-right actions like 'Add Item'."""
    st.button(f"{icon} {label}", key=key, use_container_width=True, type="primary")


def topbar_navigation(tabs, current_tab):
    """Render top navigation bar with custom styling."""
    
    # We use st.container to group the elements which is necessary for the layout
    with st.container():
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        logo_col, nav_col, settings_col = st.columns([1, 6, 1.5])
        
        with logo_col:
            st.markdown('<div class="brand">📦 SBIM</div>', unsafe_allow_html=True)

        with nav_col:
            # Create horizontal navigation links visually using HTML/CSS
            nav_html = '<div class="nav-links">'
            
            # Use invisible Streamlit buttons to handle the actual state change
            nav_buttons = []
            cols = st.columns(len(tabs))
            
            for i, t in enumerate(tabs):
                is_active = "nav-link-active" if t == current_tab else ""
                
                # HTML link structure for visual effect
                nav_html += f"""
                <a class="nav-link {is_active}">
                    {t}
                </a>
                """
                
                # Streamlit button for state change (hidden/styled by CSS later)
                if cols[i].button(t, key=f"nav_btn_{t}", help=f"Go to {t}", use_container_width=True):
                    st.session_state.tab = t
            
            nav_html += '</div>'
            
            # The HTML injection is for the custom look. The Streamlit buttons above
            # are what actually changes st.session_state.tab
            st.markdown(nav_html, unsafe_allow_html=True)

        with settings_col:
            st.markdown('<div class="settings-area">', unsafe_allow_html=True)
            if st.button("⚙️ Settings", key="top_settings_btn", use_container_width=True):
                 st.session_state.tab = "Settings"
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def aggrid_table(df, height=400):
    """Display DataFrame with AgGrid if available, fallback to standard table."""
    if not AGGRID:
        st.dataframe(df, use_container_width=True, height=height)
        return

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)
    
    # Custom cell renderer for status tags
    status_renderer_js = """
    function(params) {
        if (params.value === 'Low') {
            return '<span class="status-low">Low Stock</span>';
        }
        return params.value;
    }
    """
    
    gb.configure_column("Status", cellRenderer=status_renderer_js, width=120)
    
    # Optional formatting
    gb.configure_column("Quantity", type=["numericColumn"])
    gb.configure_column("MinStock", type=["numericColumn"])
    gb.configure_column("UnitPrice", type=["numericColumn"], valueFormatter="'$' + value.toFixed(2)")
    gb.configure_column("TotalValue", type=["numericColumn"], valueFormatter="'$' + value.toFixed(2)")

    gridOptions = gb.build()
    AgGrid(df, gridOptions=gridOptions, theme="balham-dark", height=height, 
           fit_columns_on_grid_load=False, allow_unsafe_jscode=True,
           key="inventory_aggrid")

# =============================================
# Database Assistant (Chat)
# =============================================

def inventory_assistant(P):
    """A simple Q&A chat based on the inventory data."""
    st.sidebar.markdown('---')
    st.sidebar.markdown("### 💬 Inventory Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.sidebar.chat_input("Ask about stock, price, or ID..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Simple processing logic
        response = ""
        prompt_lower = prompt.lower()
        
        # 1. Stock check
        if "stock" in prompt_lower or "quantity" in prompt_lower:
            product_info = prompt_lower.split("stock in")[-1].split("quantity of")[-1].split("stock of")[-1].strip()
            match = P[P['Name'].str.lower().str.contains(product_info, na=False) | P['SKU'].astype(str).str.lower().str.contains(product_info, na=False)].head(1)
            if not match.empty:
                qty = match['Quantity'].iloc[0]
                name = match['Name'].iloc[0]
                status = "Low Stock ⚠️" if match['Status'].iloc[0] == 'Low' else "OK ✅"
                response = f"The current stock for **{name}** is **{qty}** units. Status: **{status}**."
            else:
                response = f"Sorry, I couldn't find an item matching '{product_info}'."
        
        # 2. Product ID/SKU check
        elif "id of" in prompt_lower or "sku of" in prompt_lower:
            product_info = prompt_lower.split("id of")[-1].split("sku of")[-1].strip()
            match = P[P['Name'].str.lower().str.contains(product_info, na=False) | P['SKU'].astype(str).str.lower().str.contains(product_info, na=False)].head(1)
            if not match.empty:
                sku = match['SKU'].iloc[0]
                name = match['Name'].iloc[0]
                response = f"The **SKU** for **{name}** is `{sku}`."
                if 'Product_ID' in match.columns:
                     response += f" (Product ID: `{match['Product_ID'].iloc[0]}`)."
            else:
                response = f"Sorry, I couldn't find an item matching '{product_info}' to get its ID/SKU."

        # 3. Default response
        else:
            response = "I can currently check **stock/quantity** or **ID/SKU** for a product. Please be more specific!"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun() 


# =============================================
# Data Initialization & Preparation
# =============================================
P = load_csv(P_CSV, ["Product_ID", "SKU", "Name", "Category", "Quantity", "MinStock", "UnitPrice", "Supplier_ID"])
S = load_csv(S_CSV, ["Supplier_ID", "Supplier_Name", "Email", "Phone"])
T = load_csv(T_CSV, ["Sale_ID", "Product_ID", "Qty", "UnitPrice", "Timestamp"])

# Data typing and derived metrics
P["Quantity"] = pd.to_numeric(P["Quantity"], errors="coerce").fillna(0).astype(int)
P["MinStock"] = pd.to_numeric(P["MinStock"], errors="coerce").fillna(0).astype(int)
P["UnitPrice"] = pd.to_numeric(P["UnitPrice"], errors="coerce").fillna(0.0)
P["TotalValue"] = P["Quantity"] * P["UnitPrice"]
T["Qty"] = pd.to_numeric(T.get("Qty", 0), errors="coerce").fillna(0).astype(int)
T["UnitPrice"] = pd.to_numeric(T.get("UnitPrice", 0), errors="coerce").fillna(0.0)
T["Timestamp"] = pd.to_datetime(T.get("Timestamp", pd.NaT), errors="coerce").fillna(pd.Timestamp.utcnow())

# Status logic
P["Status"] = np.where(P["Quantity"] < P["MinStock"], "Low", "OK")
low_df = P.query("Status == 'Low'")
inventory_value = P["TotalValue"].sum()


# =============================================
# Main Page Render
# =============================================
inject_css()

# Render Top Bar (Navigation)
topbar_navigation(TABS, st.session_state.tab)
tab = st.session_state.tab

# Render Assistant in the sidebar
with st.sidebar:
    inventory_assistant(P)

st.markdown("---") 

# ---------------------------------------------
## 📊 Dashboard
# ---------------------------------------------
if tab == "Dashboard":
    # Alerts at the top
    if not low_df.empty:
        st.markdown(f'<div class="alert-low">⚠️ **{len(low_df)}** low-stock items need attention!</div>', unsafe_allow_html=True)
    
    ## KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Total Units", f"{P['Quantity'].sum():,}", "📦", "var(--blue)")
    with col2:
        kpi_card("Low Stock", str(len(low_df)), "⬇️", "var(--red)")
    with col3:
        kpi_card("Total Value", f"${inventory_value:,.2f}", "💰", "var(--green)")
    with col4:
        mtd_sales = 0.0
        if not T.empty:
            this_m = pd.Timestamp.utcnow().to_period("M")
            month_df = T[T["Timestamp"].dt.to_period("M") == this_m]
            mtd_sales = (month_df["Qty"] * month_df["UnitPrice"]).sum()
        kpi_card("Sales (MTD)", f"${mtd_sales:,.2f}", "📈", "var(--yellow)")

    st.markdown("---")

    ## Charts (Simplified)
    left, right = st.columns([3, 1])

    with left:
        st.subheader("Inventory Value by Category")
        if not P.empty:
            v = P.assign(Value=P["TotalValue"]).groupby("Category").sum("Value").reset_index()
            fig = px.bar(v, x="Category", y="Value", text_auto=".2s")
            st.plotly_chart(plotly_darkify(fig, h=300), use_container_width=True)

    with right:
        st.subheader("Recent Activity")
        # Placeholder for recent activity
        st.info("Latest stock movements (Sales, Restock, Adjustments) list goes here.")

    st.markdown("---")
    st.subheader("Low-stock Items Summary")
    if low_df.empty:
        st.success("All good — no low-stock items.")
    else:
        aggrid_table(low_df[["SKU", "Name", "Category", "Quantity", "MinStock", "UnitPrice"]])


# ---------------------------------------------
## 📦 Inventory
# ---------------------------------------------
elif tab == "Inventory":
    st.title("Inventory Items")
    
    # Top action button (mimics floating button)
    st.markdown('<div style="text-align: right; margin-top: -50px;">', unsafe_allow_html=True)
    action_button("+ Add Item", "add_item_btn", icon="")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")

    # Filters and Search Bar
    search_col, cat_col, view_col = st.columns([3, 1, 1])
    
    with search_col:
        search_query = st.text_input("Search by name or SKU...", key="inv_search", label_visibility="collapsed", placeholder="Search by name or SKU...")
    with cat_col:
        all_categories = ["All Categories"] + sorted(P["Category"].dropna().unique().tolist())
        category_filter = st.selectbox("Category", all_categories, key="cat_select", label_visibility="collapsed")
    with view_col:
        view_mode = st.radio("View Mode", ["Table", "Grid"], horizontal=True, label_visibility="collapsed", key="view_mode")

    st.markdown("---")

    # Quick Filters (All Items, Low Stock, High Value)
    if "filter_state" not in st.session_state:
        st.session_state.filter_state = "All Items"

    # Use stylable_container for the look of the filter buttons
    try:
        with stylable_container(
            key="filter_buttons_container",
            css_styles="""
            /* Override to keep radio buttons inline with custom styling */
            [data-testid="stRadio"] { display: flex; flex-direction: row; } 
            """,
        ):
            st.session_state.filter_state = st.radio("Quick Filters", ["All Items", "Low Stock", "High Value"], 
                                                     horizontal=True, label_visibility="collapsed", key="quick_filter_radio")
    except NameError:
        st.session_state.filter_state = st.radio("Quick Filters", ["All Items", "Low Stock", "High Value"], 
                                                 horizontal=True, key="quick_filter_radio")


    # --- Filtering Logic ---
    filtered_df = P.copy()
    
    # 1. Quick Filters
    if st.session_state.filter_state == "Low Stock":
        filtered_df = filtered_df[filtered_df["Status"] == "Low"]
    elif st.session_state.filter_state == "High Value":
        # Filter for the top 20% by TotalValue
        threshold = filtered_df["TotalValue"].quantile(0.8) if not filtered_df.empty else 0
        filtered_df = filtered_df[filtered_df["TotalValue"] >= threshold]
    
    # 2. Search & Category Filters
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Name"].str.contains(search_query, case=False, na=False) |
            filtered_df["SKU"].astype(str).str.contains(search_query, case=False, na=False)
        ]
        
    if category_filter != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
        
    # --- Display View ---
    st.caption(f"{len(filtered_df)} items displayed")
    
    if view_mode == "Table":
        display_cols = ["Name", "SKU", "Category", "Quantity", "MinStock", "UnitPrice", "TotalValue", "Status"]
        aggrid_table(filtered_df[display_cols], height=500)
    else: # Grid View (Placeholder)
        st.warning("Grid View is selected but the layout is currently showing the raw data. This is where individual product cards would be implemented.")
        st.dataframe(filtered_df) 

# ---------------------------------------------
## 📈 Reports/Settings
# ---------------------------------------------
elif tab == "Reports":
    st.header("Reports & Analytics")
    st.info("Detailed sales, trend, and supplier performance reports go here.")

elif tab == "Settings":
    st.header("Settings")
    st.info("User management, minimum stock level defaults, and data export/import.")
    st.download_button("Download products.csv", P.to_csv(index=False).encode(), "products.csv", "text/csv")
