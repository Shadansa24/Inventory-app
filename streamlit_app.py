import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sidebar navigation
st.sidebar.title("Menu")
menu = st.sidebar.radio(
    "Navigation",
    ("Dashboard", "Inventory", "Suppliers", "Orders", "Settings", "Chat Assistant")
)

if menu == "Dashboard":
    st.title("Inventory Management Dashboard")

    # Stock Overview
    st.subheader("Stock Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Low Stock", value="47 Items")
    with col2:
        st.metric(label="Reorder", value="120 Items")
    with col3:
        st.metric(label="In Stock", value="890 Items")

    # Supplier & Sales Data
    st.subheader("Supplier & Sales Data (Q3)")
    suppliers = ["Acme Corp", "Innovate Ltd", "Global Goods"]
    categories = ["Electronics", "Apparel", "Home Goods"]
    sales_data = {
        "Acme Corp": [40, 30, 20],
        "Innovate Ltd": [20, 40, 30],
        "Global Goods": [30, 20, 40],
    }
    df = pd.DataFrame(sales_data, index=categories)

    fig, ax = plt.subplots()
    df.plot(kind="bar", ax=ax)
    ax.set_xlabel("Category")
    ax.set_ylabel("Sales")
    ax.legend(title="Suppliers")
    st.pyplot(fig)

    # Barcode Scan Simulation
    st.subheader("Barcode Scan")
    barcode = st.text_input("Scan or enter barcode:")
    if barcode:
        st.info(f"Scanned Barcode: {barcode}")

    # Detailed Reports
    st.subheader("Detailed Reports")
    st.write("- Inventory History")
    st.write("- Movement History")

    # Chat Assistant
    st.subheader("Chat Assistant")
    chat_query = st.text_input("Type your query here:")
    if chat_query:
        # Simulated responses for demo
        if "supplier" in chat_query.lower() and "SKU 789" in chat_query:
            st.write("User: " + chat_query)
            st.write("Bot: SKU 150 units available. Supplier: Acme Corp.")
        else:
            st.write("Bot: Sorry, I didn't understand the query.")

    # Trend Performance
    st.subheader("Trend Performance - Top-Selling Products")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    product_A_sales = [20, 40, 50, 70, 90, 100]
    product_B_sales = [15, 35, 45, 65, 85, 95]

    fig2, ax2 = plt.subplots()
    ax2.plot(months, product_A_sales, label="Product A")
    ax2.plot(months, product_B_sales, label="Product B")
    ax2.set_ylabel("Units Sold")
    ax2.set_xlabel("Month")
    ax2.legend()
    st.pyplot(fig2)

else:
    st.title(f"{menu} section is under construction.")
