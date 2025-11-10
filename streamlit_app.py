import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# --- إعدادات الصفحة ---
# Set page configuration to wide mode for a dashboard layout
st.set_page_config(layout="wide")

# --- حقن CSS مخصص ---
# This is the core logic to make the Streamlit app look like the target design.
# We are manually injecting CSS to style components.
def load_css():
    st.markdown("""
        <style>
            /* --- إعدادات عامة --- */
            /* Set the main background color for the app */
            .stApp {
                background-color: #F0F4F8; /* Light blue-gray background */
            }

            /* Remove default Streamlit padding at the top */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            /* --- تصميم البطاقات (Cards) --- */
            /* This is the main style for all white containers */
            .card {
                background-color: white;
                border-radius: 20px; /* Rounded corners */
                padding: 25px; /* Inner spacing */
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* Soft shadow */
                margin-bottom: 20px; /* Space between cards */
                height: 350px; /* Fixed height for better alignment */
            }
            
            /* Taller card for the trend chart */
            .card-tall {
                height: 400px;
            }
            
            /* Shorter card for detailed reports */
            .card-short {
                height: 250px;
            }
            
            /* Special card for the nav bar */
            .nav-card {
                background-color: white;
                border-radius: 20px;
                padding: 20px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                height: 100%; /* Fill the column height */
            }

            /* --- العناوين داخل البطاقات --- */
            .card-title {
                font-size: 1.25rem; /* 20px */
                font-weight: 600;
                color: #333;
                margin-bottom: 15px;
            }

            /* --- شريط التنقل الجانبي (المزيف) --- */
            .nav-item {
                display: flex;
                align-items: center;
                padding: 10px 15px;
                font-size: 1rem;
                font-weight: 500;
                color: #555;
                border-radius: 10px;
                margin-bottom: 10px;
                transition: all 0.2s;
            }
            .nav-item:hover {
                background-color: #F0F4F8; /* Light hover effect */
                color: #000;
            }
            .nav-item.active {
                background-color: #E0E8F0; /* Active state */
                font-weight: 600;
            }
            .nav-item span {
                margin-right: 10px;
            }

            /* --- بطاقة ملخص المخزون (Stock Overview) --- */
            .kpi-metric {
                text-align: center;
            }
            .kpi-title {
                font-size: 0.9rem;
                color: #888;
            }
            .kpi-number {
                font-size: 1.5rem;
                font-weight: 600;
            }
            .kpi-items {
                font-size: 0.9rem;
                color: #888;
            }

            /* --- بطاقة ماسح الباركود (المزيفة) --- */
            .scanner-box {
                background-color: #f9f9f9;
                border: 2px dashed #ddd;
                border-radius: 10px;
                height: 150px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 4rem;
                color: #555;
                user-select: none; /* Disable text selection */
            }
            .scanner-text {
                text-align: center;
                margin-top: 15px;
                font-weight: 500;
                color: #777;
                letter-spacing: 1.5px;
            }

            /* --- بطاقة التقارير المفصلة --- */
            .report-icon-container {
                text-align: center;
                padding: 20px;
            }
            .report-icon {
                font-size: 2.5rem;
                color: #4A90E2; /* Icon color */
            }
            .report-label {
                margin-top: 10px;
                font-weight: 500;
                color: #555;
            }
            
            /* --- بطاقة مساعد الدردشة --- */
            .chat-input {
                margin-bottom: 15px;
            }
            .chat-bubble {
                padding: 8px 12px;
                border-radius: 10px;
                margin-bottom: 10px;
                max-width: 80%;
            }
            .user-msg {
                background-color: #F0F4F8;
                align-self: flex-end;
                text-align: right;
                margin-left: 20%;
            }
            .bot-msg {
                background-color: #E0E8F0;
                align-self: flex-start;
                margin-right: 20%;
            }
            
            /* --- وسيلة الإيضاح المخصصة (Custom Legend) --- */
            .custom-legend {
                padding-left: 10px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }
            .legend-color-box {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                margin-right: 10px;
            }

        </style>
    """, unsafe_allow_html=True)

# --- دالات إنشاء المكونات ---

