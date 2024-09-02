import os
import json
import pandas as pd
import requests
from openai import OpenAI
from datetime import date, datetime
from dotenv import load_dotenv
import sys
import io
import base64
import urllib
from PIL import Image
import cv2
from diffusers import AutoPipelineForText2Image, AutoPipelineForImage2Image
import torch
import prompts as pr

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# API URL for Probable Futures (if needed for future use)
pf_api_url = "https://graphql.probablefutures.org"


model = "gpt-4o"  # Model configuration for OpenAI

pipeline_text2image = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16"
)
pipeline_image2image = AutoPipelineForImage2Image.from_pretrained(
    "stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16"
)
pipeline_text2image.to("cuda")
pipeline_image2image.to("cuda")

def convert_to_iso8601(date_str):
    """
    Converts a date string to ISO 8601 format with timezone offset.

    Args:
        date_str (str): The date string to convert.

    Returns:
        str: The date string in ISO 8601 format, or the original string if parsing fails.
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        iso8601_date = date_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return iso8601_date
    except ValueError:
        return date_str

def get_pf_token():
    """
    Retrieves an access token for the Probable Futures API.

    Returns:
        str: The access token if successful, None otherwise.
    """
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    url = 'https://graphql.probablefutures.org/auth/token'

    encoded_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {'Authorization': 'Basic ' + encoded_credentials}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        access_token = data['access_token']
        return access_token
    except requests.exceptions.RequestException as e:
        print('There was a problem with your request:', e)
        return None

def json_to_dataframe(json_data, address, country):
    """
    Converts JSON data to a pandas DataFrame.

    Args:
        json_data (str): The JSON data as a string.
        address (str): Address associated with the data.
        country (str): Country associated with the data.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the extracted data.
    """
    json_data = json.loads(json_data)
    data = json_data['data']['getDatasetStatistics']['datasetStatisticsResponses']
    df = pd.DataFrame(data)
    df['address'] = address
    df['country'] = country
    df = df[['address', 'country', 'name', 'midValue', 'highValue', 'unit', 'mapCategory']]
    df = df[~((df['midValue'] == '0.0') & (df['highValue'] == '0.0'))]
    df.reset_index(drop=True, inplace=True)
    
    return df

def summary_completion(address, country, output, user_question):
    """
    Generates a summary completion based on user input and previous information.

    Args:
        address (str): The address for context.
        country (str): The country for context.
        output (str): The previous output provided to the user.
        user_question (str): The user's question to be answered.

    Returns:
        OpenAI response: The completion response from OpenAI.
    """
    content = f"Please answer the user question {user_question} for the location of {address} {country}. Use the information that was just provided previously to the user: {output}"
    print(content)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": pr.user_question_prompt},
            {"role": "user", "content": content}
        ],
        stream=True
    )

    return completion

def story_completion(story_system_prompt, units, content):
    """
    Generates a story completion based on provided content.

    Args:
        story_system_prompt (str): The prompt for the story system.
        units (str): The temperature scale to use in the story.
        content (pd.DataFrame): The content to include in the story.

    Returns:
        OpenAI response: The completion response from OpenAI.
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": str(story_system_prompt + ". Be sure to describe the result using the following temperature scale: " + units)},
            {"role": "user", "content": str(content.to_json())}
        ],
        stream=True
    )

    return completion

def get_image_response_SDXL(prompt, image_path=None, filtered_keywords=None):
    """
    Generates an image using the SDXL pipeline.

    Args:
        prompt (str): The text prompt to generate the image.
        image_path (str, optional): The path to an existing image to modify.
        filtered_keywords (str, optional): Keywords for inpainting scenarios.

    Returns:
        tuple: The generated image and its byte representation.
    """
    print('starting SDXL')
    
    if image_path is None:
        result_image = pipeline_text2image(
            prompt=prompt, num_inference_steps=2, guidance_scale=0.0
        ).images[0]
    else:
        modified_prompt = filtered_keywords if filtered_keywords else prompt
        print(modified_prompt)

        result_image = pipeline_image2image(
            prompt=modified_prompt, image=image_path, strength=0.55, guidance_scale=0.0, num_inference_steps=2
        ).images[0]

    buffer = io.BytesIO()
    result_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return result_image, image_bytes

def summarizer(content, inpainting=None):
    """
    Generates a summary of the provided content.

    Args:
        content (str): The content to summarize.
        inpainting (bool, optional): Whether to use inpainting prompts.

    Returns:
        str: The summarized content.
    """
    system_prompt = pr.summarizer_prompt if inpainting is None else pr.summarizer_prompt_inpainting
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        stream=False
    )
    
    print(str(completion.choices[0].message.content))
    return str(completion.choices[0].message.content)

def generate_inpainting_keywords(data_changes):
    """
    Generates keywords for inpainting based on data changes.

    Args:
        data_changes (pd.DataFrame): The DataFrame containing data changes.

    Returns:
        list: A list of keywords describing significant changes.
    """
    if data_changes.empty or 'midValue' not in data_changes.columns:
        return ["no significant change"]

    data_changes['name'] = data_changes['name'].str.replace('“', '', regex=False).str.replace('”', '', regex=False).str.replace('"', '', regex=False)
    print(data_changes)

    idx_max_midValue = data_changes['midValue'].astype('float').abs().idxmax()
    most_significant_change_name = data_changes.loc[idx_max_midValue, 'name']
    print(most_significant_change_name)
    
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

    qualifiers = climate_change_qualifiers.get(most_significant_change_name, ["change not specified"])
    print(qualifiers)
    return qualifiers
