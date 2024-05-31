import os
import json
import pandas as pd

import requests
from openai import OpenAI
from datetime import date
from datetime import datetime

from dotenv import load_dotenv
import sys

import io
import base64
import urllib
from PIL import Image
import io
import cv2

from diffusers import AutoPipelineForText2Image, AutoPipelineForImage2Image # DiffusionPipeline
import torch
#import matplotlib.pyplot as plt

import prompts as pr

pf_api_url = "https://graphql.probablefutures.org"
#pf_token_audience = "https://graphql.probablefutures.com"
#pf_token_url = "https://probablefutures.us.auth0.com/oauth/token"

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model = "gpt-4o" #"gpt-4-0125-preview"  # gpt-4 #gpt-3.5-turbo-16k


pipeline_text2image = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16") # digiplay/Landscape_PhotoReal_v1
pipeline_image2image = AutoPipelineForImage2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16") # digiplay/Landscape_PhotoReal_v1
pipeline_text2image.to("cuda")
pipeline_image2image.to("cuda")


def convert_to_iso8601(date_str):
    try:
        # Parse the date string to a datetime object
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Format the datetime object to ISO 8601 format with timezone offset
        iso8601_date = date_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return iso8601_date
    except ValueError:
        # Return the original string if it's not in the expected date format
        return date_str


def get_pf_token():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    url = 'https://graphql.probablefutures.org/auth/token'

    # Encode the client credentials
    encoded_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        'Authorization': 'Basic ' + encoded_credentials
        }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()
        access_token = data['access_token']
        return access_token

    except requests.exceptions.RequestException as e:
        print('There was a problem with your request:', e)
        return None


def json_to_dataframe(json_data, address, country):
    # Extract the relevant part of the JSON data
    json_data = json.loads(json_data)
    data = json_data['data']['getDatasetStatistics']['datasetStatisticsResponses']
    # Convert to a DataFrame
    df = pd.DataFrame(data)
    # Normalize the 'info' column if needed
    #if not df['info'].apply(lambda x: x == {}).all():
    #    info_df = pd.json_normalize(df['info'])
    #    df = df.drop(columns=['info']).join(info_df)
    df['address'] = address
    df['country'] = country
    df = df[['address', 'country', 'name', 'midValue', 'highValue', 'unit', 'mapCategory']]
    #df = df[df['name'].str.contains('Change')]
    df = df[~((df['midValue'] == '0.0') & (df['highValue'] == '0.0'))]
    df.reset_index(drop=True, inplace=True)
    
    return df


def summary_completion(address, country, output, user_question):
    content = f"Please answer the user question {user_question} for the location of {address} {country}. Use the information that was just provided previously to the user: {output}"
    print(content)
    completion = client.chat.completions.create(
        model=model, #"gpt-4-0125-preview",  # gpt-4 #gpt-3.5-turbo-16k
        messages=[
            {"role": "system", "content": pr.user_question_prompt},
            {"role": "user", "content": content}
        ],
        stream=True
    )

    return completion#.choices[0].message.content

# the 'content' object is a dataframe so it's wrapped in a str(to_json()) call
def story_completion(story_system_prompt, units, content):
    completion = client.chat.completions.create(
        model=model, #"gpt-4-0125-preview",  # gpt-4 #gpt-3.5-turbo-16k
        messages=[
            {"role": "system", "content": str(story_system_prompt + ". Be sure to describe the result using the following temperature scale: " + units)},
            {"role": "user", "content": str(content.to_json())}
        ],
        stream=True
    )

    return completion#.choices[0].message.content

