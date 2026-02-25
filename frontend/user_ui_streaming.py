import streamlit as st
import sys
import os

# Make backend importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm_database import chatbot_stream  # adjust to backend.llm if needed
from langchain_core.messages import HumanMessage, AIMessage

# Session config
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# helper: convert stored history to LangChain messages
def to_langchain_messages(history):
    msgs = []
    for m in history:
        if m.get('role') == 'user':
            msgs.append(HumanMessage(content=m.get('content', '')))
        else:
            msgs.append(AIMessage(content=m.get('content', '')))
    return msgs

# Display conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Chat input box
user_input = st.chat_input('Type here')

if user_input:
    # Save user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Prepare LangChain messages for backend
    langchain_msgs = to_langchain_messages(st.session_state['message_history'])

    # Stream assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        for chunk in chatbot_stream({"messages": langchain_msgs}, config=CONFIG, stream_mode="messages"):
            # chatbot_stream should yield only the new chunk (string)

    # Save assistant response