import streamlit as st
import pandas as pd
import openai
import os

# -----------------------------
# 🔧 Setup
# -----------------------------
st.set_page_config(page_title="Smart Inventory Dashboard", layout="wide")

# Load API key
openai.api_key = (
    os.getenv("OPENAI_API_KEY") 
    or st.secrets.get("OPENAI_API_KEY", None)
)

if not openai.api_key:
    st.warning("⚠️ No OpenAI API key found. Please add it in Streamlit Secrets or as an environment variable.")
    st.stop()

# -----------------------------
# 📂 Load data
# -----------------------------
DATA_PATH = "data/products.csv"

try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    st.error(f"❌ Could not find file: {DATA_PATH}. Please make sure the CSV exists.")
    st.stop()

# Clean and normalize column headers
df.columns = df.columns.str.strip()
st.write("### 🧾 Data Preview")
st.dataframe(df.head())

# -----------------------------
# 🧩 Check required columns
# -----------------------------
required_cols = {"Quantity", "Threshold"}
if not required_cols.issubset(df.columns):
    st.error(f"❌ Missing required columns: {required_cols - set(df.columns)}")
    st.info("Your CSV must include columns named 'Quantity' and 'Threshold'.")
    st.stop()

# -----------------------------
# 📊 Dashboard metrics
# -----------------------------
st.title("📊 Smart Inventory Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Products", len(df))
col2.metric("Low Stock", (df["Quantity"] < df["Threshold"]).sum())
col3.metric("Sufficient Stock", (df["Quantity"] >= df["Threshold"]).sum())

# -----------------------------
# 🔍 Low stock list
# -----------------------------
st.subheader("⚠️ Products Below Threshold")
low_stock = df[df["Quantity"] < df["Threshold"]]
if low_stock.empty:
    st.success("All products are sufficiently stocked ✅")
else:
    st.dataframe(low_stock)

# -----------------------------
# 💬 Chat Assistant (Optional)
# -----------------------------
st.subheader("💬 Ask about inventory")

user_query = st.text_input("Ask me something (e.g., 'Which products are low on stock?')")
if user_query:
    try:
        # Build a context string from the CSV data
        inventory_summary = "\n".join(
            f"{row['Product']}: {row['Quantity']} units (Threshold {row['Threshold']})"
            for _, row in df.iterrows()
        )
        prompt = f"Inventory data:\n{inventory_summary}\n\nUser question: {user_query}"

        with st.spinner("Thinking..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that analyzes inventory data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

        answer = response.choices[0].message["content"].strip()
        st.markdown(f"**Answer:** {answer}")

    except Exception as e:
        st.error(f"Error while contacting OpenAI: {e}")

# -----------------------------
# 📈 Footer
# -----------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + OpenAI API")
