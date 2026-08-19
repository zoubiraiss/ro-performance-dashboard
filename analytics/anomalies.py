import pandas as pd

def detect_anomalies(df):
    conditions =(
        df['ph'].notna() & ((df['ph'] > 9.0) | (df['ph'] < 7.0))|
        df['permeate_conductivity'].notna() & (df['permeate_conductivity'] > 125)|
        df['recovery_rate'].notna() & (df['recovery_rate'] < 70)|
        df['salt_rejection'].notna() & (df['salt_rejection'] < 85)|
        df['dp'].notna() & (df['dp'] > 6.5)
    )

    flagged = df[conditions].copy()
    flagged['flags'] = ''

    flagged.loc[flagged['ph'].notna() & ((flagged['ph'] > 9.0) | (flagged['ph'] < 7.0)), 'flags'] += 'pH abnormal | '
    flagged.loc[flagged['permeate_conductivity'].notna() & (flagged['permeate_conductivity'] > 125), 'flags'] += 'High conductivity | '
    flagged.loc[flagged['recovery_rate'].notna() & (flagged['recovery_rate'] < 70), 'flags'] += 'Low recovery | '
    flagged.loc[flagged['salt_rejection'].notna() & (flagged['salt_rejection'] < 85), 'flags'] += 'Low salt rejection | '
    flagged.loc[flagged['dp'].notna() & (flagged['dp'] > 6.5), 'flags'] += 'High DP — check CIP | '

    return flagged[['date', 'train', 'flags']].reset_index(drop=True)