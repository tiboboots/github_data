import json
from urllib import request, parse, error
from dotenv import load_dotenv
import os
import copy

load_dotenv() # Load environment variables from .env file

class APIDetails: # Class for grouping constant api data together as attributes
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.token_header = {"Authorization": f'token {self.token}'}
        self.api_url = "https://api.github.com/users/<username>/events?page"
        self.response_file_path = "api_response.json"
        self.events_file_path = "events_dictionary.json"

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

    def response_to_json(self, http_response):
        with open(self.response_file_path, "w") as json_file: # write fetched api data to json file
            json.dump(http_response, json_file, indent = 4)
            print("Response successfully retrieved and saved!")
    
    def call_api(self): # Call and run all functions to get data from api and save it
        api_url = self.parse_api_url()
        http_response = self.send_request(api_url)
        cleaned_http_response = self.clean_response(http_response) 
        self.response_to_json(cleaned_http_response)
        return cleaned_http_response
    
class EventHandling(APIDetails):
    def create_events_dict(self, json_data):
        # Create events_dict dictionary with repo name as key, and initialize with empty dictionary
        events_dict = {dic['repo']['name']: dict() for dic in json_data}
        for dictionary in json_data:
            event_type = dictionary['type']
            if event_type != "PullRequestEvent":
                # if event_type is anything besides pullrequestevent, 
                # then add it as a key with an initial value of 0 in events_dict
                for nested_dict in events_dict.values():
                    nested_dict[event_type] = 0
            else: # if event_type is pullrequest event, initialize it as a key with an empty dictionary in events_dict,
                  # as pullrequest events contain various actions which we need to store and process differently
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
    
    def count_pr_actions(self, http_response, events_dict):
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
    
    def get_and_count_repo_events(self, http_response):
        # Main method to call all event dictionary related methods, 
        # instead of having to call them individually
        events_dict = self.create_events_dict(http_response)
        events_dict_counted = self.count_events(http_response, events_dict)
        repo_events = self.count_pr_actions(http_response, events_dict_counted)
        return repo_events
    
    def events_to_json(self, repo_events):
        # write new repo events to json file
        with open(self.events_file_path, "w") as events_json:
            json.dump(repo_events, events_json, indent = 4)
            
    def load_events(self):
        # Load repo events from json file
        with open(self.events_file_path_path, "r") as events_json:
            all_events = json.load(events_json)
        return all_events
    
    def check_new_pr_events(self, repo_events):
        old_events = self.load_events() # Get previous version of http response dictionary before new response updates it
        self.events_to_json(repo_events) # Write new response to same json file to update it with new count for all events
        new_events = self.load_events() # Load new version with new counts for all events in all repo's

        for repo, new_events_dict in new_events.items():
            if repo not in old_events.keys():
                continue # Skip repo if it does not exist in old version as a key
            old_events_dict = old_events.get(repo)
            for event, value in new_events_dict.items():
                if event not in old_events_dict.keys():
                    continue # Skip event if it does not exist in old version as a key
                if event != "PullRequestEvent":
                    continue # Skip all non pull request events
                new_pr_actions = value # Save pull request actions dictionary containing count of pull requests per action
                old_pr_actions = old_events_dict.get(event) # Save the same pull request actions dict but for the old version
                if len(new_pr_actions) == 0 and len(old_pr_actions) == 0:
                    # If length of pull requests dictionary in both versions of repo_events is 0, so if it has no action keys,
                    # then we skip that pull request event
                    continue
                for action, count in new_pr_actions.items():
                    new_pr_count = count # Save value for current pr action from new version as new_count
                    old_pr_count = old_pr_actions.get(action) # Save value for current pr action from old version as old_count
                    if new_pr_count > old_pr_count:
                        # if new pr count for current action is greater than the old pr count for the current action,
                        # then new pull requests have occurred for that action
                        new_pr_event_count = new_pr_count - old_pr_count 
                        # Subtract new count with old count to get total amount of new occurrences for that type of pr action,
                        # Then assign that new amount back to the action's key value in the original repo_events dictionary
                        repo_events[repo][event][action] = new_pr_event_count
                    else:
                        # Else if new_pr_count is not greater than old_pr_count, then no new instances of that pr action happened,
                        # thus we assign action to have the value of 0
                        new_pr_event_count = 0
                        repo_events[repo][event][action] = new_pr_event_count
        return repo_events
    
    def check_new_events(self, repo_events):
        old_events = self.load_events() # Get previous version of events before new events are written to json file
        self.events_to_json(repo_events) # Write new events to new_events_dict.json file
        new_events = self.load_events() # Get new version of the events dictionary from the json file
        # Call check_new_pr_events method to handle checking for new pr events separately, return updated version of repo_events
        updated_repo_events = self.check_new_pr_events(new_events) 

        for repo, new_events_dict in new_events.items():
            if repo not in old_events.keys():
                # Skip repo if repo key from new version of the events dictionary,
                # does not exist as a repo key in the old version of the events dictionary
                continue
            old_events_dict = old_events.get(repo) # If repo exists, then get it's events dictionary
            for event, count in new_events_dict.items():
                if event == "PullRequestEvent":
                    # Skip all pullrequest events, as we have already handled this separately with the check_new_pr_events method
                    continue
                # If event is not equal to PullRequestEvent, then get that key's value, 
                # which is the count of that event in that repository
                new_count = count
                old_count = old_events_dict.get(event) # Get old count for current event
                if new_count > old_count:
                    # Check if the count of the event in the new version of the events dictionary,
                    # is higher than the count of the same event in the old version of the events dictionary
                    # If true, then subtract new count with old count to get difference,
                    # which is the total amount of new occurences for that event in it's repository
                    new_event_count = new_count - old_count
                    updated_repo_events[repo][event] = new_event_count # Update event value to equal count_status
                else:
                    # If new count is not higher than old count, 
                    # then no new occurences of that event happened
                    new_event_count = 0
                    updated_repo_events[repo][event] = new_event_count # Update event value to equal count_status
        return updated_repo_events

    def fetch_pr_event_status(self, new_events):
        # Checks pull request actions to see if any new pull requests were made in the repository
        pr_dict = dict()
        for repo, event_dict in new_events.items():
            pr_repo_counter = 0
            for event in event_dict.keys():
                if event != "PullRequestEvent":
                    continue
                pr_actions = event_dict.get(event)
                for action, count in pr_actions.items():
                    if count > 0:
                        pr_repo_counter += count
                    else:
                        continue
            pr_dict[repo] = pr_repo_counter
        return pr_dict
    
    def fetch_repo_event_status(self, new_events):
        # Method to check whether any new event's have occured in a repository
        pr_dict = self.fetch_pr_event_status(new_events)
        all_new_events = copy.deepcopy(new_events) # Create copy of original new_events dictionary

        for repo, event_dict in all_new_events.items():
            for event, event_count in event_dict.items():
                if event == "PullRequestEvent":
                    for pr_count in pr_dict.values():
                    # Assign repo pr count value as value for pull request event,
                    # in current repository. So if first repo had 0 for it's pr_count, 
                    # then pullrequestevent key in the repo's dictionary value will be updated to equal 0,
                    # if pr_count is greater than 0, then new pull requests were made in that repo, 
                    # and we update it's value to equal the pr_count as well
                        event_dict[event] = pr_count 
                else:
                    # If event is not pullrequestevent, then update it's value with event_count value from new_events
                    event_dict[event] = event_count
        return all_new_events
    
    def check_event_status(self, all_new_events):
        for repo, event_dict in all_new_events.items():
            zero_events = True
            for event, event_count in event_dict.items():
                if event_count > 0:
                    print(f"{event_count} new {event}s in {repo}")
                    zero_events = False
            if zero_events == True:
                print(f"No new events in {repo}")
                        
