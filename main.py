from database_handler import DatabaseHandler
from milvus_handler import MilvusHandler
import requests
import os
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta

load_dotenv()

# main.py - SIMPLIFIED
from healthcare_chatbot import HealthcareChatbot

if __name__ == "__main__":
    chatbot = HealthcareChatbot()  # Your FULL logic loads
    chatbot.start_chat()           # Your chat loop runs