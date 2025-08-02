from langchain.agents import Tool
from backend.dataset_loader import load_dataset
from backend.logic import (get_top_channels_by_kpi, filter_by_objective, summarize_channel_performance, suggest_spend_split, submit_user_inputs, get_current_inputs)

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

def collect_user_input(prompt: str) -> str:
    # You can hardcode logic or just echo back
    return (
        "Before I proceed, I need a few details:\n"
        "1. What’s your campaign objective? (e.g., conversions, traffic)\n"
        "2. What is your total budget?\n"
        "3. Do you have any preferred media channels (e.g., Meta, Snapchat)?"
    )

collect_user_input_tool = Tool(
    name="CollectUserInput",
    func=collect_user_input,
    description="Use this when you need to ask the user for information like objective, budget, or channel before building a media plan."
)

submit_user_inputs_tool = Tool(
        name="SubmitUserInputs",
        func=submit_user_inputs,
        description=(
            "Use this tool when the user provides campaign info in free-form text.\n"
            "Format: objective, budget, channel — e.g., 'conversions, 10000, Meta'."
        )
    )

get_inputs_tool = Tool(
    name="GetCurrentInputs",
    func=get_current_inputs,
    description="Use this tool to see what objective, budget, and channel the user has provided so far."
)

# List of tools
tools_list = [
    top_channels_tool,
    filter_objective_tool,
    channel_summary_tool,
    budget_split_tool,
    submit_user_inputs_tool,
    collect_user_input_tool,
    get_inputs_tool
]
