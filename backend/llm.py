from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph , START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import InMemorySaver


llm = OllamaLLM(model ="mistral", temperature= 0.7)

class ChatState(TypedDict):

    message: Annotated[list[BaseMessage], add_messages]


checkpointer = InMemorySaver()

graph = StateGraph(ChatState)

def chat_node(state: ChatState):
    messages = state['message']
    response = llm.invoke(messages)

    return {"message": [response]}


graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


workflow = graph.compile(checkpointer=checkpointer)
print("workflow completed")
print(workflow)


 

