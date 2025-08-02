import pandas as pd
import re
from backend.memory import memory

def get_top_channels_by_kpi(df: pd.DataFrame, kpi: str, top_n: int = 3) -> pd.DataFrame:
    """
    Get top channels by KPI efficiency.
    kpi: should be 'leads' or 'clicks' (values from the KPI column)
    """
    
    # First, filter by KPI type
    kpi_lower = kpi.lower()
    filtered_df = df[df["kpi"].str.lower() == kpi_lower]
    
    if filtered_df.empty:
        available_kpis = df["kpi"].unique()
        raise ValueError(f"KPI '{kpi}' not found. Available KPIs: {available_kpis}")
    
    # Map KPI to the actual metric column
    if kpi_lower == "leads":
        metric_col = "leads"
    elif kpi_lower == "clicks":
        metric_col = "ad_clicks"  # Use ad_clicks column for clicks KPI
    else:
        raise ValueError(f"KPI '{kpi}' not supported. Use 'leads' or 'clicks'")
    
    # Group by source and sum the metrics
    grouped = filtered_df.groupby("source")[[metric_col, "spends"]].sum()
    
    # Calculate efficiency (metric per dollar spent)
    grouped["efficiency"] = grouped[metric_col] / grouped["spends"]
    
    # Sort by efficiency and take top N
    result = grouped.sort_values("efficiency", ascending=False).head(top_n)
    
    # Reset index to make 'source' a column again
    return result.reset_index()

def filter_by_objective(df: pd.DataFrame, objective: str) -> pd.DataFrame:
    if objective.lower() not in df["objective"].str.lower().unique():
        raise ValueError(f"Objective '{objective}' not found.")
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

# def suggest_spend_split(df: pd.DataFrame, budget: float, objective: str) -> pd.DataFrame:
#     """
#     Suggests a spend split across top-performing channels based on efficiency.
#     Now handles channel preference for Meta and Snapchat only.
#     """
#     # Map objectives to KPIs
#     objective_to_kpi = {
#         "conversion": "leads",
#         "conversions": "leads", 
#         "traffic": "clicks",
#     }
    
#     kpi = objective_to_kpi.get(objective.lower())
#     if not kpi:
#         raise ValueError(f"Objective '{objective}' not supported.")
    
#     # Get both channels (Meta and Snapchat)
#     top_channels = get_top_channels_by_kpi(df, kpi, top_n=2)  # Changed to 2
    
#     if len(top_channels) == 0:
#         raise ValueError("No channels found for this KPI.")
    
#     # Get user's channel preference from global user_inputs
#     from backend.logic import user_inputs
#     preferred_channel = user_inputs.get("channel")
    
#     if preferred_channel and preferred_channel.lower() != "none":
#         # User has a channel preference - give it 70% of budget
#         pref_mask = top_channels["source"].str.lower() == preferred_channel.lower()
        
#         if pref_mask.any():
#             # Preferred channel exists in top performers
#             top_channels["allocated_budget"] = 0.0  # Reset all to 0
            
#             # Give 70% to preferred channel
#             top_channels.loc[pref_mask, "allocated_budget"] = budget * 0.7
            
#             # Give 30% to the other channel
#             other_channels = top_channels[~pref_mask]
#             if len(other_channels) > 0:
#                 top_channels.loc[~pref_mask, "allocated_budget"] = budget * 0.3
#         else:
#             # Preferred channel not found, distribute by efficiency
#             total_efficiency = top_channels["efficiency"].sum()
#             top_channels["allocated_budget"] = top_channels["efficiency"] / total_efficiency * budget
#     else:
#         # No preference (channel: none) - distribute by efficiency
#         total_efficiency = top_channels["efficiency"].sum()
#         if total_efficiency == 0:
#             raise ValueError("Total efficiency is zero.")
#         top_channels["allocated_budget"] = top_channels["efficiency"] / total_efficiency * budget
    
#     return top_channels[["source", "efficiency", "allocated_budget"]]

def suggest_spend_split(df: pd.DataFrame, budget: float, objective: str) -> pd.DataFrame:
    """
    Suggests a spend split between Meta and Snapchat based on efficiency and preference.
    Uses a simple but smart allocation logic.
    """
    # Map objectives to KPIs
    objective_to_kpi = {
        "conversion": "leads",
        "conversions": "leads", 
        "traffic": "clicks",
    }
    
    kpi = objective_to_kpi.get(objective.lower())
    if not kpi:
        raise ValueError(f"Objective '{objective}' not supported.")
    
    # Get both channels' performance
    channels_data = get_top_channels_by_kpi(df, kpi, top_n=2)
    
    if len(channels_data) == 0:
        raise ValueError("No channels found for this KPI.")
    
    # Get user's channel preference
    from backend.logic import user_inputs
    preferred_channel = user_inputs.get("channel")
    
    # Calculate efficiency ratio between channels
    meta_row = channels_data[channels_data["source"].str.lower() == "meta"]
    snap_row = channels_data[channels_data["source"].str.lower() == "snapchat"]
    
    meta_efficiency = meta_row["efficiency"].values[0] if len(meta_row) > 0 else 0
    snap_efficiency = snap_row["efficiency"].values[0] if len(snap_row) > 0 else 0
    total_efficiency = meta_efficiency + snap_efficiency
    
    # Base allocation on efficiency
    if total_efficiency > 0:
        meta_base_pct = meta_efficiency / total_efficiency
        snap_base_pct = snap_efficiency / total_efficiency
    else:
        # Equal split if no efficiency data
        meta_base_pct = 0.5
        snap_base_pct = 0.5
    
    # Apply preference adjustment
    if preferred_channel and preferred_channel.lower() != "none":
        # Preference boost: shift 20% towards preferred channel
        PREFERENCE_BOOST = 0.2
        
        if preferred_channel.lower() == "meta":
            meta_final_pct = min(meta_base_pct + PREFERENCE_BOOST, 0.85)  # Cap at 85%
            snap_final_pct = 1 - meta_final_pct
        elif preferred_channel.lower() == "snapchat":
            snap_final_pct = min(snap_base_pct + PREFERENCE_BOOST, 0.85)  # Cap at 85%
            meta_final_pct = 1 - snap_final_pct
        else:
            # Invalid preference, use base percentages
            meta_final_pct = meta_base_pct
            snap_final_pct = snap_base_pct
    else:
        # No preference - use pure efficiency-based split
        meta_final_pct = meta_base_pct
        snap_final_pct = snap_base_pct
    
    # Apply minimum allocation rule (at least 15% to each channel)
    MIN_ALLOCATION = 0.15
    if meta_final_pct < MIN_ALLOCATION:
        meta_final_pct = MIN_ALLOCATION
        snap_final_pct = 1 - MIN_ALLOCATION
    elif snap_final_pct < MIN_ALLOCATION:
        snap_final_pct = MIN_ALLOCATION
        meta_final_pct = 1 - MIN_ALLOCATION
    
    # Calculate final budgets
    meta_budget = round(budget * meta_final_pct, -2)  # Round to nearest 100
    snap_budget = budget - meta_budget  # Ensure total equals budget
    
    # Create result dataframe
    result = pd.DataFrame({
        "source": ["Meta", "Snapchat"],
        "efficiency": [meta_efficiency, snap_efficiency],
        "allocated_budget": [meta_budget, snap_budget],
        "allocation_pct": [meta_final_pct * 100, snap_final_pct * 100]
    })
    
    # Add reasoning
    result["reasoning"] = result.apply(
        lambda row: _get_simple_reasoning(
            row["source"], 
            row["allocation_pct"], 
            preferred_channel,
            meta_efficiency,
            snap_efficiency
        ), 
        axis=1
    )
    
    return result[["source", "efficiency", "allocated_budget", "reasoning"]]


def _get_simple_reasoning(channel, allocation_pct, preferred_channel, meta_eff, snap_eff):
    """Generate simple reasoning for allocation"""
    is_preferred = preferred_channel and channel.lower() == preferred_channel.lower()
    is_more_efficient = (channel == "Meta" and meta_eff > snap_eff) or \
                       (channel == "Snapchat" and snap_eff > meta_eff)
    
    if is_preferred and is_more_efficient:
        return f"{allocation_pct:.0f}% - Preferred + Best performance"
    elif is_preferred:
        return f"{allocation_pct:.0f}% - Preferred channel (boosted)"
    elif is_more_efficient:
        return f"{allocation_pct:.0f}% - Higher efficiency"
    else:
        return f"{allocation_pct:.0f}% - Diversification"

user_inputs = {
    "objective": None,
    "budget": None,
    "channel": None
}

valid_objectives = {"conversion", "traffic"}
valid_channels = {"meta", "snapchat"}

# def submit_user_inputs(input_str: str) -> str:
#     try:
#         text = input_str.lower()

