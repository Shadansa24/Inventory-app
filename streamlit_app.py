import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# --- إعدادات الصفحة ---
# Set page configuration to wide mode for a dashboard layout
st.set_page_config(layout="wide")

# --- حقن CSS مخصص لتحقيق التنظيم والاحترافية ---
def load_css():
    st.markdown("""
        <style>
            /* --- إعدادات عامة وتعديل حاويات Streamlit --- */
            .stApp {
                background-color: #F0F4F8; 
            }
            /* تقليل الـ Padding الافتراضي حول المحتوى */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            /* تقليل الـ Padding بين الأعمدة */
            .st-emotion-cache-z5fcl4 { 
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            /* --- تصميم البطاقات الرئيسية (تعديل حاويات Streamlit) --- */
            .st-emotion-cache-1ky897g, .st-emotion-cache-1629p8f, .st-emotion-cache-1cpx6h0 {
                background-color: white !important;
                border-radius: 20px; 
                padding: 25px;
                box-shadow: 0 5px 10px -2px rgba(0, 0, 0, 0.08); /* ظل أكثر احترافية */
                margin-bottom: 20px;
                height: 350px; 
                overflow: hidden; 
            }
            
            /* --- شريط التنقل (Navigation Bar) --- */
            .nav-card {
                background-color: white;
                border-radius: 20px;
                padding: 20px;
                box-shadow: 0 5px 10px -2px rgba(0, 0, 0, 0.08);
                height: 100%;
                min-height: 1090px;
                /* استخدام Flexbox لتنظيم العناصر (الرئيسية في الأعلى، الدردشة في الأسفل) */
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .nav-group-top {
                flex-grow: 1; /* يسمح للعناصر بالنمو */
            }
            .nav-item {
                display: flex;
                align-items: center;
                padding: 12px 15px; /* زيادة Padding */
                font-size: 1rem;
                font-weight: 500;
                color: #555;
                border-radius: 10px;
                margin-bottom: 5px; /* تقليل المسافة بين العناصر */
                transition: all 0.2s;
            }
            .nav-item:hover {
                background-color: #E6EBF0; /* Light hover effect */
                color: #000;
            }
            .nav-item.active {
                background-color: #E0E8F0; 
                font-weight: 600;
                color: #007AFF; /* لون أزرق مميز */
            }
            .nav-item span {
                margin-right: 15px; /* زيادة المسافة للأيقونة */
                font-size: 1.1rem;
            }

            /* --- العناوين داخل البطاقات --- */
            .card-title {
                font-size: 1.25rem;
                font-weight: 700; /* جعل الخط أثقل */
                color: #222;
                margin-bottom: 15px;
            }

            /* --- تنسيقات KPIs ومؤشرات الأداء --- */
            .kpi-metric { text-align: center; }
            .kpi-title { font-size: 0.9rem; color: #888; margin-top: 5px;}
            .kpi-number { font-size: 1.5rem; font-weight: 700; }
            .kpi-items { font-size: 0.9rem; color: #888; }
            
            /* --- تنسيق الدردشة لتبدو نظيفة --- */
            .chat-bubble { padding: 8px 12px; border-radius: 15px; margin-bottom: 10px; max-width: 80%; line-height: 1.4; }
            .user-msg { background-color: #F0F4F8; text-align: right; margin-left: 20%; }
            .bot-msg { background-color: #E0E8F0; margin-right: 20%; }
            
            /* --- وسيلة الإيضاح المخصصة --- */
            .custom-legend { padding-left: 10px; }
            .legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.95rem; }
            .legend-color-box { width: 15px; height: 15px; border-radius: 4px; margin-right: 10px; }

        </style>
    """, unsafe_allow_html=True)

# --- دالات إنشاء المكونات ---

def render_sidebar():
    """تنظيم شريط التنقل إلى مجموعتين: أساسية ومساعدة."""
    st.markdown("""
        <div class="nav-card">
            <div class="nav-group-top">
                <div class="nav-item active"><span>📊</span> Dashboard</div>
                <div class="nav-item"><span>📦</span> Inventory</div>
                <div class="nav-item"><span>🚚</span> Suppliers</div>
                <div class="nav-item"><span>🛒</span> Orders</div>
                <div class="nav-item"><span>⚙️</span> Settings</div>
            </div>
            <div class="nav-group-bottom">
                <div class="nav-item"><span>💬</span> Chat Assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_stock_overview():
    """عرض بيانات نظرة عامة على المخزون (KPIs)."""
    with st.container():
        st.markdown('<div class="card-title">Stock Overview</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        # Helper function to create the donut gauge
        def create_kpi_gauge(value, title, color):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = value,
                number = {'font': {'size': 36}},
                gauge = {
                    'axis': {'range': [None, 1000], 'visible': False}, # Max range adjusted
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

def render_supplier_sales():
    """عرض بيانات الموردين والمبيعات (مخطط أفقي ووسيلة إيضاح)."""
    with st.container():
        st.markdown('<div class="card-title">Supplier & Sales Data</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])

        # --- بيانات الرسم البياني ---
        supplier_data = {
            'Supplier': ['Electronics', 'Global Goods', 'Apparel', 'Home Goods', 'Acme Corp', 'Innovate Ltd'],
            'Sales': [150, 120, 100, 90, 200, 180],
            'Color': ['#3498DB', '#F39C12', '#2ECC71', '#E74C3C', '#9B59B6', '#1ABC9C']
        }
        df = pd.DataFrame(supplier_data)
        
        custom_order = ['Acme Corp', 'Innovate Ltd', 'Global Goods', 'Apparel', 'Home Goods', 'Electronics']
        df = df.set_index('Supplier').loc[custom_order].reset_index()

        # إنشاء المخطط الأفقي
        with col1:
            st.markdown("<b>Top Suppliers (Q3)</b>", unsafe_allow_html=True)
            fig = go.Figure()
            
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

def render_chat_assistant():
    """عرض واجهة مساعد الدردشة (Mockup)."""
    with st.container():
        st.markdown('<div class="card-title">Chat Assistant</div>', unsafe_allow_html=True)
        
        # واجهة الدردشة الوهمية
        st.markdown("""
            <div style="display: flex; flex-direction: column; height: 80%; justify-content: space-between;">
                <div style="overflow-y: auto;">
                    <div class="chat-bubble user-msg">
                        User: Check stock for SKU 789
                    </div>
                    <div class="chat-bubble bot-msg">
                        Bot: SKU: 150 units available.<br>Supplier: Acme Corp.
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <!-- مربع الإدخال -->
                    <input type="text" placeholder="Type your query..." style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 10px; font-size: 1rem;">
                </div>
            </div>
        """, unsafe_allow_html=True)
        # Note: Using native HTML input instead of st.text_input to style it better inside the container

def render_trend_performance():
    """عرض بيانات الأداء والاتجاه (Trend Performance)."""
    with st.container():
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


# --- التخطيط الرئيسي للتطبيق ---

# تحميل الـ CSS
load_css()

# إنشاء التخطيط (Layout)
col_nav, col_content = st.columns([1, 4])

with col_nav:
    render_sidebar()

with col_content:
    # الصف الأول: ملخص المخزون
    render_stock_overview()

    # الصف الثاني: بيانات الموردين
    render_supplier_sales()

    # الصف الثالث: الدردشة والأداء
    col1, col2 = st.columns(2)
    with col1:
        render_chat_assistant()
    with col2:
        render_trend_performance()
