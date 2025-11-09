import os
import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional: AgGrid support (Highly recommended for this app)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID = True
except ImportError:
    AGGRID = False
    print("AgGrid not found. Install with 'pip install streamlit-aggrid' for better tables.")

# Optional: Streamlit-Extras for advanced styling
try:
    from streamlit_extras.stylable_container import stylable_container 
    STYLABLE_CONTAINER = True
except ImportError:
    STYLABLE_CONTAINER = False


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
    
    css = """
    :root {
        --background: #0b1020;
        --card-background: #1e2439;
        --text: #e8eeff;
        --accent: #ff4b4b; /* Primary color */
        --danger: #ff5722;
        --ok: #4CAF50;
        --blue: #2196F3;
        --red: #F44336;
        --green: #4CAF50;
        --yellow: #FFC107;
    }

    [data-testid="stAppViewContainer"] { background-color: var(--background); color: var(--text); }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 3rem; padding-right: 3rem; }
    
    /* --- General Button Styling --- */
    .stButton > button {
        border: 1px solid #4a546c;
        background-color: var(--card-background);
        color: var(--text);
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
    }
    /* Primary (Add Item) button */
    .stButton > button[kind="primary"] {
        background-color: var(--accent);
        border: none;
        color: var(--text);
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #e54545; /* Darker red on hover */
    }


    /* --- Top Navigation Bar Styling --- */
    /* Target the button container for the navigation bar */
    .nav-container .stButton > button {
        background-color: transparent;
        border: none;
        color: #aeb5c2;
        font-weight: 500;
        padding: 0.5rem 1rem;
        margin: 0;
        border-radius: 4px;
    }
    
    /* Active button styling */
    .nav-container .stButton > button.active-nav-button {
        color: var(--text) !important;
        border-bottom: 3px solid var(--accent);
        background-color: rgba(255, 75, 75, 0.1);
        border-radius: 4px 4px 0 0;
    }
    
    /* Brand logo */
    .brand { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
    .nav-flex { display: flex; align-items: center; border-bottom: 1px solid #24385f; padding-bottom: 10px;}

    /* --- KPI Cards --- */
    .kpi-card { background-color: var(--card-background); border-radius: 12px; padding: 1.5rem; display: flex; align-items: center; gap: 1rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
    .kpi-icon-container { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
    .kpi-icon { font-size: 1.5rem; color: var(--text); }
    .kpi-title { font-size: 0.9rem; color: #aeb5c2; text-transform: uppercase; font-weight: 600; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: var(--text); }

    /* --- Low Stock Alert --- */
    .alert-low { background-color: #3b1014; color: #ff5722; padding: 1rem; border-radius: 8px; border-left: 5px solid #ff5722; margin-bottom: 2rem; }

    /* --- Inventory Quick Filter Buttons (Radio) --- */
    [data-testid="stRadio"] label {
        background-color: #24385f; 
        color: #aeb5c2;
        border-radius: 20px;
        padding: 5px 15px;
        margin-right: 10px;
        transition: all 0.2s;
    }
    [data-testid="stRadio"] input:checked + div {
        background-color: var(--accent) !important;
        color: var(--text) !impo;
    }
    
    /* --- Inventory Grid View Card --- */
    .grid-card {
        background-color: var(--card-background);
        border-radius: 8px;
        padding: 1rem;
        border-left: 5px solid var(--blue);
    }
    .grid-card h3 { font-size: 1.2rem; margin-bottom: 5px; color: var(--text); }
    .grid-card .sku { font-size: 0.8rem; color: #aeb5c2; margin-bottom: 10px; }
    .grid-card .details { display: flex; justify-content: space-between; }
    .grid-card .details span { font-size: 0.9rem; }
    
    /* AgGrid Status Tag */
    .status-low { background-color: var(--danger); color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
    
    /* --- Floating Chat Button --- */
    /* This targets the st.popover button */
    [data-testid="stPopover"] > button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: var(--accent);
        color: white;
        font-size: 24px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 99;
    }
    [data-testid="stPopover"] > button:hover {
        background-color: #e54545;
        color: white;
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
# Utilities & Components
# =============================================
def load_csv(path, cols):
    """Load a CSV file with column alignment and safe fallback."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=cols)
    
    # Ensure all columns exist, preventing key errors later
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df[cols].copy() # Return a copy to avoid SettingWithCopyWarning


def save_csv(df, path):
    """Save DataFrame to CSV safely."""
    df.to_csv(path, index=False)


def plotly_darkify(fig, h=300):
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

# --- [FIXED] KPI Card Definition ---
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

