#this block of code will create a streamlit ui where user will be able to
#1. create a new chat
#2. Resume the past chat using dynamic threads

import streamlit as st
import sys
import os

# Import backend streaming function
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm import chatbot_stream

# Session config
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

#sidebar ui
st.sidebar.title("Chat Options")
st.sidebar.button("New Chat")
st.sidebar.header("My Conversations")



# Display conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            chatbot_stream(
                {"messages": st.session_state['message_history']},  # full history
                config=CONFIG,
                stream_mode="messages"
            )
        )
    


    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
