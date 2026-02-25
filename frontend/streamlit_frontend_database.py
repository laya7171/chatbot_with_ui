# This block of code will create a streamlit ui where user will be able to
# 1. create a new chat
# 2. Resume the past chat using dynamic threads

import streamlit as st
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm import chatbot
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from backend.llm_database import retrieve_all_threads, get_thread_messages


# Utility functions
def generate_thread_id():
    thread_id = str(uuid.uuid4())  # Convert to string for consistency
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    # Also backup locally
    st.session_state['local_conversations'][thread_id] = []
    add_thread(st.session_state['thread_id'])
    st.rerun()  # Force rerun to update UI immediately

def add_thread(thread_id):
    if 'chat_threads' not in st.session_state:
        st.session_state['chat_threads'] = []
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

checkpointer = InMemorySaver()

def load_convo(thread_id):
    try:
        # Debug: Check if we have local backup first
        if thread_id in st.session_state['local_conversations']:
            st.sidebar.write(f"Loading from local backup for {thread_id}")
            return st.session_state['local_conversations'][thread_id]
        
        # Get the saved state for this thread
        config = {'configurable': {'thread_id': thread_id}}
        state = chatbot.get_state(config=config)
        
        # Debug information
        st.sidebar.write(f"State for {thread_id}: {state}")
        st.sidebar.write(f"State values: {state.values if state else 'No state'}")
        
        # Return the messages if they exist, otherwise return empty list
        messages = state.values.get('messages', []) if state and state.values else []
        
        st.sidebar.write(f"Raw messages count: {len(messages)}")
        
        # Convert to the format expected by streamlit
        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = 'user'
            elif isinstance(message, AIMessage):
                role = 'assistant'
            else:
                # Handle other message types if needed
                role = 'assistant'
            temp_messages.append({'role': role, 'content': message.content})
        
        st.sidebar.write(f"Converted messages count: {len(temp_messages)}")
        return temp_messages
        
    except Exception as e:
        st.sidebar.error(f"Error loading conversation: {e}")
        return []

# Import backend streaming function
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm import chatbot_stream

# Session config
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = list(retrieve_all_threads())

# Add a local backup of conversations in session state for debugging
if 'local_conversations' not in st.session_state:
    st.session_state['local_conversations'] = {}

# Add current thread to the list
add_thread(st.session_state['thread_id'])

# Sidebar UI
st.sidebar.title("Chat Options")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

# Display thread buttons with better labels
for i, thread_id in enumerate(st.session_state['chat_threads']):
    # Create a more user-friendly label
    if thread_id == st.session_state['thread_id']:
        button_label = f"Chat {i+1} (Current)"
    else:
        button_label = f"Chat {i+1}"
    
    if st.sidebar.button(button_label, key=f"thread_{thread_id}"):
        # Debug: Show what we're trying to load
        st.sidebar.write(f"Switching to thread: {thread_id}")
        
        # Switch to the selected thread
        st.session_state['thread_id'] = thread_id
        
        # Load the conversation history for this thread
        loaded_messages = load_convo(thread_id)
        st.session_state['message_history'] = loaded_messages
        
        # Debug: Show what was loaded
        st.sidebar.write(f"Loaded {len(loaded_messages)} messages")
        
        # Force a rerun to update the display
        st.rerun()

# Dynamic config based on current thread
CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

# Display conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Chat input
user_input = st.chat_input('Type here')

if user_input:
    # Add user message to history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    
    # Also backup to local storage
    current_thread = st.session_state['thread_id']
    st.session_state['local_conversations'][current_thread] = st.session_state['message_history'].copy()
    
    # Display user message
    with st.chat_message('user'):
        st.text(user_input)
    
    # Generate and display AI response
    with st.chat_message("assistant"):
        try:
            ai_message = st.write_stream(
                chatbot_stream(
                    {"messages": st.session_state['message_history']},  # full history
                    config=CONFIG,
                    stream_mode="messages"
                )
            )
            
            # Add AI response to history
            st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
            
            # Update local backup
            st.session_state['local_conversations'][current_thread] = st.session_state['message_history'].copy()
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            # Still add an error message to history to maintain consistency
            error_msg = "Sorry, there was an error generating the response."
            st.text(error_msg)
            st.session_state['message_history'].append({'role': 'assistant', 'content': error_msg})
            # Update local backup
            st.session_state['local_conversations'][current_thread] = st.session_state['message_history'].copy()