# --- [FIXED] Top Navigation ---
def topbar_navigation(tabs, current_tab):
    """Render top navigation bar with custom styling."""
    
    st.markdown('<div class="nav-flex">', unsafe_allow_html=True)
    
    logo_col, nav_col = st.columns([1, 6])
    
    with logo_col:
        st.markdown('<div class="brand">📦 SBIM</div>', unsafe_allow_html=True)

    with nav_col:
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        nav_cols = st.columns(len(tabs))
        
        for i, t in enumerate(tabs):
            # Use st.session_state.tab to determine active button
            is_active = (t == current_tab)
            
            if nav_cols[i].button(t, key=f"nav_btn_{t}", use_container_width=True):
                st.session_state.tab = t
                st.rerun() # Force rerun to update active style
            
            # JS hack to add 'active' class to the correct button
            if is_active:
                st.markdown(f"""
                <script>
                    var buttons = window.parent.document.querySelectorAll('.nav-container .stButton > button');
                    if (buttons.length > {i}) {{
                        buttons[{i}].classList.add('active-nav-button');
                    }}
                </script>
                """, unsafe_allow_html=True)
            
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
    
    # Formatting
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
    """A simple Q&A chat based on the inventory data, placed in a popover."""
    
    chat_popover = st.popover("💬")

    with chat_popover:
        st.markdown("### 💬 Inventory Assistant")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about stock, price, or ID..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            response = ""
            prompt_lower = prompt.lower()
            
            # Simple, robust search logic
            search_terms = prompt_lower.replace("stock in", "").replace("quantity of", "").replace("id of", "").replace("sku of", "").replace("price of", "").strip()
            
            # Find matches by Name or SKU
            match = P[P['Name'].str.lower().str.contains(search_terms, na=False) | 
                      P['SKU'].astype(str).str.lower().str.contains(search_terms, na=False)].head(1)
            
            if not match.empty:
                name = match['Name'].iloc[0]
                sku = match['SKU'].iloc[0]
                
                if "stock" in prompt_lower or "quantity" in prompt_lower:
                    qty = match['Quantity'].iloc[0]
                    status = "Low Stock ⚠️" if match['Status'].iloc[0] == 'Low' else "OK ✅"
                    response = f"The current stock for **{name}** is **{qty}** units. Status: **{status}**."
                
                elif "id" in prompt_lower or "sku" in prompt_lower:
                    response = f"The **SKU** for **{name}** is `{sku}`."
                
                # --- [NEW] Added price logic ---
                elif "price" in prompt_lower:
                    price = match['UnitPrice'].iloc[0]
                    response = f"The **Unit Price** for **{name}** is **${price:,.2f}**."

                else:
                    response = f"Found **{name}** (SKU: {sku}). What do you want to know about it? (Stock/Price/ID)"
            else:
                response = f"Sorry, I couldn't find an item matching '{search_terms}'."

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
T["Timestamp"] = pd.to_datetime(T.get("Timestamp", pd.NaT), errors="coerce", utc=True)

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

# Render Assistant as a floating popover
inventory_assistant(P)

st.markdown("---") 

# ---------------------------------------------
## 📊 Dashboard
# ---------------------------------------------
if tab == "Dashboard":
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
            # Ensure Timestamp is timezone-aware for comparison
            month_df = T[T["Timestamp"].dt.tz_convert(None).dt.to_period("M") == thism]
            mtd_sales = (month_df["Qty"] * month_df["UnitPrice"]).sum()
        kpi_card("Sales (MTD)", f"${mtd_sales:,.2f}", "📈", "var(--yellow)")

    st.markdown("---")
    left, right = st.columns([3, 1])
    with left:
        st.subheader("Inventory Value by Category")
        if not P.empty:
            v = P.assign(Value=P["TotalValue"]).groupby("Category").sum("Value").reset_index()
            fig = px.bar(v, x="Category", y="Value", text_auto=".2s")
            st.plotly_chart(plotly_darkify(fig, h=300), use_container_width=True)
    with right:
        st.subheader("Top Low-Stock Categories")
        if not low_df.empty:
             lc = low_df.groupby('Category')['Quantity'].count().reset_index().rename(columns={'Quantity': 'LowCount'})
             fig2 = px.pie(lc, values='LowCount', names='Category', title="Low Stock Item Count")
             st.plotly_chart(plotly_darkify(fig2, h=300), use_container_width=True)
        else:
            st.info("No low-stock items.")

