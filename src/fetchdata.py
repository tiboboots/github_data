from classes import APIDetails, APICall

user_name = input("Enter your github username: ")

api_details = APIDetails() # Create instance of APIDetails class containing constant api variables/data

api_instance = APICall(user_name) # Pass user input as argument/value of user_name attribute in APICall

http_response = api_instance.call_api() # Send request, get response, save response, with the call_api() method

user_events = api_instance.filter_events(http_response) # Return dicitonary with user events, using response

