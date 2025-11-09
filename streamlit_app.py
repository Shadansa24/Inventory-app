import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================
# Page Config & CSS
# =============================================

# Set page config
st.set_page_config(
    page_title="Inventory Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed" # Hide the default sidebar
)

# --- Inject Custom CSS ---
def load_css():
    """Injects custom CSS to replicate the design."""
    st.markdown(r"""
    <style>
        /* --- Global --- */
        /* Hide default Streamlit elements */
        [data-testid="stDecoration"] { display: none; }
        [data-testid="stHeader"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        
        /* Main app background */
        [data-testid="stAppViewContainer"] {
            background-color: #f0f2f5;
        }

        /* --- Custom Sidebar --- */
        .sidebar {
            background-color: #ffffff;
            padding: 2rem 1.5rem;
            height: 100vh; /* Full viewport height */
            border-right: 1px solid #e0e0e0;
            
            /* Make it scrollable if content overflows */
            overflow-y: auto;
            position: fixed; /* Fix it to the left */
            width: 250px; /* Fixed width */
        }
        
        /* Sidebar navigation buttons */
        .sidebar .stButton > button {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            background-color: transparent;
            color: #555;
            border: none;
            border-radius: 8px;
            width: 100%;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-size: 1rem;
            font-weight: 500;
        }
        .sidebar .stButton > button:hover {
            background-color: #f0f2f5;
            color: #0068c9;
        }
        /* Active nav button */
        .sidebar .stButton > button.active-nav {
            background-color: #e6f0fa;
            color: #0068c9;
            font-weight: 600;
        }
        
        /* Chat assistant button (at the bottom) */
        .sidebar .stButton > button[kind="secondary"] {
            background-color: #e6f0fa;
            color: #0068c9;
            font-weight: 600;
        }
        .sidebar .stButton > button[kind="secondary"]:hover {
            background-color: #d0e0f0;
        }

        /* --- Main Content Area --- */
        /* Add left margin to offset for the fixed sidebar */
        .main-content {
            margin-left: 270px; /* Sidebar width + gap */
            padding: 2rem;
        }

        /* --- Dashboard Cards --- */
        .card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            width: 100%;
            height: 100%; /* Make cards in a row equal height */
        }
        
        /* Ensure columns have consistent height within a row */
        [data-testid="stHorizontalBlock"] {
            align-items: stretch;
        }

        /* --- Specific Card Styling --- */
        
        /* Stock Overview */
        .stock-overview-container {
            display: flex;
            justify-content: space-around;
            align-items: center;
            text-align: center;
        }
        .stock-item {
            text-align: center;
        }
        .stock-item .value {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }
        .stock-item .label {
            font-size: 0.9rem;
            color: #777;
        }
        .low-stock .value { color: #d9534f; }
        .reorder .value { color: #f0ad4e; }
        .in-stock .value { color: #5cb85c; }
        
        /* Barcode Scan */
        .barcode-scan {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 1rem;
        }
        .barcode-scan .stCaption {
            margin-top: 1rem;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        /* Detailed Reports */
        .report-icons {
            display: flex;
            justify-content: space-around;
            align-items: center;
            height: 100%;
        }
        .report-icon-item {
            text-align: center;
            font-size: 2.5rem;
            color: #555;
            cursor: pointer;
        }
        .report-icon-item .stCaption {
            font-size: 0.8rem;
            color: #777;
        }
        
        /* Chat Assistant Card */
        .chat-history {
            background-color: #f0f2f5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            height: 100px;
            overflow-y: auto;
        }
        .chat-history .user { font-weight: 600; color: #333; }
        .chat-history .bot { color: #0068c9; }

    </style>
    """, unsafe_allow_html=True)

# =============================================
# Helper Functions (Plotly Charts)
# =============================================

