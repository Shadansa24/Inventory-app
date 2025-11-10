import streamlit as st
import pandas as pd
import json, os, re
from io import BytesIO

# ========================== DATA SECTION ==========================
products = pd.DataFrame([
    {"Product_ID": 101, "SKU": "IPH-15", "Name": "iPhone 15", "Category": "Mobile", "Quantity": 12, "MinStock": 15, "UnitPrice": 999, "Supplier": "ACME"},
    {"Product_ID": 102, "SKU": "GS24", "Name": "Galaxy S24", "Category": "Mobile", "Quantity": 30, "MinStock": 8, "UnitPrice": 899, "Supplier": "GX"},
    {"Product_ID": 103, "SKU": "MBA-M3", "Name": "MacBook Air M3", "Category": "Laptop", "Quantity": 5, "MinStock": 8, "UnitPrice": 1299, "Supplier": "ACME"},
    {"Product_ID": 104, "SKU": "LG-MSE", "Name": "Logitech Mouse", "Category": "Accessory", "Quantity": 3, "MinStock": 5, "UnitPrice": 29, "Supplier": "ACC"},
    {"Product_ID": 105, "SKU": "AP-PR2", "Name": "AirPods Pro", "Category": "Accessory", "Quantity": 20, "MinStock": 5, "UnitPrice": 249, "Supplier": "ACME"}
])
products["Low"] = products["Quantity"] < products["MinStock"]

supplier_summary = (
    products.groupby("Supplier")
    .agg(Products=("Name", "count"), Units=("Quantity", "sum"))
    .reset_index()
)

orders = pd.DataFrame([
    {"Order_ID": "S-1001", "Product": "Logitech Mouse", "Units": 2, "Price": 29, "Date": "2025-01-10"},
    {"Order_ID": "S-1002", "Product": "iPhone 15", "Units": 1, "Price": 999, "Date": "2025-02-01"},
])

# ========================== SETTINGS STORAGE ==========================
SETTINGS_FILE = "user_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"theme": "Sky Blue", "reorder_threshold": 25, "persist_chat": True}

def save_settings(settings_dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_dict, f, indent=4)

def export_to_excel():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        products.to_excel(writer, index=False, sheet_name="Inventory")
        supplier_summary.to_excel(writer, index=False, sheet_name="Suppliers")
        orders.to_excel(writer, index=False, sheet_name="Orders")
    buffer.seek(0)
    return buffer

# ========================== CHAT MEMORY ==========================
chat_file = "chat_memory.json"

def load_chat(settings):
    if settings.get("persist_chat") and os.path.exists(chat_file):
        with open(chat_file, "r") as f:
            return json.load(f)
    return []

def save_chat(settings, chat):
    if settings.get("persist_chat"):
        with open(chat_file, "w") as f:
            json.dump(chat, f, indent=4)

# ========================== CHAT LOGIC ==========================
def answer(q: str) -> str:
    ql = q.lower().strip()

    if any(x in ql for x in ["low stock", "low on stock", "restock", "reorder", "need stock"]):
        lows = products.loc[products["Low"], ["Name", "Quantity", "MinStock"]]
        if lows.empty:
            return "All items are at or above minimum stock."
        rows = [f"- {r.Name}: {int(r.Quantity)}/{int(r.MinStock)} (below min)" for r in lows.itertuples()]
        return "Items that need restocking:\n" + "\n".join(rows)

    if "quantity of" in ql:
        name = ql.split("quantity of")[-1].strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"I couldn't find any product matching '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} — Quantity: {int(r['Quantity'])}, MinStock: {int(r['MinStock'])}."

    if "supplier of" in ql:
        name = ql.split("supplier of")[-1].strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"No supplier found for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} is supplied by {r['Supplier']}."

    if "price of" in ql:
        name = ql.split("price of")[-1].strip()
        match = products[products["Name"].str.lower().str.contains(name)]
        if match.empty:
            return f"No price info found for '{name}'."
        r = match.iloc[0]
        return f"{r['Name']} costs ${int(r['UnitPrice'])}."

    if "sku" in ql or "code" in ql:
        parts = re.findall(r"[a-z0-9\-]+", ql.upper())
        for sku in parts:
            match = products[products["SKU"].str.upper() == sku]
            if not match.empty:
                r = match.iloc[0]
                return f"{r['Name']} — Qty {int(r['Quantity'])}, Min {int(r['MinStock'])}, Price ${int(r['UnitPrice'])}, Supplier {r['Supplier']}."
        return "I couldn't find that SKU."

    return ("Sorry, I didn't understand. Try:\n"
            "• 'low stock'\n"
            "• 'quantity of iPhone'\n"
            "• 'supplier of AirPods'\n"
            "• 'price of MacBook'\n"
            "• 'sku GS24'")

