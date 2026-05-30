#main application file
#- after using streamlit could ingnore this from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

#after using streamlit could ingnore this  load_dotenv()

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Page config ───────────────────────────────────────────
st.set_page_config(page_title="RO Performance Dashboard",
                   layout="wide")

# ─── Load and clean data ───────────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)

    # Drop empty columns
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

    # Rename columns to clean names
    df = df.rename(columns={
        'date':               'date',
        'Train':              'train',
        'temperator':         'temperature',
        'feed water':         'feed_flow',
        'reject water':       'reject_flow',
        'permeit flow':       'permeate_flow',
        'pressur':            'pressure',
        'condictiviy ':       'permeate_conductivity',
        'tds':                'tds',
        'ph':                 'ph',
        'condictivity feed':  'feed_conductivity'
    })

    # Fix inconsistent train names
    df['train'] = (df['train']
                   .str.replace('Train1', 'Train 1', regex=False)
                   .str.replace('Train2', 'Train 2', regex=False)
                   .str.strip())

    # Calculate KPIs
    df['recovery_rate']   = df['permeate_flow'] / df['feed_flow'] * 100
    df['salt_rejection']  = (1 - df['permeate_conductivity'] /
                             df['feed_conductivity']) * 100

    return df

# ─── Anomaly detection ─────────────────────────────────────
def detect_anomalies(df):
    flags = []
    for _, row in df.iterrows():
        issues = []
        if pd.notna(row['ph']) and (row['ph'] > 8.5 or row['ph'] < 8.0):
            issues.append(f"pH abnormal: {row['ph']}")
        if pd.notna(row['permeate_conductivity']) and row['permeate_conductivity'] > 150:
            issues.append(f"High conductivity: {row['permeate_conductivity']:.1f} μS/cm")
        if pd.notna(row['recovery_rate']) and row['recovery_rate'] < 70:
            issues.append(f"Low recovery: {row['recovery_rate']:.1f}%")
        if pd.notna(row['salt_rejection']) and row['salt_rejection'] < 85:
            issues.append(f"Low salt rejection: {row['salt_rejection']:.1f}%")
        if issues:
            flags.append({
                'date':  row['date'].strftime('%Y-%m-%d'),
                'train': row['train'],
                'flags': ' | '.join(issues)
            })
    return pd.DataFrame(flags)

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
        fig3.add_hline(y=150, line_dash="dash",
                       line_color="red", annotation_text="Alert threshold")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Operating pressure trend")
        fig4 = px.line(filtered, x='date', y='pressure',
                       color='train', markers=True,
                       labels={'pressure': 'Pressure (bar)'})
        fig4.update_traces(connectgaps=True)
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # ── Anomaly report ─────────────────────────────────────
    st.subheader("⚠ Anomaly report")
    anomalies = detect_anomalies(filtered)
    if anomalies.empty:
        st.success("No anomalies detected in selected data.")
    else:
        st.error(f"{len(anomalies)} anomalies detected")
        st.dataframe(anomalies, use_container_width=True)

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
def build_context(df):
    anomalies = detect_anomalies(df)
    anomaly_text = anomalies.to_string() if not anomalies.empty else "No anomalies detected"

    return f"""
You are an expert RO (Reverse Osmosis) system engineer assistant at Sonatrach, Algeria.
You help operators understand their RO unit performance and take corrective actions.
Answer in clear, simple language suitable for field operators.

CURRENT PERFORMANCE DATA:
- Date range: {df['date'].min().date()} to {df['date'].max().date()}
- Trains monitored: {', '.join(df['train'].unique())}
- Average recovery rate: {df['recovery_rate'].mean():.1f}%
- Average salt rejection: {df['salt_rejection'].mean():.1f}%
- Average pressure: {df['pressure'].mean():.2f} bar
- Average temperature: {df['temperature'].mean():.1f} °C
- Average permeate conductivity: {df['permeate_conductivity'].mean():.1f} μS/cm
- Average feed conductivity: {df['feed_conductivity'].mean():.1f} μS/cm

ANOMALIES DETECTED:
{anomaly_text}

LAST 3 READINGS:
{df[['date','train','recovery_rate','salt_rejection',
     'permeate_conductivity','pressure','feed_conductivity']].tail(3).to_string()}

Answer based on this data. If asked about something not in the data, say so clearly.
"""

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
{build_context(filtered)}

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




