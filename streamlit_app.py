import streamlit as st
import pandas as pd
import openai

# --- Setup ---
st.set_page_config(page_title="Smart Inventory Dashboard", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Load Data ---
df = pd.read_csv("data/products.csv")

# --- Dashboard Header ---
st.title("📊 Smart Inventory Dashboard")
st.write("Monitor product stock and query your inventory with AI")

# --- Basic Stats ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Products", len(df))
col2.metric("Low Stock", (df["Quantity"] < df["Threshold"]).sum())
col3.metric("In Stock", (df["Quantity"] >= df["Threshold"]).sum())

# --- Inventory Table ---
st.subheader("Inventory Overview")
st.dataframe(df)

# --- Highlight Low Stock Items ---
low_stock = df[df["Quantity"] < df["Threshold"]]
if not low_stock.empty:
    st.warning("⚠️ Products running low:")
    st.dataframe(low_stock)
else:
    st.success("✅ All products sufficiently stocked.")

# --- Chat Section ---
st.subheader("💬 Inventory Chat Assistant")

user_query = st.text_input("Ask a question about your inventory (e.g., 'Which products need restock?')")

if user_query:
    # Convert query into context-aware prompt
    context = df.to_string(index=False)
    prompt = f"""
    You are an inventory assistant. Based on this table of data:
    {context}
    Answer the question: {user_query}
    Be concise and data-specific.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    st.write("**Answer:**")
    st.info(response.choices[0].message.content)