# need GPU to run this part; uncomment lines 31 & 32
def get_image_response_SDXL(prompt, image_path=None, filtered_keywords=None): #i'm passing a file path to image when using inpainting; FOR NOW
    print('starting SDXL')  # Check here for prompt language tips: https://stable-diffusion-art.com/sdxl-prompts/
    
    if image_path is None:
        # Generate image from text
        # using flash attention for memory optimization 
        # https://huggingface.co/docs/diffusers/en/optimization/memory#memory-efficient-attention
        #with torch.inference_mode():
        result_image = pipeline_text2image(
            prompt=prompt, num_inference_steps=2, guidance_scale=0.0).images[0]  # Assuming default image dimensions or specify if required
    else:
        # Load the image from the path
        #img = Image.open(image_path) 

        #plt.imshow(img)
        #plt.title("Loaded Image")
        #plt.show() 

        #if strength == None:
        #    strength = 0.51

        # adding inpaiting keywords for 2.0 and 3.0 warming scenarios
        modified_prompt = filtered_keywords if filtered_keywords else prompt
        print(modified_prompt)

        # Modify existing image based on new prompt
        # using flash attention https://huggingface.co/docs/diffusers/en/optimization/memory#memory-efficient-attention
        #with torch.inference_mode():
        result_image = pipeline_image2image(
            prompt=modified_prompt, image=image_path, strength=0.55, guidance_scale=0.0, num_inference_steps=2).images[0]  # negative_prompt="deformed faces, distorted faces, mangled hands, extra legs", 

    # Save the image to a byte buffer
    buffer = io.BytesIO()
    result_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return result_image, image_bytes 


def summarizer(content, inpainting=None):
    if inpainting is None:
        system_prompt = pr.summarizer_prompt
    else:
        system_prompt = pr.summarizer_prompt_inpainting
    completion = client.chat.completions.create(
        model=model, #"gpt-3.5-turbo-16k",  # gpt-4 #gpt-4-0125-preview
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        stream=False
    )
    
    print(str(completion.choices[0].message.content))# + " Photorealism, Sharp Image, wide shot")
    return str(completion.choices[0].message.content)# + " realistic humans " #" long exposure, blurred motion, streaks of light, surreal, dreamy, ghosting effect, highly detailed"


def generate_inpainting_keywords(data_changes):
    # Check if the DataFrame is empty or missing the necessary columns
    if data_changes.empty or 'midValue' not in data_changes.columns:
        return ["no significant change"]
    data_changes['name'] = data_changes['name'].str.replace('“', '', regex=False).str.replace('”', '', regex=False).str.replace('"', '', regex=False)
    print(data_changes)

    # Example: Select the change with the highest 'midValue' as the most significant
    # Find the index of the row with the highest 'midValue'
    idx_max_midValue = data_changes['midValue'].astype('float').abs().idxmax()

    # Retrieve the 'name' from the row with the highest 'midValue'
    most_significant_change_name = data_changes.loc[idx_max_midValue, 'name']
    print(most_significant_change_name)
    
    #change_name = most_significant_change['name']  # Assuming the name of the change is in the 'name' column
    #impact = 'increase' if most_significant_change['midValue'] > 0 else 'decrease'

    # Mapping of change types to potential keywords
    climate_change_qualifiers = {
    'Change in total annual precipitation': 'heavy rain, flooding, gloomy skies',
    'Change in wettest 90 days': 'increased rainfall, frequent storms, saturated grounds',
    'Change in dry hot days': 'intense sunlight, heat haze, dry atmosphere',
    'Change in frequency of 1-in-100-year storm': 'severe storms, extreme weather events, damaged infrastructure',
    'Change in precipitation 1-in-100-year storm': 'torrential rain, flash floods, overflowing rivers',
    'Likelihood of year-plus extreme drought': 'faded colors, heat mirages, stark shadows',
    'Likelihood of year-plus drought': 'heat haze, dusty air, sun-bleached surfaces',
    'Change in wildfire danger days': 'smoky haze, distant glow of fires, ash particles in air'
}

    # Retrieve qualifiers for the most significant change category
    qualifiers = climate_change_qualifiers.get(most_significant_change_name, ["change not specified"])
    #qualifiers_string = ", ".join([str(qualifier) for qualifier in qualifiers])
    
    print(qualifiers)
    return qualifiers