def create_stock_gauge(value, max_val, title, color):
    """Creates a gauge-like donut chart."""
    fig = go.Figure(go.Pie(
        values=[value, max_val - value],
        labels=[title, ''],
        hole=0.7,
        marker_colors=[color, '#f0f2f5'],
        textinfo='none',
        hoverinfo='none',
        sort=False,  # Keep the order
        direction='clockwise'
    ))
    fig.update_layout(
        showlegend=False,
        width=120,
        height=120,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def create_sales_chart():
    """Creates the Supplier & Sales Data bar chart."""
    data = {
        'Supplier': ['Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods',
                     'Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods'],
        'Category': ['Electronics', 'Electronics', 'Electronics', 'Apparel', 'Home Goods',
                     'Electronics', 'Electronics', 'Electronics', 'Apparel', 'Home Goods'],
        'Sales': [100, 80, 60, 40, 20, 90, 70, 50, 30, 10],
        'Legend': ['Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods',
                   'Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods']
    }
    # This is a bit of a hack to match the stacked-but-grouped look
    df = pd.DataFrame(data)
    df_top = df.iloc[:5]
    df_bottom = df.iloc[5:]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_top['Category'],
        x=df_top['Sales'],
        name='Top Suppliers (Q3)',
        orientation='h',
        marker_color='#ffb74d'
    ))
    fig.add_trace(go.Bar(
        y=df_bottom['Category'],
        x=df_bottom['Sales'],
        name='Sales by Category (Q3)',
        orientation='h',
        marker_color='#42a5f5'
    ))
    
    fig.update_layout(
        barmode='stack',
        height=300,
        margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_trend_chart():
    """Creates the Trend Performance line chart."""
    data = {
        'Date': pd.to_datetime(['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01']),
        'Product A': [40, 45, 60, 70, 90, 100],
        'Product B': [30, 50, 40, 65, 70, 80],
        'Product C': [50, 55, 70, 60, 80, 75]
    }
    df = pd.DataFrame(data).melt('Date', var_name='Product', value_name='Sales')
    
    fig = px.line(df, x='Date', y='Sales', color='Product')
    fig.update_layout(
        height=300,
        margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text=''
    )
    return fig

# =============================================
# Main App Layout
# =============================================

# Inject CSS
load_css()

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# --- Main 2-Column Layout (Sidebar + Content) ---
sidebar_col, content_col = st.columns([1, 4], gap="small")

# --- 1. Custom Sidebar ---
with sidebar_col:
    with st.container():
        st.markdown('<div class="sidebar">', unsafe_allow_html=True)
        
        # Navigation Buttons
        nav_items = ["Dashboard", "Inventory", "Suppliers", "Orders", "Settings"]
        icons = ["🏠", "📦", "👥", "🛒", "⚙️"]
        
        for item, icon in zip(nav_items, icons):
            is_active = (st.session_state.page == item)
            # We use a bit of JS to add the active class
            button_html = f"""
            <button class="stButton" style="width: 100%;">
                <div class="{"active-nav" if is_active else ""}" style="width: 100%; text-align: left;">
                    {icon} &nbsp; {item}
                </div>
            </button>
            """
            if st.button(f"{icon} {item}", key=f"nav_{item}", use_container_width=True):
                st.session_state.page = item
                st.rerun()

        # Spacer
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Chat Assistant Button
        if st.button("💬 Chat Assistant", key="nav_chat", use_container_width=True, type="secondary"):
            st.session_state.page = "Chat"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# --- 2. Main Content Area ---
with content_col:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # --- Dashboard Page ---
    if st.session_state.page == "Dashboard":
        
        # --- Row 1 ---
        r1c1, r1c2 = st.columns([2, 1], gap="large")
        
        with r1c1:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Stock Overview")
                
                # We use Plotly for the gauges
                g1, g2, g3 = st.columns(3)
                with g1:
                    st.plotly_chart(create_stock_gauge(47, 200, 'Low', '#d9534f'), use_container_width=True)
                    st.markdown("<div class='stock-item low-stock'><p class='value'>47</p><p class='label'>Low Stock</p></div>", unsafe_allow_html=True)
                with g2:
                    st.plotly_chart(create_stock_gauge(120, 200, 'Reorder', '#f0ad4e'), use_container_width=True)
                    st.markdown("<div class='stock-item reorder'><p class='value'>120</p><p class='label'>Reorder</p></div>", unsafe_allow_html=True)
                with g3:
                    st.plotly_chart(create_stock_gauge(890, 1000, 'In Stock', '#5cb85c'), use_container_width=True)
                    st.markdown("<div class='stock-item in-stock'><p class='value'>890</p><p class='label'>In Stock</p></div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

        with r1c2:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Barcode Scan")
                st.markdown('<div class="barcode-scan">', unsafe_allow_html=True)
                st.markdown(r"")
                st.caption("SCANNING...")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---") # Visual spacer

        # --- Row 2 ---
        r2c1, r2c2 = st.columns([2, 1], gap="large")
        
        with r2c1:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Supplier & Sales Data")
                st.plotly_chart(create_sales_chart(), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
        with r2c2:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Detailed Reports")
                st.markdown('<div class="report-icons">', unsafe_allow_html=True)
                st.markdown('<div class="report-icon-item">📦<br><caption class="stCaption">Inventory</caption></div>', unsafe_allow_html=True)
                st.markdown('<div class="report-icon-item">📈<br><caption class="stCaption">Movement</caption></div>', unsafe_allow_html=True)
                st.markdown('<div class="report-icon-item">📜<br><caption class="stCaption">History</caption></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---") # Visual spacer

        # --- Row 3 ---
        r3c1, r3c2 = st.columns([1, 1], gap="large")
        
        with r3c1:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Chat Assistant")
                st.markdown('<div class="chat-history">', unsafe_allow_html=True)
                st.markdown('<span class="user">User:</span> Check stock for SKU 789')
                st.markdown('<span class="bot">Bot:</span> SKU: 150 units available. Supplier: Acme Corp.')
                st.markdown('</div>', unsafe_allow_html=True)
                st.text_input("Type your query...")
                st.markdown('</div>', unsafe_allow_html=True)

        with r3c2:
            with st.container(border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Trend Performance")
                st.plotly_chart(create_trend_chart(), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- Other Pages (Placeholders) ---
    elif st.session_state.page == "Inventory":
        st.title("📦 Inventory Management")
        st.info("This is where the inventory grid/table would go.")
        
    elif st.session_state.page == "Suppliers":
        st.title("👥 Suppliers")
        st.info("This is where the supplier management list would go.")
        
    elif st.session_state.page == "Orders":
        st.title("🛒 Orders")
        st.info("This is where the order tracking page would go.")
        
    elif st.session_state.page == "Settings":
        st.title("⚙️ Settings")
        st.info("This is where the app settings would go.")
        
    elif st.session_state.page == "Chat":
        st.title("💬 Chat Assistant")
        st.info("This is where the full chat interface would go.")

    st.markdown('</div>', unsafe_allow_html=True)
    
