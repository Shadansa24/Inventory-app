import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.lines import Line2D

# Set page layout
st.set_page_config(layout="wide", page_title="Inventory Dashboard")

# Custom CSS for styling
st.markdown("""
<style>
/* Sidebar */
.sidebar .css-1d391kg {padding-top: 1rem;}

/* Sidebar menu items */
.sidebar .css-1d391kg > div:nth-child(1) {
    margin-bottom: 1.5rem;
}

/* Cards */
.card {
    background-color: #fff;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    box-shadow: rgba(0, 0, 0, 0.1) 0px 2px 12px 0px;
    margin-bottom: 1.5rem;
}

/* Sidebar icons & text*/
.sidebar .css-1d391kg label {
    font-size: 1.1rem;
    margin-left: 0.75rem;
}

.sidebar .css-1d391kg div[role="radiogroup"] > div {
    align-items: center;
    display: flex;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}

.sidebar .css-1d391kg div[role="radiogroup"] > div:hover {
    background-color: #e1e7f0;
}

.sidebar .css-1d391kg div[role="radiogroup"] > div:has(input:checked) {
    background-color: #d1dde9;
    font-weight: 600;
}

/* Custom scrollbar for chat */
.chat-box {
    max-height: 130px;
    overflow-y: auto;
    background:#f0f5fa;
    border-radius: 8px;
    padding: 10px;
    font-size: 0.9rem;
    color: #333;
    margin-bottom: 1rem;
}

.chat-user {
    color: #034069;
    font-weight: bold;
}

.chat-bot {
    color: #0b6069;
    font-style: italic;
}

/* Barcode box */
.barcode-box {
    background-color: #e6e9f0;
    border-radius: 12px;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: inset 0 0 5px #c9c9c9;
    margin-bottom: 1rem;
}

.barcode-placeholder {
    font-size: 1rem;
    letter-spacing: 3px;
    font-family: monospace;
    border: 2px solid #999;
    padding: 0.25rem 0.5rem;
    margin-top: 0.25rem;
    user-select: none;
}

.barcode-label {
    font-size: 0.8rem;
    color: #777;
    margin-top: 0.5rem;
}

/* Detailed reports */
.report-item {
    cursor: pointer;
    padding: 10px 0;
    display: flex;
    align-items: center;
}

.report-icon {
    margin-right: 0.75rem;
    font-size: 20px;
}

/* Adjust layout margins */
.main-col {
    padding: 0 1.5rem;
}

.stButton button {
    background-color: #1976D2;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Sidebar with icons & text
from streamlit_option_menu import option_menu

with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Inventory", "Suppliers", "Orders", "Settings", "Chat Assistant"],
        icons=["speedometer2", "box-seam", "people", "receipt", "gear", "chat-dots"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px 0px 10px 0px"},
            "icon": {"color": "#6c757d", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "3px 0", "--hover-color": "#e1e7f0"},
            "nav-link-selected": {"background-color": "#d1dde9", "font-weight": "600"},
        },
    )

if selected == "Dashboard":

    st.markdown("<h2 style='margin-bottom:1rem;'>Inventory Management Dashboard</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([2.5, 1])

    with col1:

        # Stock Overview Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Stock Overview")
        col_low, col_reorder, col_instock = st.columns(3)

        def draw_gauge(value, label, color):
            fig, ax = plt.subplots(figsize=(1.8, 1.8))
            ax.axis('equal')
            wedge = Wedge(center=(0,0), r=1, theta1=180, theta2=180 + (value/150)*180, facecolor=color, edgecolor='lightgray', lw=15)
            ax.add_patch(wedge)
            ax.plot([0, np.cos(np.radians(180 + (value/150)*180))], [0, np.sin(np.radians(180 + (value/150)*180))], color='black', lw=2)
            ax.text(0, -0.2, f"{label}\n{value}", ha='center', va='center', fontsize=12)
            ax.axis('off')
            plt.tight_layout()
            return fig

        with col_low:
            st.pyplot(draw_gauge(47, "Low Stock", "#d9534f"), clear_figure=True)
            st.markdown("47 Items", unsafe_allow_html=True)
        with col_reorder:
            st.pyplot(draw_gauge(120, "Reorder", "#f0ad4e"), clear_figure=True)
            st.markdown("120 Items", unsafe_allow_html=True)
        with col_instock:
            st.pyplot(draw_gauge(890, "In Stock", "#5cb85c"), clear_figure=True)
            st.markdown("890 Items", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Supplier & Sales Data Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Supplier & Sales Data")
        data = {
            "Acme Corp": [40, 30, 20],
            "Innovate Ltd": [25, 35, 15],
            "Global Goods": [22, 18, 30]
        }
        categories = ["Electronics", "Apparel", "Home Goods"]
        df = pd.DataFrame(data, index=categories)

        # Horizontal bar chart
        fig, ax = plt.subplots(figsize=(6, 2))
        df.plot(kind='barh', stacked=False, ax=ax, color=['#377eb8', '#4daf4a', '#ff7f00'])
        ax.set_xlabel('Sales')
        ax.set_xlim(0, 60)
        ax.legend(title="Suppliers", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

        # Detailed Reports Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Detailed Reports")
        st.markdown("""
        <div class="report-item">&#128218; Inventory History</div>
        <div class="report-item">&#128203; Movement History</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Barcode Scan Card
        st.markdown('<div class="card barcode-box">', unsafe_allow_html=True)
        st.write("### Barcode Scan")
        st.markdown('<div class="barcode-placeholder">| | | |  3 0 0 0  3 9 2 0 | | | |</div>', unsafe_allow_html=True)
        st.markdown('<div class="barcode-label">SCANNING..</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat Assistant Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Chat Assistant")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        def add_message(user_msg, bot_msg):
            st.session_state.chat_history.append({"user": user_msg, "bot": bot_msg})

        query = st.text_input("Type your query here:", key="chat_input")
        if query:
            # Simple demo response logic
            if "supplier" in query.lower() and "sku 789" in query.lower():
                add_message(query, "SKU 150 units available. Supplier: Acme Corp.")
            else:
                add_message(query, "Sorry, I didn't understand the query.")
            st.experimental_rerun()

        # Chat messages display
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for chat in st.session_state.chat_history:
            st.markdown(f"<div class='chat-user'>User: {chat['user']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-bot'>Bot: {chat['bot']}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Trend Performance Card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Trend Performance - Top-Selling Products")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    product_A = [20, 40, 50, 70, 90, 100]
    product_B = [15, 35, 45, 65, 85, 95]

    fig2, ax2 = plt.subplots(figsize=(8,3))
    ax2.plot(months, product_A, marker='o', label='Product A', color='#1f77b4')
    ax2.plot(months, product_B, marker='o', label='Product B', color='#ff7f0e')

    ax2.set_ylabel('Units Sold')
    ax2.set_xlabel('Month')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig2)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title(f"{selected} section is under construction.")
