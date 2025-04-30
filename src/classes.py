import json
from urllib import request, parse, error
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env file

class APIDetails: # Class for grouping constant api data together as attributes
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.token_header = {"Authorization": f'token {self.token}'}
        self.api_url = "https://api.github.com/users/<username>/events?page"
        self.file_path = "api_response.json"
        self.old_events_path = "old_events_dict.json"
        self.new_events_path = "new_events_dict.json"

class APICall(APIDetails): # Inherits attributes from APIDetails parent class
    def __init__(self, user_name, api_page):
        super().__init__()
        self.user_name = user_name
        self.api_page = api_page

    def parse_api_url(self):
        parsed_api = parse.urlparse(self.api_url) # parses api_url into tuple object
        
        url_path = parsed_api.path # Extract path from api tuple using path property method
        url_page = parsed_api.query # Extract page from query parameter
        
        updated_page = url_page.replace(url_page, self.api_page) # Update path with page input
        updated_path = url_path.replace("<username>", self.user_name) # Update path with user_name input

        updated_parsed_api = parsed_api._replace(path = updated_path, query = updated_page) # Replace old path in tuple with new path
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
        
    def create_events_dict(self, json_data):
        # Create events_dict dictionary with repo name as key, and initialize with empty dictionary
        events_dict = {dic['repo']['name']: dict() for dic in json_data}
        for dictionary in json_data:
            event_type = dictionary['type']
            if event_type != "PullRequestEvent":
                for nested_dict in events_dict.values():
                    nested_dict[event_type] = 0
            else:
                for nested_dict in events_dict.values():
                    nested_dict[event_type] = dict()
        return events_dict
    
    def count_events(self, http_response, events_dict):
        for dictionary in http_response:
            if dictionary['type'] == "PullRequestEvent":
                continue # Skip dictionary if event type is equal to PullRequestEvent
            for repo, nested_dict in events_dict.items():
                if dictionary['repo']['name'] != repo or dictionary['type'] not in nested_dict.keys():
                    # Skip dictionary if repo name does not match repo key in event_dict
                    # or if dictionary event type is not a key in nested_dict keys
                    continue 
                # If event type is not PullRequestEvent, and dictionary repo name equals repo key in event_dict,
                # and dictionary event type exists as key within nested_dict, 
                # then access that event type's matching key in nested_dict and add 1 to it's value
                nested_dict[dictionary['type']] += 1 
        return events_dict
    
    def add_pr_actions(self, http_response, events_dict):
        for dictionary in http_response:
            if dictionary['type'] != "PullRequestEvent":
                continue # skip dictionary if event type is not pull request event
            event_type = dictionary['type']
            event_repo = dictionary['repo']['name']
            pr_action = dictionary['payload']['action']
            # if dictionary event type is pull request event, then save repo name, pr action, and event type
            if event_repo not in events_dict.keys():
                # Skip dictionary if event repo not found as key in events_dict
                continue 
            # If event repository does exist within events_dict as a key,
            # then return that key's value, which is a dictionary, and save it to repo_dict
            repo_dict = events_dict.get(event_repo)
            if event_type not in repo_dict.keys():
                # Skip dictionary if event type not found as an event key within the repo's dictionary
                continue
            # If the event type exists as a key within repository dictionary keys,
            # then return that event key's value and save it as the pr_dict variable,
            # since the event type should be pullrequestevent, with a dictionary as it's value
            pr_dict = repo_dict.get(event_type)
            if pr_action not in pr_dict.keys():
                # If the pull request action does not yet exist as a key within the pr dictionary,
                # then add it as a key with the initial value of 1,
                # since that action for the pull request event occured within the repository
                pr_dict[pr_action] = 1
            else:
                # If the pull request action does already exist as a key within the pr dictionary,
                # then increment it's value by 1, 
                # since that action for the pull request event occured in the repository again
                pr_dict[pr_action] += 1
        return events_dict
    
    def get_repo_events(self, http_response):
        # Main method to call all event dictionary related methods, 
        # instead of having to call them individually
        repo_events_init = self.create_events_dict(http_response)
        repo_events_counted = self.count_events(http_response, repo_events_init)
        repo_events = self.add_pr_actions(http_response, repo_events_counted)
        return repo_events
    
    def new_repo_events_to_json(self, repo_events):
        with open(self.new_events_path, "w") as events_json:
            repo_events = json.loads(repo_events) # turn events dictionary into list object
            json.dump(repo_events, events_json, indent = 4)
            print("Repo events successfully saved!")

    def response_to_json(self, json_data):
        if json_data is None: # Exit function if json_data is empty
            return
        with open(self.file_path, "w") as json_file: # write fetched api data to json file
            json.dump(json_data, json_file, indent = 4)
            print("Data successfully retrieved and saved!")
    
    def call_api(self): # Call and run all functions to get data from api and save it
        api_url = self.parse_api_url()
        http_response = self.send_request(api_url)
        cleaned_http_response = self.clean_response(http_response) 
        return cleaned_http_response
    
