import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

def card(title, content_fn):
    """Creates a visual card wrapper that contains charts properly."""
    with st.container():
        # create visual frame using markdown background
        st.markdown(
            f"""
            <div style="
                background-color: rgba(173,216,230,0.6);
                border-radius:16px;
                box-shadow:0 4px 10px rgba(0,0,0,0.05);
                padding:25px 30px;
                margin-bottom:25px;
            ">
            <h3 style="margin-top:0;color:#222;">{title}</h3>
            """,
            unsafe_allow_html=True
        )
        # everything inside this container is part of the card visually
        content_fn()
        st.markdown("</div>", unsafe_allow_html=True)

def stock_content():
    col1, col2, col3 = st.columns(3)
    def gauge(value, color):
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=value,
            gauge={'axis': {'range':[None,150]},
                   'bar':{'color':color,'thickness':0.25},
                   'bgcolor':"#f5f5f5"}))
        fig.update_layout(height=150, margin=dict(l=0,r=0,t=10,b=0))
        return fig
    for val, color, label in [(47,"#E74C3C","Low Stock"),(120,"#F39C12","Reorder"),(890,"#2ECC71","In Stock")]:
        with col1 if label=="Low Stock" else col2 if label=="Reorder" else col3:
            st.plotly_chart(gauge(val,color), use_container_width=True)
            st.markdown(f"<center><b style='color:{color};font-size:20px'>{val}</b><br>{label}</center>", unsafe_allow_html=True)

def supplier_content():
    col1, col2 = st.columns([2,1])
    suppliers = {'Acme Corp':200,'Innovate Ltd':180,'Global Goods':120,'Apparel':100,'Home Goods':90,'Electronics':150}
    df = pd.DataFrame(list(suppliers.items()), columns=["Supplier","Sales"])
    fig = go.Figure(go.Bar(y=df["Supplier"], x=df["Sales"], orientation="h",
                           marker_color=['#3498DB','#F39C12','#2ECC71','#E74C3C','#9B59B6','#1ABC9C']))
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        for c,color in [('Acme Corp','#3498DB'),('Innovate Ltd','#F39C12'),('Global Goods','#2ECC71'),('Apparel','#E74C3C'),('Home Goods','#9B59B6')]:
            st.markdown(f"<div style='display:flex;align-items:center;margin-bottom:8px;'><div style='width:15px;height:15px;border-radius:4px;background-color:{color};margin-right:8px;'></div>{c}</div>", unsafe_allow_html=True)

def chat_content():
    st.markdown("""
        <div style="background:#e1f0ff;padding:10px 14px;border-radius:12px;margin-bottom:10px;max-width:80%;margin-left:auto;">
            User: Check stock for SKU 789
        </div>
        <div style="background:#f1f4f7;padding:10px 14px;border-radius:12px;margin-bottom:10px;max-width:80%;">
            Bot: SKU: 150 units available.<br>Supplier: Acme Corp.
        </div>
    """, unsafe_allow_html=True)
    st.text_input("Type your query...", placeholder="Type your query...", label_visibility="collapsed")

def trend_content():
    trend = pd.DataFrame({
        'Month':['Jan','Feb','Mar','Apr','May','Jun'],
        'Product A':[40,45,60,55,70,85],
        'Product B':[30,50,40,65,60,75],
        'Product C':[50,35,55,45,50,60]
    })
    fig = go.Figure()
    for name, color in zip(['Product A','Product B','Product C'], ['#007AFF','#FF9500','#34C759']):
        fig.add_trace(go.Scatter(x=trend["Month"], y=trend[name], mode="lines+markers", name=name, line=dict(color=color,width=3)))
    fig.update_layout(height=280, margin=dict(l=10,r=10,t=40,b=20), paper_bgcolor="white", plot_bgcolor="white", xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#eee'))
    st.plotly_chart(fig, use_container_width=True)

# --- Layout ---
col_nav, col_content = st.columns([1,4])
with col_nav:
    st.markdown("<div style='background-color:lightblue;border-radius:20px;padding:20px;min-height:100vh;'>📊 Dashboard<br>📦 Inventory<br>🚚 Suppliers<br>🛒 Orders<br>⚙️ Settings</div>", unsafe_allow_html=True)
with col_content:
    card("Stock Overview", stock_content)
    card("Supplier & Sales Data", supplier_content)
    c1, c2 = st.columns(2)
    with c1: card("Chat Assistant", chat_content)
    with c2: card("Trend Performance", trend_content)
