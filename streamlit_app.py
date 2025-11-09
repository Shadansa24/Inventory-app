import streamlit as st
import pandas as pd
import openai
import os

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="Inventory Dashboard", layout="wide")
st.markdown(
    """
    <style>
    .main {background-color:#f8f9fa;}
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Load Data
# -----------------------------
DATA_PATH = "data/products.csv"

try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    st.error("❌ Could not find 'data/products.csv'. Upload it and redeploy.")
    st.stop()

df.columns = df.columns.str.strip()

if not {"Quantity", "Threshold"}.issubset(df.columns):
    st.error("Your CSV must include columns named 'Quantity' and 'Threshold'.")
    st.stop()

# -----------------------------
# Header
# -----------------------------
st.title("📊 Smart Inventory Dashboard")
st.caption("Monitor product stock levels and detect low inventory in real time.")

# -----------------------------
# KPI Metrics
# -----------------------------
total_products = len(df)
low_stock_count = (df["Quantity"] < df["Threshold"]).sum()
sufficient_stock = (df["Quantity"] >= df["Threshold"]).sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total Products", total_products)
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Low Stock", low_stock_count)
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Sufficient Stock", sufficient_stock)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# Low-Stock Table
# -----------------------------
st.subheader("⚠️ Low Stock Products")
low_stock_df = df[df["Quantity"] < df["Threshold"]]

if low_stock_df.empty:
    st.success("All products are sufficiently stocked ✅")
else:
    st.dataframe(low_stock_df.style.highlight_min(subset=["Quantity"], color="#ffcccc"))

# -----------------------------
# Optional: Chat Assistant
# -----------------------------
st.subheader("💬 Ask the Inventory Assistant")

openai.api_key = (
    os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
)
user_query = st.text_input("Ask a question (e.g., 'Which items need restocking?')")

if user_query and openai.api_key:
    summary = "\n".join(
        f"{row['Name']} ({row['Category']}): {row['Quantity']} units, threshold {row['Threshold']}"
        for _, row in df.iterrows()
    )
    prompt = f"Inventory data:\n{summary}\n\nUser question: {user_query}"
    try:
        with st.spinner("Analyzing..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert inventory analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        st.success(response.choices[0].message["content"].strip())
    except Exception as e:
        st.error(f"OpenAI error: {e}")
elif user_query and not openai.api_key:
    st.warning("Set your OpenAI API key in Streamlit Secrets to enable chat.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("© 2025 Smart Inventory Dashboard | Built with Streamlit + OpenAI API")
