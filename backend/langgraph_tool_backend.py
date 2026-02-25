from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

import requests
import random

from sqlalchemy import case

llm = ChatOllama(model="phi4-mini:latest")

@tool
def calculate(num1: int, num2: int, operator: str) -> dict:
    """A calculator tool that performs basic arithmetic operation based on the operator provided. 
    Supported operators are +, -, *, and /.
    Takes 2 numbers and an operator as input and returns the result of the calculation."""
    match operator:
        case "+":
            result = num1 + num2
        case "-":
            result = num1 - num2
        case "*":
            result = num1 * num2
        case "/":
            result =  num1 / num2
        case _:
            result =  "Invalid operator"
    return {"result": result}

search_tool = DuckDuckGoSearchRun(region = "us-en", max_results=5)

@tool
def get_stock_price(symbol: str)-> dict:
    """A tool that retrieves the current stock price for a given stock symbol using the Alpha Vantage API."""
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey=AIB6CASM87HZ3NQ3'
    r = requests.get(url)
    data = r.json()
    return {"data": data}


tools = [calculate, get_stock_price, search_tool]

llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    """Defines the structure of the chat state, which includes a list of messages exchanged in the conversation."""
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState)-> ChatState:
    """A function that takes the current chat state as input, generates a response using the language model with tools, and returns the updated chat state."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools= tools)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

# Create a memory saver for thread persistence
memory = MemorySaver()
chatbot = graph.compile(checkpointer=memory)

def retrieve_all_threads():
    """Retrieve all thread IDs from the checkpoint memory."""
    try:
        # Get all namespaces/threads from the checkpointer
        all_namespaces = list(memory.storage.keys())
        # Extract unique thread IDs from namespaces
        thread_ids = list(set(ns[0] for ns in all_namespaces if ns))
        return thread_ids
    except:
        return []

# Only run test code when script is executed directly
if __name__ == "__main__":
    out = chatbot.invoke({"messages": [HumanMessage(content="Divide 9 by 3 and give me answer also give the stock price of APPLE today")]})
    print(out["messages"][-1].content)