# ---------------------------------------------
## 📦 Inventory
# ---------------------------------------------
elif tab == "Inventory":
    st.title("Inventory Items")
    
    # --- [NEW] Add Item Modal ---
    add_item_modal = st.modal("Add New Inventory Item")
    with add_item_modal:
        with st.form("add_item_form"):
            st.subheader("Enter Item Details")
            
            # Form fields
            name = st.text_input("Item Name *")
            sku = st.text_input("SKU (Stock Keeping Unit) *")
            category = st.text_input("Category", "General")
            c1, c2 = st.columns(2)
            quantity = c1.number_input("Quantity", min_value=0, step=1)
            min_stock = c2.number_input("Min Stock Level", min_value=0, step=1)
            unit_price = st.number_input("Unit Price ($)", min_value=0.0, format="%.2f")
            
            # Form submission
            submitted = st.form_submit_button("Add Item", type="primary")
            
            if submitted:
                if not name or not sku:
                    st.error("Item Name and SKU are required.")
                else:
                    # Create a new product ID (simple increment)
                    new_id = (P['Product_ID'].max() + 1) if not P.empty else 1
                    
                    new_item = pd.DataFrame({
                        "Product_ID": [new_id],
                        "SKU": [sku],
                        "Name": [name],
                        "Category": [category],
                        "Quantity": [quantity],
                        "MinStock": [min_stock],
                        "UnitPrice": [unit_price],
                        "Supplier_ID": [np.nan] # Placeholder for supplier
                    })
                    
                    # Append and save
                    P = pd.concat([P, new_item], ignore_index=True)
                    save_csv(P, P_CSV)
                    st.success(f"Added '{name}' to inventory!")
                    st.rerun()

    # Top action button
    st.markdown('<div style="text-align: right; margin-top: -50px;">', unsafe_allow_html=True)
    if st.button("+ Add New Item", "add_item_btn", type="primary"):
        add_item_modal.open()
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

    # Quick Filters
    if "filter_state" not in st.session_state: st.session_state.filter_state = "All Items"
    st.session_state.filter_state = st.radio("Quick Filters", ["All Items", "Low Stock", "High Value"], 
                                             horizontal=True, label_visibility="collapsed", key="quick_filter_radio")

    # --- Filtering Logic ---
    filtered_df = P.copy()
    if st.session_state.filter_state == "Low Stock":
        filtered_df = filtered_df[filtered_df["Status"] == "Low"]
    elif st.session_state.filter_state == "High Value":
        threshold = filtered_df["TotalValue"].quantile(0.8) if not filtered_df.empty and len(filtered_df) > 1 else 0
        filtered_df = filtered_df[filtered_df["TotalValue"] >= threshold]
    
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Name"].str.contains(search_query, case=False, na=False) |
            filtered_df["SKU"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    if category_filter != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
        
    # --- Display View ---
    st.caption(f"**{len(filtered_df)}** items displayed")
    
    if view_mode == "Table":
        display_cols = ["Name", "SKU", "Category", "Quantity", "MinStock", "UnitPrice", "TotalValue", "Status"]
        aggrid_table(filtered_df[display_cols], height=500)
    
    # --- [NEW] Grid View Implementation ---
    else: 
        cols = st.columns(3)
        for i, row in enumerate(filtered_df.itertuples()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="grid-card">
                    <h3>{row.Name}</h3>
                    <div class="sku">SKU: {row.SKU}</div>
                    <div class="details">
                        <span>Qty: <strong>{row.Quantity}</strong> / {row.MinStock}</span>
                        <span>Value: <strong>${row.TotalValue:,.2f}</strong></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---") # Spacer

# ---------------------------------------------
## 📈 Reports
# ---------------------------------------------
elif tab == "Reports":
    st.header("Reports & Analytics")
    
    # --- [NEW] Sales Over Time Chart ---
    st.subheader("Sales Over Time")
    if not T.empty:
        # Resample data by day
        sales_over_time = T.set_index('Timestamp').resample('D').agg(TotalSales=('UnitPrice', 'sum')).reset_index()
        fig = px.line(sales_over_time, x='Timestamp', y='TotalSales', title="Daily Sales Revenue")
        st.plotly_chart(plotly_darkify(fig, h=400), use_container_width=True)
    else:
        st.info("No sales data recorded yet to display a report.")

# ---------------------------------------------
## ⚙️ Settings
# ---------------------------------------------
elif tab == "Settings":
    st.header("Settings")
    st.info("User management, minimum stock level defaults, and data export/import.")
    
    st.download_button(
        label="Download Inventory (products.csv)", 
        data=P.to_csv(index=False).encode(), 
        file_name="products.csv", 
        mime="text/csv"
    )
