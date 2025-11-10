# streamlit_app.py
# Fully self-contained Streamlit dashboard that visually replicates the provided design.
# No QR/Barcode scanner libraries are used.

import io
import random
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ---------- Page Setup ----------
st.set_page_config(
    page_title="Inventory Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Global Styles ----------
GRADIENT_CSS = """
<style>
/* Page background (teal/blue gradient) */
.stApp {
  background: radial-gradient(1200px 800px at 20% 15%, #7aa3ab 0%, #6c8f9e 35%, #5f7f8f 65%, #547481 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #eaf1f3;
  border-right: 0px solid transparent;
}
section[data-testid="stSidebar"] .stMarkdown p {
  margin-bottom: 0.4rem;
}

/* Generic card container */
.card {
  background: #ffffff;
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(38, 57, 77, 0.18);
  border: 1px solid rgba(0,0,0,0.04);
}

/* Small title */
.card h3, .card h4, .card h5 {
  font-weight: 700;
  color: #263238;
  margin-top: 0;
  margin-bottom: 12px;
}

/* Subtle caption */
.captionx {
  color: #6b7f89; 
  font-size: 0.85rem;
}

/* "Pill" metric badge */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-right: 10px;
  border-radius: 14px;
  font-weight: 600;
  background: #f5f7f8;
  color: #314147;
  border: 1px solid rgba(0,0,0,0.06);
}
.badge .dot { 
  width: 10px; height: 10px; border-radius: 10px; display: inline-block; 
}
.badge.red .dot { background: #e65a5a; }
.badge.amber .dot { background: #f0ac2b; }
.badge.green .dot { background: #24a07a; }

/* Detail card list */
.detail-list { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.detail-item {
  background: #f6fafb; border: 1px dashed #d9e1e4; 
  padding: 14px; border-radius: 12px; text-align: center; 
  font-weight: 600; color: #4b5e66;
}

/* Chat assistant bubble styles */
.chat {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 10px;
  align-items: start;
}
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #94d0c2 0%, #6ea5ff 100%);
  display: inline-flex; align-items: center; justify-content: center; color: #fff;
  font-weight: 900;
}
.msg {
  background: #f6fbfd; border: 1px solid #d9e9ee; border-radius: 12px; padding: 10px 12px;
  margin-bottom: 8px; color: #41545c;
}
.msg.bot { background: #fff9f1; border-color: #f0d4a9; }

/* Barcode placeholder area */
.barcode-wrap {
  background: #f1faf8; border: 1px dashed #b8d5ce; padding: 10px; border-radius: 12px;
}

/* Tiny legend dot */
.legend-dot { width: 10px; height: 10px; display:inline-block; border-radius: 50%; margin-right:6px; }
.legend { display:flex; flex-wrap:wrap; gap:12px; color:#607681; }

hr.sep { border: none; height: 1px; background: #edf2f5; margin: 10px 0 14px; }
</style>
"""
st.markdown(GRADIENT_CSS, unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ")
    st.markdown("##")
    st.markdown("##")  # spacer
    st.markdown("### Navigation")
    st.markdown(
        """
        <div class='card'>
          <div style="display:grid; gap:10px;">
            <div>📊 Dashboard</div>
            <div>📦 Inventory</div>
            <div>🤝 Suppliers</div>
            <div>🧾 Orders</div>
            <div>⚙️ Settings</div>
            <div>💬 Chat Assistant</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Helper: donut gauge ----------
def donut(value, total, label, color, subtitle, height=160):
    # value/total donut with center text
    fig, ax = plt.subplots(figsize=(2.2, 2.2), dpi=140)
    ax.pie(
        [value, total - value],
        startangle=200,
        counterclock=False,
        wedgeprops=dict(width=0.32, edgecolor="white"),
        colors=[color, "#edf3f5"],
    )
    ax.text(
        0, 0.05 if value >= 100 else 0.0,
        f"{value}",
        ha="center", va="center", fontsize=16, fontweight="bold", color="#263238"
    )
    ax.text(0, -0.22, subtitle, ha="center", va="center", fontsize=9, color="#6b7f89")
    ax.set(aspect="equal")
    ax.axis("off")
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)

import base64

# ---------- Helper: simple barcode (no libraries) ----------
def generate_barcode_png(code="3200 3820", width=500, height=160):
    rng = random.Random(code)
    bars = [rng.randint(1, 4) for _ in range(90)]
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    x = 0
    for i, w in enumerate(bars):
        ax.add_patch(plt.Rectangle((x, 0), w, 1, color=("black" if i % 2 == 0 else "white")))
        x += w
    ax.set_xlim(0, x)
    ax.set_ylim(0, 1)
    ax.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ---------- Barcode Card ----------
with c2:
    barcode_base64 = generate_barcode_png()
    st.markdown(
        f"""
        <div class='card'>
          <h3>Barcode Scan</h3>
          <div class='barcode-wrap'>
            <div style="display:flex; align-items:center; justify-content:center;">
              <img id="barcode-img" style="width:100%; border-radius:8px;" 
                   src="data:image/png;base64,{barcode_base64}">
            </div>
          </div>
          <p class='captionx' style='text-align:center;margin-top:8px;'>SCANNING…</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Top Row ----------
c1, c2 = st.columns([3.1, 1.6], gap="large")

with c1:
    st.markdown(
        """
        <div class='card'>
          <h3>Stock Overview</h3>
          <div style="display:flex; gap:30px; align-items:center;">
            <div class='badge red'><span class='dot'></span>Low Stock<br><span class='captionx'>47 Items</span></div>
            <div class='badge amber'><span class='dot'></span>Reorder<br><span class='captionx'>120 Items</span></div>
            <div class='badge green'><span class='dot'></span>In Stock<br><span class='captionx'>890 Items</span></div>
          </div>
          <hr class='sep'/>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d1, d2, d3 = st.columns(3)
    with d1:
        donut(47, 200, "Low Stock", "#e65a5a", "47 Items")
    with d2:
        donut(120, 200, "Reorder", "#f0ac2b", "120 Items")
    with d3:
        donut(890, 1000, "In Stock", "#24a07a", "890 Items")

with c2:
    import base64

    def generate_barcode_png(code="3200 3820", width=500, height=160):
        rng = random.Random(code)
        bars = [rng.randint(1, 4) for _ in range(90)]
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        x = 0
        for i, w in enumerate(bars):
            ax.add_patch(plt.Rectangle((x, 0), w, 1, color=("black" if i % 2 == 0 else "white")))
            x += w
        ax.set_xlim(0, x)
        ax.set_ylim(0, 1)
        ax.axis("off")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    barcode_base64 = generate_barcode_png()
    st.markdown(
        f"""
        <div class='card'>
          <h3>Barcode Scan</h3>
          <div class='barcode-wrap'>
            <div style="display:flex; align-items:center; justify-content:center;">
              <img id="barcode-img" style="width:100%; border-radius:8px;" 
                   src="data:image/png;base64,{barcode_base64}">
            </div>
          </div>
          <p class='captionx' style='text-align:center;margin-top:8px;'>SCANNING…</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Middle Row ----------
m1, m2 = st.columns([3.1, 1.6], gap="large")

with m1:
    st.markdown("<div class='card'><h3>Supplier & Sales Data</h3>", unsafe_allow_html=True)

    # Top suppliers (Q3) – horizontal bar chart
    suppliers = pd.DataFrame({
        "Supplier": ["Acme Corp", "Innovative Ltd", "Global Goods"],
        "Qty": [62, 48, 41],
    }).sort_values("Qty", ascending=True)

    fig1, ax1 = plt.subplots(figsize=(5.6, 2.0), dpi=180)
    ax1.barh(suppliers["Supplier"], suppliers["Qty"], edgecolor="none")
    ax1.set_xlabel("")
    ax1.set_ylabel("")
    ax1.grid(axis="x", linestyle=":", alpha=0.3)
    ax1.set_facecolor("white")
    for spine in ax1.spines.values():
        spine.set_visible(False)
    st.pyplot(fig1, use_container_width=True)
    plt.close(fig1)

    st.markdown("<div class='captionx' style='margin: 2px 0 6px;'>Top Suppliers (Q3)</div>", unsafe_allow_html=True)

    # Sales by category (Q3) – small grouped bars
    categories = ["Electronics", "Apparel", "Home Goods"]
    acme = [120, 60, 80]
    innovative = [70, 90, 50]
    globalg = [40, 55, 65]

    df2 = pd.DataFrame({
        "Category": categories,
        "Acme Corp": acme,
        "Innovative Ltd": innovative,
        "Global Goods": globalg,
    })

    x = np.arange(len(categories))
    width = 0.24
    fig2, ax2 = plt.subplots(figsize=(6.4, 2.2), dpi=180)
    ax2.bar(x - width, df2["Acme Corp"], width)
    ax2.bar(x, df2["Innovative Ltd"], width)
    ax2.bar(x + width, df2["Global Goods"], width)
    ax2.set_xticks(x, categories)
    ax2.set_ylabel("")
    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.grid(axis="y", linestyle=":", alpha=0.3)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown(
        """
        <div class='legend'>
          <div><span class='legend-dot' style='background:#1f77b4'></span>Acme Corp</div>
          <div><span class='legend-dot' style='background:#ff7f0e'></span>Innovative Ltd</div>
          <div><span class='legend-dot' style='background:#2ca02c'></span>Global Goods</div>
          <div><span class='captionx'>Sales by Category (Q3)</span></div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        """
        <div class='card'>
          <h3>Detailed Reports</h3>
          <div class='detail-list'>
            <div class='detail-item'>📦 Inventory</div>
            <div class='detail-item'>🔁 Movement History</div>
            <div class='detail-item'>📑 Report</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Bottom Row ----------
b1, b2 = st.columns([1.6, 3.1], gap="large")

with b1:
    st.markdown(
        """
        <div class='card'>
          <h3>Chat Assistant</h3>
          <div class='msg'>Type your query…</div>
          <div class='chat'>
            <div class='avatar'>U</div>
            <div class='msg'>Check stock for SKU 789</div>
            <div class='avatar'>B</div>
            <div class='msg bot'><b>SKU:</b> 150 units available.<br/><b>Supplier:</b> Acme Corp.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with b2:
    st.markdown("<div class='card'><h3>Trend Performance</h3>", unsafe_allow_html=True)

    # Fake time-series matching the screenshot vibe
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    a = [40, 85, 100, 125, 110, 160]
    b = [70, 95, 80, 75, 90, 120]
    c = [20, 55, 75, 95, 100, 140]

    df_line = pd.DataFrame({
        "Month": months,
        "Series A": a,
        "Series B": b,
        "Series C": c,
    })

    # Line chart with plain matplotlib (single axes, no custom colors to keep default aesthetic)
    fig3, ax3 = plt.subplots(figsize=(7.4, 3.2), dpi=160)
    ax3.plot(months, df_line["Series A"], marker="o")
    ax3.plot(months, df_line["Series B"], marker="o")
    ax3.plot(months, df_line["Series C"], marker="o")
    ax3.set_ylabel("")
    ax3.set_xlabel("")
    ax3.set_title("Top-Selling Products", fontsize=11, pad=8)
    ax3.grid(axis="y", linestyle=":", alpha=0.35)
    for spine in ax3.spines.values():
        spine.set_visible(False)
    st.pyplot(fig3, use_container_width=True)
    plt.close(fig3)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Footer (subtle) ----------
st.markdown(
    f"<div style='text-align:center; color:#6c828b; font-size:0.8rem; padding:6px 0 10px;'>Updated {datetime.now().strftime('%b %d, %Y')}</div>",
    unsafe_allow_html=True,
)
