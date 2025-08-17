from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_ollama import OllamaLLM
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages


llm = OllamaLLM(model = "phi3:latest")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Checkpointer
checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)


chatbot = graph.compile(checkpointer=checkpointer)

# Streaming generator for demo/testing: yields response one character at a time
def stream_response(text, delay=0.05):
    import time
    chunk = ""
    for c in text:
        chunk += c
        yield chunk
        time.sleep(delay)

# Example streaming interface for the chatbot
def chatbot_stream(input_dict, config=None, stream_mode=None):
    # Get the response as usual
    result = chatbot.invoke(input_dict, config=config)
    # Extract the message content
    content = result['messages'][-1].content
    # Yield chunks (simulate streaming)
    for chunk in stream_response(content):
        # Yield a dummy message object with .content attribute
        class DummyMsg:
            def __init__(self, content):
                self.content = content
        yield DummyMsg(chunk), {}

