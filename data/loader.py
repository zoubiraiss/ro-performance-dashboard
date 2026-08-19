import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

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
                            'condictivity feed':  'feed_conductivity',
                            'dp':                 'dp'
                             })

    df['train'] = (df['train']
                   .str.replace('Train1', 'Train 1', regex=False)
                   .str.replace('Train2', 'Train 2', regex=False)
                   .str.strip())

    df['recovery_rate']   = df['permeate_flow'] / df['feed_flow'] * 100
    df['salt_rejection']  = (1 - df['permeate_conductivity'] /
                             df['feed_conductivity']) * 100

    df['TCF']           = np.exp(2640 * (1/(273 + df['temperature']) - 1/298))
    df['normalized_dp'] = df['dp'] * df['TCF']

    return df
