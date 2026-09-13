#main application file
#- after using streamlit could ingnore this from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
from ai.rag import load_vectorstore, ask_document
from data.loader import load_data
from analytics.anomalies import detect_anomalies
from analytics.cip import cip_recommendation
from ai.assistant import build_context, build_full_context


@st.cache_resource
def get_vectorstore():
    return load_vectorstore()


#after using streamlit could ingnore this  load_dotenv()dir

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Page config ───────────────────────────────────────────
st.set_page_config(page_title="RO Performance Dashboard",
                   layout="wide")



# ─── Anomaly detection ─────────────────────────────────────



# ─── App ───────────────────────────────────────────────────
st.title("RO Unit Performance Dashboard")
st.caption("GRN — Reverse Osmosis Monitoring System")

uploaded_file = st.file_uploader("Upload RO data (Excel)", type=["xlsx", "xls"])



if uploaded_file:
    df = load_data(uploaded_file)

    # Sidebar filters
    st.sidebar.title("Filters")
    trains = ["All"] + sorted(df['train'].unique().tolist())
    selected_train = st.sidebar.selectbox("Select train", trains)

    filtered = df.copy()


    # ── TEMPORARY DIAGNOSTICS ──
# TEMPORARY DIAGNOSTICS
    #st.write("Date type:", filtered['date'].dtype)
    #st.write("Train names:", filtered['train'].unique())
    #st.write("NaN in recovery rate:", filtered['recovery_rate'].isna().sum())
    #st.write(filtered[['date', 'train', 'recovery_rate', 'salt_rejection']])
    # ── END DIAGNOSTICS ──

    if selected_train != "All":
        filtered = filtered[filtered['train'] == selected_train]

    # ── KPI cards ──────────────────────────────────────────
    st.subheader("Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg recovery rate",
              f"{filtered['recovery_rate'].mean():.1f}%")
    c2.metric("Avg salt rejection",
              f"{filtered['salt_rejection'].mean():.1f}%")
    c3.metric("Avg pressure",
              f"{filtered['pressure'].mean():.2f} bar")
    c4.metric("Avg temperature",
              f"{filtered['temperature'].mean():.1f} °C")
    st.caption(f"Note: {df['recovery_rate'].isna().sum()} missing readings in dataset.")

    st.divider()

    # ── Trend charts ───────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recovery rate trend")
        fig1 = px.line(filtered, x='date', y='recovery_rate',
                       color='train', markers=True,
                       labels={'recovery_rate': 'Recovery rate (%)'})
        fig1.update_traces(connectgaps=True)
        fig1.add_hline(y=75, line_dash="dash",
                       line_color="red", annotation_text="Min threshold 75%")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Salt rejection trend")
        fig2 = px.line(filtered, x='date', y='salt_rejection',
                       color='train', markers=True,
                       labels={'salt_rejection': 'Salt rejection (%)'})
        fig2.update_traces(connectgaps=True)
        fig2.add_hline(y=90, line_dash="dash",
                       line_color="orange", annotation_text="Target 90%")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Permeate conductivity trend")
        fig3 = px.line(filtered, x='date', y='permeate_conductivity',
                       color='train', markers=True,
                       labels={'permeate_conductivity': 'Conductivity (μS/cm)'})
        fig3.update_traces(connectgaps=True)
        fig3.add_hline(y=125, line_dash="dash",
                       line_color="red", annotation_text="Alert threshold")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Operating pressure trend")
        fig4 = px.line(filtered, x='date', y='pressure',
                       color='train', markers=True,
                       labels={'pressure': 'Pressure (bar)'})
        fig4.update_traces(connectgaps=True)
        st.plotly_chart(fig4, use_container_width=True)
    
    # ── Normalized DP trend ────────────────────────────────────
    st.subheader("Normalized differential pressure trend")
    st.caption("Temperature-corrected to 25°C — CPA7-LD-4040 Hydranautics specification")

    fig_dp = px.line(filtered, x='date', y='normalized_dp',
                     color='train', markers=True,
                     labels={'normalized_dp': 'Normalized DP (bar)'})
    fig_dp.add_hline(y=6.5, line_dash="dash",
                     line_color="orange",
                     annotation_text="Watch: 6.5 bar")
    fig_dp.add_hline(y=6.8, line_dash="dash",
                     line_color="red",
                     annotation_text="CIP required: 6.8 bar")
    fig_dp.update_traces(connectgaps=True)
    st.plotly_chart(fig_dp, use_container_width=True)

    st.divider()

    # ── Anomaly report ─────────────────────────────────────
    st.subheader("⚠ Anomaly report")
    anomalies = detect_anomalies(filtered)
    if anomalies.empty:
        st.success("No anomalies detected in selected data.")
    else:
        st.error(f"{len(anomalies)} anomalies detected")
        st.dataframe(anomalies, use_container_width=True)

    # ── Generate Flagged Report ────────────────────────────────
    st.divider()
    st.subheader("📋 Generate Report")

    anomalies = detect_anomalies(filtered)

    if not anomalies.empty:
        import io
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Sheet 1 — Flagged anomalies
            anomalies.to_excel(writer, sheet_name='Anomalies', index=False)
            
            # Sheet 2 — KPI Summary
            summary = pd.DataFrame({
                'KPI': [
                    'Avg Recovery Rate',
                    'Avg Salt Rejection',
                    'Avg DP',
                    'Avg Permeate Conductivity',
                    'Avg Temperature',
                    'Total Anomalies Detected'
                ],
                'Value': [
                    f"{filtered['recovery_rate'].mean():.1f}%",
                    f"{filtered['salt_rejection'].mean():.1f}%",
                    f"{filtered['dp'].mean():.2f} bar",
                    f"{filtered['permeate_conductivity'].mean():.1f} μS/cm",
                    f"{filtered['temperature'].mean():.1f} °C",
                    str(len(anomalies))
                ]
            })
            summary.to_excel(writer, sheet_name='KPI Summary', index=False)

        buffer.seek(0)
        
        filename = f"RO_report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
        
        st.download_button(
            label="⬇ Download Anomaly Report (Excel)",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.caption(f"Report includes {len(anomalies)} flagged readings across 2 sheets.")

    else:
        st.success("No anomalies detected — no report needed.")

    # ── CIP Recommendations ─────────────────────────────────
    st.divider()
    st.subheader("🔧 CIP Recommendation Engine")
    st.caption("Based on contractor specification: Watch > 6.5 bar | Action > 6.8 bar")

    cip_df = cip_recommendation(filtered)

    for _, row in cip_df.iterrows():
        st.markdown(f"### {row['train']}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Current DP", f"{row['latest_dp']} bar",
                    delta=f"{row['dp_trend_7days']:+.3f} bar (7-day trend)")
        col2.metric("Days to warning threshold", str(row['days_to_warning']))
        col3.metric("CIP status", "Required" if row['latest_dp'] > 6.8 else "Not required")

        if "🔴" in row['status']:
            st.error(row['status'])
        elif "🟡" in row['status']:
            st.warning(row['status'])
        else:
            st.success(row['status'])

        st.info(f"**Recommendation:** {row['cip_type']}")
        st.divider()

    # ── Raw data ───────────────────────────────────────────
    with st.expander("View raw data"):
        st.dataframe(filtered, use_container_width=True)
    # ─── AI Assistant ──────────────────────────────────────────
import google.generativeai as genai

st.divider()
st.subheader("🤖 RO Assistant")
st.caption("Ask anything about your RO unit performance")

# Build data context from live DataFrame


# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Ask about your RO unit...")

if user_input:
    # Show user message
    with st.chat_message("user"):
        st.write(user_input)

    # Add to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    # Build full prompt with context + history
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    history_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.chat_history[:-1]
    ])

    full_prompt = f"""
{build_full_context(filtered, get_vectorstore(), user_input)}

CONVERSATION SO FAR:
{history_text}

OPERATOR QUESTION: {user_input}
"""

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = model.generate_content(full_prompt)
            answer = response.text
            st.write(answer)

    # Save response to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })




