from langchain.agents import Tool
from backend.dataset_loader import load_dataset
from backend.logic import (get_top_channels_by_kpi, filter_by_objective, summarize_channel_performance, suggest_spend_split)

df = load_dataset()

# Tool 1: Top-performing channels by KPI
top_channels_tool = Tool(
    name="TopChannelsByKPI",
    func=lambda kpi: get_top_channels_by_kpi(df, kpi).to_string(index=False),
    description=(
        "Use this tool to get top-performing media channels by KPI (e.g., leads, ad_clicks, website_traffic). "
        "Input should be a single string KPI name."
    )
)

# Tool 2: Filter campaigns by objective
filter_objective_tool = Tool(
    name="FilterByObjective",
    func=lambda objective: filter_by_objective(df, objective).to_string(index=False),
    description=(
        "Use this tool to filter the dataset by campaign objective (e.g., Conversion, Traffic). "
        "Input should be a single string like 'Conversion'."
    )
)

# Tool 3: Summarize performance of each channel
channel_summary_tool = Tool(
    name="SummarizeChannelPerformance",
    func=lambda _: summarize_channel_performance(df).to_string(index=False),
    description="Summarizes each channel's spend, cost per lead, and cost per click. Input can be empty."
)

# Tool 4: Recommend budget split based on KPI efficiency
budget_split_tool = Tool(
    name="SuggestSpendSplit",
    func=lambda input: _parse_and_suggest_split(input),
    description=(
        "Suggests how to split a budget across top-performing channels based on a given KPI. "
        "Input format: '<budget> <kpi>', e.g., '10000 leads'."
    )
)

# Helper function for parsing the input of SuggestSpendSplit
def _parse_and_suggest_split(input: str) -> str:
    try:
        parts = input.strip().split()
        budget = float(parts[0])
        kpi = parts[1]
        return suggest_spend_split(df, budget, kpi).to_string(index=False)
    except Exception as e:
        return f"Invalid input. Please use format like '10000 leads'. Error: {str(e)}"

# List of tools
tools_list = [
    top_channels_tool,
    filter_objective_tool,
    channel_summary_tool,
    budget_split_tool
]
