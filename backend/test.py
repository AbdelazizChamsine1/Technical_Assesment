from backend.agent import chat_with_agent

if __name__ == "__main__":
    prompt = "I have a $10000 budget and want more leads. What channels do you recommend?"
    response = chat_with_agent(prompt)
    print("Agent Response:\n", response)