# ========================== UI STYLE ==========================
SKY = """
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 50% -80px, #ffffff 0, #e9f3fb 35%, #cfe3f4 100%);
}
.block-container {padding-top: 1rem; padding-bottom: 3rem;}
section[data-testid="stVerticalBlock"] > div:empty {display:none}
div.row-widget.stHorizontal {margin-bottom:0 !important;}
hr {visibility:hidden; margin:0}
.paper {
  background: #fff;
  border-radius: 14px;
  padding: 22px 26px 20px 26px;
  margin-top: 0.4rem;
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
  border: 1px solid rgba(20,60,120,.06);
}
.tile {
  background: #fff;
  border-radius: 14px;
  padding: 18px 16px;
  box-shadow: 0 6px 16px rgba(0,0,0,.05);
  border: 1px solid rgba(20,60,120,.06);
}
h2,h3 {margin:0 0 .6rem 0;}
"""
st.markdown(f"<style>{SKY}</style>", unsafe_allow_html=True)

# ========================== SIDEBAR ==========================
menu = ["Dashboard", "Inventory", "Suppliers", "Orders", "Chat Assistant", "Settings"]
choice = st.sidebar.radio("📦 Navigation", menu)

# Load settings and chat memory
settings = load_settings()
if "chat" not in st.session_state:
    st.session_state.chat = load_chat(settings)

# ========================== PAGES ==========================

if choice == "Dashboard":
    st.title("Inventory Management Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stock Items", f"{len(products)}", "distinct products")
    col2.metric("Low Stock", f"{sum(products['Low'])}", "below minimum")
    col3.metric("Reorder Needed", f"{sum(products['Low'])}", "order these")
    col4.metric("In Stock", f"{len(products) - sum(products['Low'])}", "OK level")

    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.subheader("Supplier & Sales Data")
    st.bar_chart(products.groupby("Category")["Quantity"].sum())
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.subheader("Trend Performance — Top-Selling Products")
    sales_trend = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Product A": [14, 18, 23, 27, 30, 35],
        "Product B": [10, 15, 19, 23, 27, 31],
    }).set_index("Month")
    st.line_chart(sales_trend)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Inventory":
    st.title("Inventory")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.dataframe(products, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.info("💡 Tip: items with Low = True need reordering.")

elif choice == "Suppliers":
    st.title("Suppliers")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.dataframe(supplier_summary, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Orders":
    st.title("Orders")
    st.markdown('<div class="paper">', unsafe_allow_html=True)
    st.dataframe(orders, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Chat Assistant":
    st.title("Chat Assistant")
    st.markdown('<div class="paper">', unsafe_allow_html=True)

    user_input = st.text_input("Ask about stock, SKU, supplier, price...")
    if user_input:
        st.session_state.chat.append({"user": user_input, "bot": answer(user_input)})
        save_chat(settings, st.session_state.chat)

    for msg in st.session_state.chat[-8:]:
        st.markdown(f"**You:** {msg['user']}")
        st.markdown(f"**Bot:** {msg['bot']}")
        st.divider()

    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Settings":
    st.title("Settings")
    st.markdown('<div class="paper">', unsafe_allow_html=True)

    st.subheader("App Preferences")

    theme = st.selectbox("Theme", ["Sky Blue", "Dark Mode (Coming soon)"],
                         index=0 if settings["theme"] == "Sky Blue" else 1)

    reorder_threshold = st.slider("Reorder alert threshold (%)", 0, 100, settings["reorder_threshold"])
    persist_chat = st.checkbox("Persist chat history across sessions", value=settings["persist_chat"])

    if st.button("💾 Save Settings"):
        save_settings({"theme": theme, "reorder_threshold": reorder_threshold, "persist_chat": persist_chat})
        st.success("Settings saved successfully!")

    st.divider()
    st.subheader("Export Data")
    if st.button("📤 Export to Excel"):
        excel_file = export_to_excel()
        st.download_button("Download Excel File", excel_file, "inventory_data.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()
    st.write("**About**")
    st.caption("Version 1.3 — Streamlit Inventory Manager")
    st.caption("Includes saved settings, export, and persistent chat.")
    st.markdown('</div>', unsafe_allow_html=True)
