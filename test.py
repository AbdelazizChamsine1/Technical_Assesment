from backend.agent import chat_with_agent

prompts = [
    "I have a $10000 budget and want more leads. What channels do you recommend?",
    "What are the top channels for ad clicks?",
    "Which channel had the best cost per lead?",
    "Give me a performance summary of all channels.",
    "Split a $5000 budget based on lead efficiency."
]

for prompt in prompts:
    print("\n>>>", prompt)
    print(chat_with_agent(prompt))
