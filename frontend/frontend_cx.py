import streamlit as st
import sys
import os
import uuid
from langchain_core.messages import HumanMessage

# Make backend importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm_db_cx import chatbot, retrieve_all_threads, get_thread_messages

# *************** utility functions ***************

def generate_thread_id() -> str:
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id: str):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id: str):
    # Load from persistent checkpointer (SQLite)
    messages = get_thread_messages(thread_id)
    temp_messages = []
    for msg in messages:
        # LangChain messages have .type: 'human' or 'ai'
        role = 'user' if getattr(msg, "type", "") == "human" else 'assistant'
        content = getattr(msg, "content", "")
        temp_messages.append({'role': role, 'content': content})
    return temp_messages

# *************** Session Setup *******************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = list(retrieve_all_threads())

add_thread(st.session_state['thread_id'])

# *************** Sidebar UI **********************
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat', key="new_chat_btn"):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id), key=f"thread_btn_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = load_conversation(thread_id)

# *************** Main UI *************************
# Show history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # Save and show user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Stream assistant response; ChatOllama + graph node streams message chunks
    with st.chat_message('assistant'):
        ai_text = st.write_stream(
            (
                # each yielded message_chunk should be an AIMessageChunk; .content is the delta
                (message_chunk.content or "")
                for message_chunk, _ in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode='messages'
                )
                if getattr(message_chunk, "type", "") in ("ai", "ai_chunk")
            )
        )

    # Save assistant response
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_text})