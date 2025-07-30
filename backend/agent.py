from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
from backend.media_tools import tools_list

import os
from dotenv import load_dotenv

# Load Gemini API key
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini chat model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=google_api_key
)

# Optional: Memory to support iterative conversation
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create the agent
agent = initialize_agent(
    tools=tools_list,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory
)

def chat_with_agent(prompt: str) -> str:
    """
    Run a prompt through the Gemini-powered agent and return the result.
    """
    try:
        response = agent.invoke(prompt)
        return response
    except Exception as e:
        return f"Agent error: {str(e)}"