#         # --- Objective ---
#         obj_match = re.search(r"objective\s*:\s*(\w+)", text)
#         if obj_match:
#             objective = obj_match.group(1).strip()
#             if objective in valid_objectives:
#                 user_inputs["objective"] = objective

#         # --- Budget ---
#         budget_match = re.search(r"budget\s*:\s*(\d{3,6})", text)
#         if budget_match:
#             user_inputs["budget"] = float(budget_match.group(1))

#         # --- Channel ---
#         ch_match = re.search(r"channel\s*:\s*([a-z\s]+)", text)
#         if ch_match:
#             ch = ch_match.group(1).strip()
#             if "none" in ch or "no" in ch:
#                 user_inputs["channel"] = None
#             elif ch in valid_channels:
#                 user_inputs["channel"] = ch

#         # --- Validate ---
#         if user_inputs["objective"] and user_inputs["budget"] is not None:
#             channel_display = (
#                 user_inputs["channel"].capitalize()
#                 if user_inputs["channel"]
#                 else "No preference"
#             )
#             return (
#                 f"✅ Got it! Here's what I understood:\n"
#                 f"- Objective: {user_inputs['objective'].capitalize()}\n"
#                 f"- Budget: ${user_inputs['budget']}\n"
#                 f"- Channel: {channel_display}\n\n"
#                 f"You can now ask me to generate a media plan."
#             )
#         else:
#             return (
#                 f"❌ Missing or unrecognized values.\n"
#                 f"- Objective: {user_inputs.get('objective')}\n"
#                 f"- Budget: {user_inputs.get('budget')}\n"
#                 f"- Channel: {user_inputs.get('channel')}\n\n"
#                 f"✅ Please use the format: `budget: 10000, objective: conversion, channel: meta`\n"
#                 f"Allowed objectives: {', '.join(valid_objectives)}\n"
#                 f"Allowed channels: {', '.join(valid_channels)} or `none`"
#             )

#     except Exception as e:
#         return f"⚠️ Error processing input: {str(e)}"
    
def submit_user_inputs(input_str: str) -> str:
    try:
        text = input_str.lower()

        # --- Objective ---
        obj_match = re.search(r"objective\s*:\s*(\w+)", text)
        if obj_match:
            objective = obj_match.group(1).strip()
            if objective in valid_objectives:
                user_inputs["objective"] = objective

        # --- Budget ---
        budget_match = re.search(r"budget\s*:\s*(\d{3,6})", text)
        if budget_match:
            user_inputs["budget"] = float(budget_match.group(1))

        # --- Channel ---
        ch_match = re.search(r"channel\s*:\s*([a-z\s]+)", text)
        if ch_match:
            ch = ch_match.group(1).strip()
            if "none" in ch or "no" in ch:
                user_inputs["channel"] = None
            elif ch in valid_channels:
                user_inputs["channel"] = ch

        # --- Validate ---
        if user_inputs["objective"] and user_inputs["budget"] is not None:
            channel_display = (
                user_inputs["channel"].capitalize()
                if user_inputs["channel"]
                else "No preference"
            )
            return (
                f"✅ Got it! Here's what I understood:\n"
                f"- Objective: {user_inputs['objective'].capitalize()}\n"
                f"- Budget: ${user_inputs['budget']}\n"
                f"- Channel: {channel_display}\n\n"
                f"I have all the information needed. Let me generate your optimized media plan..."
            )
        else:
            return (
                f"❌ Missing or unrecognized values.\n"
                f"- Objective: {user_inputs.get('objective')}\n"
                f"- Budget: {user_inputs.get('budget')}\n"
                f"- Channel: {user_inputs.get('channel')}\n\n"
                f"✅ Please use the format: `budget: 10000, objective: conversion, channel: meta`\n"
                f"Allowed objectives: {', '.join(valid_objectives)}\n"
                f"Allowed channels: {', '.join(valid_channels)} or `none`"
            )

    except Exception as e:
        return f"⚠️ Error processing input: {str(e)}"

def get_current_inputs(_: str = "") -> str:
    if not user_inputs["objective"] or not user_inputs["budget"]:
        return "❌ Some inputs are still missing."

    channel_display = (
        user_inputs["channel"].capitalize()
        if user_inputs["channel"]
        else "No preference"
    )

    return (
        f"📋 Stored campaign info:\n"
        f"- Objective: {user_inputs['objective'].capitalize()}\n"
        f"- Budget: ${user_inputs['budget']}\n"
        f"- Channel: {channel_display}"
    )
