import pandas as pd

def cip_recommendation(df):
    recommendations = []

    for train in df['train'].unique():
        train_data = df[df['train'] == train].sort_values('date')

        latest_dp = train_data['dp'].iloc[-1]
        first_dp = train_data['dp'].tail(7).iloc[0]
        dp_trend = latest_dp - first_dp

        if latest_dp > 6.8:
            status = "🔴 ACTION REQUIRED — Start CIP immediately"
        elif latest_dp > 6.5:
            status = "🟡 WARNING — Approaching CIP threshold"
        else:
            status = "🟢 Normal operation"

        if dp_trend > 0:
            margin = 6.5 - latest_dp
            daily_rise = dp_trend / 7
            days_until_warning = int(margin / daily_rise) if daily_rise > 0 else 999
        else:
            days_until_warning = 999

        if latest_dp > 6.5:
            feed_conductivity = train_data['feed_conductivity'].tail(7).mean()
            if feed_conductivity > 1500:
                cip_type = "Acid wash recommended — high feed TDS indicates scaling"
            else:
                cip_type = "Base wash recommended — biological fouling likely"
        else:
            cip_type = "No CIP needed at this time"

        recommendations.append({
            'train': train,
            'latest_dp': round(latest_dp, 2),
            'dp_trend_7days': round(dp_trend, 3),
            'status': status,
            'days_to_warning': days_until_warning if days_until_warning < 999 else "Not imminent",
            'cip_type': cip_type
        })

    return pd.DataFrame(recommendations)