def render_sidebar():
    """Renders the navigation sidebar in the first column."""
    with st.container():
        # This HTML/CSS creates the visual sidebar
        st.markdown(f"""
            <div class="nav-card" style="height: 1190px;">
                <div class="nav-item active"><span>📊</span> Dashboard</div>
                <div class="nav-item"><span>📦</span> Inventory</div>
                <div class="nav-item"><span>🚚</span> Suppliers</div>
                <div class="nav-item"><span>🛒</span> Orders</div>
                <div class="nav-item"><span>⚙️</span> Settings</div>
                <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
                <div class="nav-item"><span>💬</span> Chat Assistant</div>
            </div>
        """, unsafe_allow_html=True)

def render_stock_overview():
    """Renders the 'Stock Overview' card with 3 KPI donuts."""
    st.markdown('<div class="card card-tall">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Helper function to create the donut gauge
    def create_kpi_gauge(value, title, color):
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            number = {'font': {'size': 36}},
            gauge = {
                'axis': {'range': [None, 150], 'visible': False}, # Max range (adjust as needed)
                'bar': {'color': color, 'thickness': 0.15},
                'bgcolor': "#f0f0f0",
                'borderwidth': 0,
                'shape': 'angular'
            },
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(
            height=150,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="white",
            font_color="#333"
        )
        return fig

    # KPI 1: Low Stock
    with col1:
        st.plotly_chart(create_kpi_gauge(47, "Low Stock", "#E74C3C"), use_container_width=True)
        st.markdown(f"""
            <div class="kpi-metric">
                <div class="kpi-title">Low Stock</div>
                <div class="kpi-number" style="color: #E74C3C;">47</div>
                <div class="kpi-items">47 Items</div>
            </div>
        """, unsafe_allow_html=True)

    # KPI 2: Reorder
    with col2:
        st.plotly_chart(create_kpi_gauge(120, "Reorder", "#F39C12"), use_container_width=True)
        st.markdown(f"""
            <div class="kpi-metric">
                <div class="kpi-title">Reorder</div>
                <div class="kpi-number" style="color: #F39C12;">120</div>
                <div class="kpi-items">120 Items</div>
            </div>
        """, unsafe_allow_html=True)
        
    # KPI 3: In Stock
    with col3:
        st.plotly_chart(create_kpi_gauge(890, "In Stock", "#2ECC71"), use_container_width=True)
        st.markdown(f"""
            <div class="kpi-metric">
                <div class="kpi-title">In Stock</div>
                <div class="kpi-number" style="color: #2ECC71;">890</div>
                <div class="kpi-items">890 Items</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_barcode_scanner():
    """Renders the 'Barcode Scan' placeholder card."""
    st.markdown('<div class="card card-tall">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Barcode Scan</div>', unsafe_allow_html=True)
    
    # This is a static placeholder to mimic the image. NO real scanner.
    st.markdown("""
        <div class="scanner-box">
            <span style="font-family: 'Libre Barcode 39', cursive;">||| || |||</span>
        </div>
        <div class="scanner-text">SCANNING...</div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_supplier_sales():
    """Renders the 'Supplier & Sales Data' card."""
    st.markdown('<div class="card card-tall">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Supplier & Sales Data</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])

    # --- بيانات الرسم البياني ---
    supplier_data = {
        'Supplier': ['Electronics', 'Global Goods', 'Apparel', 'Home Goods', 'Acme Corp', 'Innovate Ltd'],
        'Sales': [150, 120, 100, 90, 200, 180],
        'Category': ['Electronics', 'Global Goods', 'Apparel', 'Home Goods', 'Acme Corp', 'Innovate Ltd'],
        'Color': ['#3498DB', '#F39C12', '#2ECC71', '#E74C3C', '#9B59B6', '#1ABC9C']
    }
    df = pd.DataFrame(supplier_data)
    
    # فرز البيانات كما في الصورة (يبدو أنها مخصصة)
    custom_order = ['Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods', 'Electronics']
    df = df.set_index('Supplier').loc[custom_order].reset_index()

    # إنشاء المخطط الأفقي
    with col1:
        st.markdown("<b>Top Suppliers (Q3)</b>", unsafe_allow_html=True)
        fig = go.Figure()
        
        # إضافة الأشرطة لونًا بلون
        for i, row in df.iterrows():
            fig.add_trace(go.Bar(
                y=[row['Supplier']],
                x=[row['Sales']],
                name=row['Supplier'],
                orientation='h',
                marker_color=row['Color'],
                showlegend=False
            ))
            
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            barmode='stack',
            yaxis=dict(
                categoryorder='array',
                categoryarray=custom_order,
                showline=False,
                showgrid=False
            ),
            xaxis=dict(
                showgrid=False,
                showline=False,
                showticklabels=False
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- وسيلة الإيضاح المخصصة (Custom Legend) ---
    with col2:
        st.markdown("<div class='custom-legend'><b>Sales by Category (Q3)</b>", unsafe_allow_html=True)
        
        # بيانات وسيلة الإيضاح
        legend_items = {
            'Acme Corp': '#3498DB',
            'Innovate Ltd': '#F39C12',
            'Global Goods': '#2ECC71',
            'Apparel': '#E74C3C',
            'Home Goods': '#9B59B6'
        }
        
        for item, color in legend_items.items():
            st.markdown(f"""
                <div class="legend-item">
                    <div class="legend-color-box" style="background-color: {color};"></div>
                    {item}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_detailed_reports():
    """Renders the 'Detailed Reports' card."""
    st.markdown('<div class="card card-short">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Detailed Reports</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="report-icon-container">
                <div class="report-icon">📈</div>
                <div class="report-label">Inventory</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="report-icon-container">
                <div class="report-icon">🔄</div>
                <div class="report-label">Movement</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div class="report-icon-container">
                <div class="report-icon">📜</div>
                <div class="report-label">History</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_assistant():
    """Renders the 'Chat Assistant' card."""
    st.markdown('<div class="card card-tall">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
    
    # واجهة الدردشة الوهمية
    st.markdown("""
        <div class="chat-bubble user-msg">
            User: Check stock for SKU 789
        </div>
        <div class="chat-bubble bot-msg">
            Bot: SKU: 150 units available.<br>Supplier: Acme Corp.
        </div>
    """, unsafe_allow_html=True)
    
    # مربع الإدخال الحقيقي
    st.text_input("Type your query...", placeholder="Type your query...", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_trend_performance():
    """Renders the 'Trend Performance' card."""
    st.markdown('<div class="card card-tall">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Trend Performance</div>', unsafe_allow_html=True)

    # --- بيانات المخطط الخطي ---
    trend_data = {
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Product A': [40, 45, 60, 55, 70, 85],
        'Product B': [30, 50, 40, 65, 60, 75],
        'Product C': [50, 35, 55, 45, 50, 60]
    }
    df_trend = pd.DataFrame(trend_data)

    fig = go.Figure()
    
    # إضافة الخطوط
    fig.add_trace(go.Scatter(
        x=df_trend['Month'], y=df_trend['Product A'],
        mode='lines+markers', name='Product A',
        line=dict(color='#007AFF', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=df_trend['Month'], y=df_trend['Product B'],
        mode='lines+markers', name='Product B',
        line=dict(color='#FF9500', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=df_trend['Month'], y=df_trend['Product C'],
        mode='lines+markers', name='Product C',
        line=dict(color='#34C759', width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title='Top-Selling Products',
        title_x=0.5,
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#eee'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- التخطيط الرئيسي للتطبيق ---

# تحميل الـ CSS
load_css()

# إنشاء التخطيط (Layout)
# العمود 1: شريط التنقل
# العمود 2: المحتوى الرئيسي
col_nav, col_content = st.columns([1, 4])

with col_nav:
    render_sidebar()

with col_content:
    # الصف الأول من المحتوى
    col1, col2 = st.columns([2, 1])
    with col1:
        render_stock_overview()
    with col2:
        render_barcode_scanner()

    # الصف الثاني من المحتوى
    col3, col4 = st.columns([2, 1])
    with col3:
        render_supplier_sales()
    with col4:
        render_detailed_reports()

    # الصف الثالث من المحتوى
    col5, col6 = st.columns([1, 1])
    with col5:
        render_chat_assistant()
    with col6:
        render_trend_performance()
