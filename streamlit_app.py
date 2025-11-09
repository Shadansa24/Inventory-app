import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from st_aggrid import AgGrid, GridOptionsBuilder

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(page_title="Smart Inventory Dashboard", layout="wide")

# -----------------------------
# Custom Styling
# -----------------------------
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1, h2, h3, h4, h5 {
        font-family: 'Inter', sans-serif;
        color: #212529;
    }
    .metric-card {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Load Data
# -----------------------------
DATA_PATH = "data/products.csv"
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    st.error("❌ Could not find 'data/products.csv'. Please upload it and redeploy.")
    st.stop()

df.columns = df.columns.str.strip()
if not {"Quantity", "Threshold"}.issubset(df.columns):
    st.error("❌ Your CSV must include columns named 'Quantity' and 'Threshold'.")
    st.stop()

# -----------------------------
# Page Header
# -----------------------------
st.title("📊 Smart Inventory Dashboard")
st.caption("Monitor product stock levels and detect low inventory in real time.")

# -----------------------------
# KPI Section
# -----------------------------
total_products = len(df)
low_stock_count = (df["Quantity"] < df["Threshold"]).sum()
sufficient_stock = (df["Quantity"] >= df["Threshold"]).sum()

metric_html = f"""
<div style='display:flex; gap:1.5rem; justify-content:space-between;'>
  <div class='metric-card'>
    <h4>Total Products</h4>
    <h2 style='color:#007bff;'>{total_products}</h2>
  </div>
  <div class='metric-card'>
    <h4>Low Stock</h4>
    <h2 style='color:#dc3545;'>{low_stock_count}</h2>
  </div>
  <div class='metric-card'>
    <h4>Sufficient Stock</h4>
    <h2 style='color:#28a745;'>{sufficient_stock}</h2>
  </div>
</div>
"""
st.markdown(metric_html, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# Low Stock Products Table (AgGrid)
# -----------------------------
st.subheader("⚠️ Low Stock Products")

low_stock_df = df[df["Quantity"] < df["Threshold"]]

if low_stock_df.empty:
    st.success("✅ All products are sufficiently stocked.")
else:
    gb = GridOptionsBuilder.from_dataframe(low_stock_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(editable=False, groupable=True)
    gb.configure_side_bar()
    grid_options = gb.build()

    AgGrid(
        low_stock_df,
        gridOptions=grid_options,
        height=400,
        theme="balham",
        fit_columns_on_grid_load=True,
    )

st.markdown("---")

# -----------------------------
# OpenAI Assistant
# -----------------------------
st.subheader("💬 Ask the Inventory Assistant")

api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    st.warning("⚠️ Add your OpenAI API key in Streamlit Secrets to use the assistant.")
else:
    client = OpenAI(api_key=api_key)

user_query = st.text_input("Ask a question (e.g., 'Which products are low on stock?' or 'What is the ID for iPhone 15?')")

if user_query:
    try:
        inventory_summary = "\n".join(
            f"{row['Product_ID']}: {row['Name']} ({row['Category']}) - {row['Quantity']} units, threshold {row['Threshold']}"
            for _, row in df.iterrows()
        )
        prompt = f"Inventory Data:\n{inventory_summary}\n\nUser question: {user_query}"

        with st.spinner("Analyzing inventory..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert inventory analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )

        answer = response.choices[0].message.content.strip()
        st.success(answer)

    except Exception as e:
        st.error(f"OpenAI error: {e}")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("© 2025 Smart Inventory Dashboard | Built with Streamlit + OpenAI API + AgGrid")
