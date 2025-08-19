from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_ollama import OllamaLLM
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

# Initialize Ollama LLM
llm = OllamaLLM(model="mistral")

# Define chat state for LangGraph
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    # Non-streaming (used internally if needed)
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Setup graph + checkpointer
checkpointer = InMemorySaver()
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# Streaming generator
def chatbot_stream(input_dict, config=None, stream_mode=None):
    """Stream response chunks from Ollama."""
    for chunk in llm.stream(input_dict["messages"]):
        # Case 1: AIMessageChunk
        if hasattr(chunk, "content"):
            yield chunk.content
        # Case 2: GenerationChunk
        elif hasattr(chunk, "text"):
            yield chunk.text
        # Case 3: Plain string
        elif isinstance(chunk, str):
            yield chunk
        else:
            # Fallback: dump whatever it is
            yield str(chunk)

