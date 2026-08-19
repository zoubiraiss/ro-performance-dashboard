def build_context(df):
    def get_latest(train_name, column):
        subset = df[df['train'].str.contains(train_name)]
        if subset.empty:
            return 'No data'
        return f"{subset[column].iloc[-1]:.2f}"

    def get_mean(train_name, column):
        subset = df[df['train'].str.contains(train_name)]
        if subset.empty:
            return 'No data'
        return f"{subset[column].mean():.2f}"

    return f"""
You are an expert RO system engineer at Sonatrach, Algeria.

CURRENT PERFORMANCE DATA:
- Date range: {df['date'].min().date()} to {df['date'].max().date()}
- Trains monitored: {', '.join(df['train'].unique())}
- Average recovery rate: {df['recovery_rate'].mean():.1f}%
- Average salt rejection: {df['salt_rejection'].mean():.1f}%
- Average pressure: {df['pressure'].mean():.2f} bar
- Average temperature: {df['temperature'].mean():.1f} °C
- Average permeate conductivity: {df['permeate_conductivity'].mean():.1f} μS/cm
- Average feed conductivity: {df['feed_conductivity'].mean():.1f} μS/cm

DIFFERENTIAL PRESSURE:
- Average DP Train 1: {get_mean('Train 1', 'dp')} bar
- Average DP Train 2: {get_mean('Train 2', 'dp')} bar
- Latest DP Train 1: {get_latest('Train 1', 'dp')} bar
- Latest DP Train 2: {get_latest('Train 2', 'dp')} bar
- DP contractor thresholds: Watch at 6.5 bar, CIP required at 6.8 bar

LAST 3 READINGS:
{df[['date', 'train', 'recovery_rate', 'salt_rejection',
     'permeate_conductivity', 'pressure', 'dp']].tail(3).to_string()}

Answer based on this data. If asked about something not in the data, say so clearly.
Answer in clear language suitable for field operators.
"""


def build_full_context(df, vectorstore, question):
    live_context = build_context(df)

    doc_results = vectorstore.similarity_search(question, k=3)
    doc_context = "\n\n".join([doc.page_content for doc in doc_results])

    return f"""
{live_context}

REFERENCE DOCUMENTATION (membrane datasheet, CIP procedures):
{doc_context}

Answer using BOTH the live sensor data above AND the reference
documentation above, whichever is relevant to the question. If asked
about something in neither source, say so clearly.
"""