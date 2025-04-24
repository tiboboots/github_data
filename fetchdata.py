from urllib import request, parse, error
import json
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

user_name = input("Enter your github username: ")

activity_api = "https://api.github.com/users/<username>/events"

token = os.getenv("GITHUB_TOKEN") # use os.getenv() method to get value of token environment variable

file_path = "api_response.json"

token_header = {"Authorization": f'token {token}'} # Add token to Authorization header in http request

parsed_api = parse.urlparse(activity_api) # parses activity_api url into tuple object
# Tuple object is: (scheme='https', netloc='api.github.com', path='/users/<username>/events', params='', query='', fragment='')

url_path = parsed_api.path # Extract path part from url, save to url_path

updated_path = url_path.replace("<username>", user_name) # Replace <username> parameter with user input

user_parsed_api = parsed_api._replace(path = updated_path) # Return new tuple object with updated path

user_activity_api = parse.urlunparse(user_parsed_api) # Undo parsing on updated url, returns a new, full url

http_request = request.Request(url = user_activity_api, headers = token_header)
# Create Request object, specifying api url and additional headers, in this case the token for the Authorization header

http_response = request.urlopen(http_request) # Send request and get http response from github server

decoded_http_response = http_response.read().decode('utf-8') # Decode response from bytes to str

json_data = json.loads(decoded_http_response) # Turn decoded response into list or dict object

with open(file_path, "w") as json_file: # write fetched api data to json file
    json.dump(json_data, json_file, indent = 4)






