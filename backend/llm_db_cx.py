from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Use the chat model (supports streaming)
llm = ChatOllama(model="llama3.2:latest")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Persistent checkpointer (SQLite)
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Build graph with the model as a runnable node (enables streaming)
graph = StateGraph(ChatState)
graph.add_node("model", llm)
graph.add_edge(START, "model")
graph.add_edge("model", END)

chatbot = graph.compile(checkpointer=checkpointer)

def get_thread_messages(thread_id: str):
    # Load messages for a given thread_id
    config = {'configurable': {'thread_id': str(thread_id)}}
    state = checkpointer.get_state(config)
    if state is None:
        return []
    values = getattr(state, "values", state)  # compatibility across versions
    return values.get("messages", [])

def retrieve_all_threads():
    threads = set()
    try:
        it = checkpointer.list()
    except TypeError:
        it = checkpointer.list(None)
    for cp in it:
        try:
            threads.add(cp.config['configurable']['thread_id'])
        except Exception:
            pass
    return list(threads)