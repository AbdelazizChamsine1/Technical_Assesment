import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'Dataset.xlsx')

def load_dataset():
    try:
        df = pd.read_excel(DATA_PATH)
    except FileNotFoundError:
        raise Exception(f"Dataset file not found at: {DATA_PATH}")

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    df["cost_per_lead"] = df.apply(
        lambda row: row.spends / row.leads if row.leads > 0 else None, axis=1)
    df["cost_per_click"] = df.apply(
        lambda row: row.spends / row.ad_clicks if row.ad_clicks > 0 else None, axis=1)

    return df
