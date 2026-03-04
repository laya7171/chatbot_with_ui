from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import OllamaLLM
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langgraph.types import interrupt, Command
from dotenv import load_dotenv
import requests

llm = OllamaLLM(model="gemma3:4b")

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key from environment variables.
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {"error": "ALPHA_VANTAGE_API_KEY not set in environment"}
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    r = requests.get(url)
    return r.json()

@tool
def purchase_stock(symbol: str, quantity: int) -> str:
    """
    Simulate purchasing a stock. In a real implementation, this would 
    integrate with a brokerage API. Here we just return a confirmation message.
    """
    decision = interrupt(f"Do you want to purchase {quantity} shares of {symbol}? ")

    if isinstance(decision, str) and decision.lower() == "yes":
        return {
            "status": "success",
            "message": f"Purchased {quantity} shares of {symbol}."
        }
    else: 
        return {
            "status": "cancelled",
            "message": f"Purchase of {quantity} shares of {symbol} cancelled."
        }
    
tools = [get_stock_price, purchase_stock]
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call"""

    message = state["messages"]
    response = llm_with_tools(message)
    return {"messages": [response]}


tool_node = ToolNode(tools)

memory = MemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)


graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer = memory)

