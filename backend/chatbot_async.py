from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_mcp_adapters import MultiServerMCPClient

import requests
import random
import asyncio
from sqlalchemy import case

from backend.llm_database import chat_node

llm = ChatOllama(model="phi4-mini:latest")

client  =  MultiServerMCPClient(
    {
        "artih": {
            "transport": "http",
            "commands": "python3",
            "args": ["-m", "mcp_adapter"],
        }
    }
)


class ChatState(TypedDict):
    """Defines the structure of the chat state, which includes a list of messages exchanged in the conversation."""
    messages: Annotated[list[BaseMessage], add_messages]

async def build_graph():

    tools = await client.get_tools()

    llm_with_tools = llm.bind_tools(tools)

    
    async def chat_node(state: ChatState)-> ChatState:
        message = state["messages"]
        response =await llm_with_tools.ainvoke(message)
        return {"messages": [response]}
    
    graph = StateGraph()
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge("chat_node", "tools", condition=tools_condition)
    graph.add_edge(START, "chat_node")

    return graph

async def main():
    chatbot = await build_graph()

    result = chatbot.ainvoke({"messages": [HumanMessage(content="What is the current stock price of AAPL?")]})
    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())