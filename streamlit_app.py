import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from streamlit_option_menu import option_menu

# --- Page configuration ---
st.set_page_config(page_title="Inventory Management System", layout="wide")

# --- CSS Styling ---
st.markdown("""
<style>
/* General cards */
.card {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    box-shadow: rgba(0, 0, 0, 0.1) 0px 2px 12px 0px;
    margin-bottom: 1.5rem;
}

/* Sidebar option menu styling overrides */
.sidebar .css-1d391kg {
    padding-top: 1rem;
}
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

/* Chat assistant styling */
.chat-box {
    max-height: 140px;
    overflow-y: auto;
    background:#f0f5fa;
    border-radius: 8px;
    padding: 12px;
    font-size: 0.9rem;
    color: #333;
    margin-bottom: 1rem;
}

.chat-user {
    color: #034069;
    font-weight: 600;
    margin-bottom: 4px;
}

.chat-bot {
    color: #0b6069;
    font-style: italic;
    margin-bottom: 8px;
}

/* Barcode scan styling */
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
    padding: 0.3rem 0.6rem;
    user-select: none;
}

.barcode-label {
    font-size: 0.8rem;
    color: #777;
    margin-top: 0.5rem;
}

/* Detailed reports styling */
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

/* Metric number styling */
.metric-text {
    font-size: 1rem;
    margin-top: 4px;
    color: #555;
}

</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Inventory", "Suppliers", "Orders", "Settings", "Chat Assistant"],
        icons=["speedometer2", "box-seam", "people", "receipt", "gear", "chat-dots"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px 0 10px 0"},
            "icon": {"color": "#6c757d", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "3px 0", "--hover-color": "#e1e7f0"},
            "nav-link-selected": {"background-color": "#d1dde9", "font-weight": "600"},
        },
    )

# --- Helper functions ---
def draw_gauge(value, max_value, label, color):
    fig, ax = plt.subplots(figsize=(1.6, 1.6), dpi=80)
    ax.axis('equal')
    # Background arc
    arc_bg = Wedge((0, 0), 1, 180, 360, facecolor="#ECECEC", edgecolor='none')
    ax.add_patch(arc_bg)
    # Value arc
    theta2 = 180 + (value / max_value) * 180
    arc_val = Wedge((0, 0), 1, 180, theta2, facecolor=color, edgecolor='none')
    ax.add_patch(arc_val)
    # Needle
    needle_length = 0.9
    needle_angle = np.radians(theta2)
    ax.plot([0, needle_length * np.cos(needle_angle)], [0, needle_length * np.sin(needle_angle)], color='black', linewidth=2)
    # Center circle
    center_circle = plt.Circle((0, 0), 0.1, color='black')
    ax.add_patch(center_circle)
    # Text
    ax.text(0, -0.2, f"{label}\n{value}", ha='center', va='center', fontsize=12, weight='bold')
    ax.axis('off')
    return fig

def plot_supplier_sales():
    data = {
        "Acme Corp": [40, 30, 20],
        "Innovate Ltd": [25, 35, 15],
        "Global Goods": [22, 18, 30]
    }
    categories = ["Electronics", "Apparel", "Home Goods"]
    df = pd.DataFrame(data, index=categories)

    fig, ax = plt.subplots(figsize=(6,2))
    df.plot(kind='barh', stacked=False, ax=ax, color=['#377eb8', '#4daf4a', '#ff7f00'])
    ax.set_xlabel('Sales')
    ax.set_xlim(0, 60)
    ax.legend(title="Suppliers", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    return fig

def plot_trend_performance():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    product_A = [20, 40, 50, 70, 90, 100]
    product_B = [15, 35, 45, 65, 85, 95]

    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(months, product_A, marker='o', label='Product A', color='#1f77b4')
    ax.plot(months, product_B, marker='o', label='Product B', color='#ff7f0e')
    ax.set_ylabel('Units Sold')
    ax.set_xlabel('Month')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    return fig

# --- Page content ---
if selected == "Dashboard":
    st.title("Inventory Management Dashboard")

    col1, col2 = st.columns([2.5, 1])

    with col1:
        # Stock Overview card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Stock Overview")
        col_low, col_reorder, col_instock = st.columns(3)

        with col_low:
            fig = draw_gauge(47, 150, "Low Stock", "#d9534f")
            st.pyplot(fig, use_container_width=True)
            st.markdown('<div class="metric-text">47 Items</div>', unsafe_allow_html=True)
        with col_reorder:
            fig = draw_gauge(120, 150, "Reorder", "#f0ad4e")
            st.pyplot(fig, use_container_width=True)
            st.markdown('<div class="metric-text">120 Items</div>', unsafe_allow_html=True)
        with col_instock:
            fig = draw_gauge(890, 1500, "In Stock", "#5cb85c")
            st.pyplot(fig, use_container_width=True)
            st.markdown('<div class="metric-text">890 Items</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Supplier & Sales Data card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Supplier & Sales Data")
        fig = plot_supplier_sales()
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

        # Detailed Reports card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Detailed Reports")
        st.markdown("""
        <div class="report-item">&#128218; Inventory History</div>
        <div class="report-item">&#128203; Movement History</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Barcode Scan card
        st.markdown('<div class="card barcode-box">', unsafe_allow_html=True)
        st.write("### Barcode Scan")
        st.markdown('<div class="barcode-placeholder">| | | |  3 0 0 0  3 9 2 0 | | | |</div>', unsafe_allow_html=True)
        st.markdown('<div class="barcode-label">SCANNING..</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat Assistant card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("### Chat Assistant")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        def add_message(user_msg, bot_msg):
            st.session_state.chat_history.append({"user": user_msg, "bot": bot_msg})

        query = st.text_input("Type your query here:", key="chat_input")
        if query:
            if "supplier" in query.lower() and "sku 789" in query.lower():
                add_message(query, "SKU 150 units available. Supplier: Acme Corp.")
            else:
                add_message(query, "Sorry, I didn't understand the query.")
            st.experimental_rerun()

        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for chat in st.session_state.chat_history:
            st.markdown(f"<div class='chat-user'>User: {chat['user']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-bot'>Bot: {chat['bot']}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Trend Performance card full width below
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Trend Performance - Top-Selling Products")
    fig = plot_trend_performance()
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

elif selected == "Inventory":
    st.title("Inventory Management")
    st.markdown('<div class="card"><em>Inventory details and management features coming soon...</em></div>', unsafe_allow_html=True)

elif selected == "Suppliers":
    st.title("Suppliers")
    st.markdown('<div class="card"><em>Supplier profiles and contacts coming soon...</em></div>', unsafe_allow_html=True)

elif selected == "Orders":
    st.title("Orders")
    st.markdown('<div class="card"><em>Order processing and history coming soon...</em></div>', unsafe_allow_html=True)

elif selected == "Settings":
    st.title("Settings")
    st.markdown('<div class="card"><em>Application settings and preferences coming soon...</em></div>', unsafe_allow_html=True)

elif selected == "Chat Assistant":
    st.title("Chat Assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def add_message(user_msg, bot_msg):
        st.session_state.chat_history.append({"user": user_msg, "bot": bot_msg})

    query = st.text_input("Type your query here:", key="chat_page_input")
    if query:
        if "supplier" in query.lower() and "sku 789" in query.lower():
            add_message(query, "SKU 150 units available. Supplier: Acme Corp.")
        else:
            add_message(query, "Sorry, I didn't understand the query.")
        st.experimental_rerun()

    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for chat in st.session_state.chat_history:
        st.markdown(f"<div class='chat-user'>User: {chat['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bot'>Bot: {chat['bot']}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
