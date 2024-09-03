##----------------------------------- Imports --------------------------------##

import os
import pprint
from openai import OpenAI # pip install openai
import prompt as pr
import pandas as pd
import json
from literalai import LiteralClient # pip install literalai

##--------------------------------- API Connections ----------------------------##

literal_client = LiteralClient(api_key=os.environ.get("LITERAL_API_KEY"))
#export LITERAL_API_KEY= 
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
#export OPENAI_API_KEY= 

##------------------------------ EXTRACT DATA FROM LITERAL AI ----------------------------##

## https://cloud.getliteral.ai/projects/Climate-Change-Assistant-GpwYcBiMWzLQ/dashboard

has_next_page = True
after = None
filters = None

order_by = {
    "column": "createdAt",
    "direction": "DESC"
}

all_threads = [] #list of dictionaries of all the threads

# while has_next_page:
#     # Fetch the current page of threads
#     response = literal_client.api.get_threads(
#         filters=filters,
#         order_by=order_by,
#         after=after
#     )

#     # Convert the response to a dictionary
#     response_dict = response.to_dict()
#     single_thread = response_dict.get('data', [])
#     all_threads.extend(single_thread)

#     # Check if there is another page to fetch
#     has_next_page = response_dict.get('pageInfo', {}).get('hasNextPage', False)
#     after = response_dict.get('pageInfo', {}).get('endCursor', None)

# # Define the filename
# filename = 'raw_thread_data.json'

# # Check if the file exists and remove it if it does
# if os.path.exists(filename):
#     os.remove(filename)

# with open('raw_thread_data.json', 'w') as f:
#     json.dump(all_threads, f, indent=4)

# print("Total number of threads is: {}".format(len(all_threads)))

##-------------------------------- PARSE RAW THREAD DATA ------------------------------##

def parse_json(input_data):
    parsed_data = {
        "threadId": input_data["id"],
        "created_at": input_data["createdAt"],
        "client_type": input_data["metadata"].get("client_type", None),
        "steps": []
    }

    for step in input_data["steps"]:
        step_data = {
            "stepId": step["id"],
            #"location": step_location_map.get(step["id"], None),
            "start_time": step.get("startTime"),
            "end_time": step.get("endTime"),
            "scores": step.get("scores", []),
            "tags": step.get("tags"),
            "name": step["name"],
            "content": step.get("output", {}).get("content") if step.get("output") else None
        }
        parsed_data["steps"].append(step_data)

    return parsed_data

# Load the list of raw threads from the JSON file
with open('raw_thread_data.json', 'r') as f:
    all_threads = json.load(f)


# Initialize a list to store the parsed thread data
parsed_threads = []

# Iterate over each thread and parse the data

# for thread in all_threads:

#     # Parse the thread using the traditional method
#     parsed_thread = parse_json(thread)
    
#     #Append the parsed thread to the list
#     parsed_threads.append(parsed_thread)


# # Define the filename
# filename = 'parsed_thread_data.json'

# # Check if the file exists and remove it if it does
# if os.path.exists(filename):
#     os.remove(filename)

# # Save the parsed data to a new JSON file
# with open('parsed_thread_data.json', 'w') as f:
#     json.dump(parsed_threads, f, indent=4)  

# print("Total number of parsed threads is: {}".format(len(parsed_threads)))

# parsed_threads_df = pd.json_normalize(parsed_threads, 'steps', ['threadId', 'created_at', 'client_type'])
# pprint.pprint(parsed_threads_df.head())

##-------------------------- EXTRACT LOCATION FOR EACH STEPID---------OpenAI Call------------##

location_extracts = []

def openai_location_extract_from_json(json_input):
    # Convert the JSON input to a string
    json_string = json.dumps(json_input)

    # Define the prompt for the model
    prompt_sys = pr.system_prompt_locations
    # gpt-4o-mini
    # gpt-4o-2024-08-06
    response = openai_client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": f"Here is the JSON input:\n\n{json_input}"}
    ])

    # Extract the assistant's reply and clean it up
    reply = response.choices[0].message.content.strip()

    return reply

# Load the list of raw threads from the JSON file
with open('raw_thread_data.json', 'r') as f:
    all_threads = json.load(f)

# this can take about an hour for full thread data
# i = 1
# for thread in all_threads:
#     if i < 5:
#         location_extract = openai_location_extract_from_json(thread)
#         location_extract_dict = json.loads(location_extract)
#         location_extracts.append(location_extract_dict)
#     i += 1

# # Define the filename
# filename = 'location_extracts.json'

# # Check if the file exists and remove it if it does
# if os.path.exists(filename):
#     os.remove(filename)

# # Save the insight data to a new JSON file
# with open('location_extracts.json', 'w') as f:
#     json.dump(location_extracts, f, indent=4)

# location_extracts_df = pd.json_normalize(location_extracts, 'steps', ['threadId'])
# pprint.pprint(location_extracts_df.head())

##-------------------------- EXTRACT METADATA FOR EACH THREAD----------OpenAI Call-----------##

metadata_extracts = []

def openai_metadata_extract_from_json(json_input):
    # Convert the JSON input to a string
    json_string = json.dumps(json_input)

    # Define the prompt for the model
    prompt_sys = pr.system_prompt_metadata
    # gpt-4o-mini
    # gpt-4o-2024-08-06
    response = openai_client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": f"Here is the JSON input:\n\n{json_input}"}
    ])

    # Extract the assistant's reply and clean it up
    reply = response.choices[0].message.content.strip()

    return reply

# Load the list of dictionaries from the JSON file
with open('raw_thread_data.json', 'r') as f:
    all_threads = json.load(f)

i = 1 # this can take about 15 minutes for all threads
for thread in all_threads:
    if i < 5: 
        metadata_extract = openai_metadata_extract_from_json(thread)
        metadata_extract_dict = json.loads(metadata_extract)
        metadata_extracts.append(metadata_extract_dict)
    i += 1


# Define the filename
filename = 'metadata_extracts.json'

# Check if the file exists and remove it if it does
if os.path.exists(filename):
    os.remove(filename)

# Save the insight data to a new JSON file
with open('metadata_extracts.json', 'w') as f:
    json.dump(metadata_extracts, f, indent=4)

metadata_extracts_df = pd.DataFrame(metadata_extracts)
pprint.pprint(metadata_extracts_df.head())
