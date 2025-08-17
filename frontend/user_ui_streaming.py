import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm import chatbot_stream
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage

CONFIG = {'configurable': {'thread_id': 'thread-1'}}


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []


# Render past chat history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Chat input
user_input = st.chat_input('Type here')

if user_input:
    # Store + render user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Use backend streaming function
    with st.chat_message('assistant'):
        response_placeholder = st.empty()
        full_response = ""
        for message_chunk, metadata in chatbot_stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode='messages'
        ):
            full_response = message_chunk.content
            response_placeholder.markdown(full_response)
    # Save assistant reply into history
    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': full_response}
    )
