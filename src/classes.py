import json
from urllib import request, parse, error

class APICall:
    def __init__(self, user_name, token, token_header, api_url):
        self.user_name = user_name
        self.token = token
        self.token_header = token_header
        self.api_url = api_url
        self.file_path = "api_response.json"

    def parse_api_url(self):
        parsed_api = parse.urlparse(self.api_url) # parses api_url into tuple object
        url_path = parsed_api.path # Extract path from api tuple using path property method
        updated_path = url_path.replace("<username>", self.user_name) # Update path with user_name input
        updated_parsed_api = parsed_api._replace(path = updated_path) # Replace old path in tuple with new path
        updated_api_url = parse.urlunparse(updated_parsed_api) # Undo parsing on updated url, returns a new, full url
        return updated_api_url
    
    def send_request(self, updated_api_url):
        http_request = request.Request(url = updated_api_url , headers = self.token_header)
        try:
            http_response = request.urlopen(http_request) # Send request and get http response from github server
        except error.HTTPError as e:
            print(e.code, e.reason) # If request is invalid due to http error, print error status code
        except error.URLError as u:
            print(u.reason)  # If request is invalid due to network error, print network error
        else:
            return http_response # Return http response if request was successful
    
    def clean_response(self, http_response):
        if http_response is None: # Exit function is http_response is empty
            return 
        try:
            decoded_http_response = http_response.read().decode('utf-8') # Decode response from bytes to str
        except json.JSONDecodeError as j: # Raise json decode exception if json format is invalid
            print(j.msg)
        else:
            json_data = json.loads(decoded_http_response) # Turn decoded response into list or dict object
            return json_data
    
    def response_to_json(self, json_data):
        if json_data is None: # Exit function if json_data is empty
            return
        with open(self.file_path, "w") as json_file: # write fetched api data to json file
            json.dump(json_data, json_file, indent = 4)
            print("Data successfully retrieved and saved!")
    
    def call_api(self): # Call and run all functions to get data from api and save it
        updated_api_url = self.parse_api_url()
        http_response = self.send_request(updated_api_url)
        json_data = self.clean_response(http_response)
        self.response_to_json(json_data)