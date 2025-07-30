import pandas as pd

def get_top_channels_by_kpi(df: pd.DataFrame, kpi: str, top_n: int = 3) -> pd.DataFrame:

    if kpi not in df.columns:
        raise ValueError(f"KPI '{kpi}' not found in dataset.")

    grouped = df.groupby("source")[[kpi, "spends"]].sum()
    grouped["efficiency"] = grouped[kpi] / grouped["spends"]
    result = grouped.sort_values("efficiency", ascending=False).head(top_n)
    return result.reset_index()


def filter_by_objective(df: pd.DataFrame, objective: str) -> pd.DataFrame:
    return df[df["objective"].str.lower() == objective.lower()]


def summarize_channel_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize each channel’s total spend and average cost per lead/click.
    """
    summary = df.groupby("source").agg({
        "spends": "sum",
        "cost_per_lead": "mean",
        "cost_per_click": "mean",
        "leads": "sum",
        "ad_clicks": "sum"
    }).reset_index()
    return summary.sort_values("spends", ascending=False)


def suggest_spend_split(df: pd.DataFrame, budget: float, kpi: str) -> pd.DataFrame:
    """
    Suggests a spend split across top-performing channels based on efficiency.
    """
    top_channels = get_top_channels_by_kpi(df, kpi, top_n=3)
    total_efficiency = top_channels["efficiency"].sum()
    
    top_channels["allocated_budget"] = top_channels["efficiency"] / total_efficiency * budget
    return top_channels[["source", "efficiency", "allocated_budget"]]
