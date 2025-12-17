#the goal is to use the sqlite data base and to try to give my name to the llm and store it and access it when the llm makes another response
import os 
import sys
from llm import chatbot
import sqlite3
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

#1 store some type of response made my llm to the database in sqlite
#2 retrive the information from the database
#3 feed the information the llm again to get more customized response


conn = sqlite3.connect(database='../chatbot.db',check_same_thread=False)# if True then code will give error because the sqlite only supports for 1 thread
checkpointer = SqliteSaver(conn=conn)

CONFIG = {'configurable': {'thread_id': 'thread-1'}}

state = {
    "message": "Hello chatbot my name is laya",
    "config": CONFIG,
}