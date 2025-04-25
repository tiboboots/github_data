import json
import os
from dotenv import load_dotenv
from urllib import request, parse, error
from classes import APICall

load_dotenv() # Load environment variables from .env file

user_name = input("Enter your github username: ")

api_url = "https://api.github.com/users/<username>/events"

token = os.getenv("GITHUB_TOKEN") # use os.getenv() method to get value of token environment variable

token_header = {"Authorization": f'token {token}'}

github_api = APICall(user_name, token, token_header, api_url)

github_api.call_api()


