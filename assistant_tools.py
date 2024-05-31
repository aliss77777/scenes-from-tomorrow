import os
import json
import pandas as pd

import requests
from openai import OpenAI
from datetime import date
from datetime import datetime

from dotenv import load_dotenv
import sys

import prompts as pr
import helper_functions as hf

pf_api_url = "https://graphql.probablefutures.org"
#pf_token_audience = "https://graphql.probablefutures.com"
#pf_token_url = "https://probablefutures.us.auth0.com/oauth/token"

load_dotenv()
#client = OpenAI()

def get_pf_data_timeline(address, country, warming_scenario='1.5', units='C'):
    variables = {}

    location = f"""
        country: "{country}"
        address: "{address}"
    """

    query = (
            """
            mutation {
                getDatasetStatistics(input: { """
            + location
            + """ \
                    warmingScenario: \"""" + warming_scenario + """\" 
                }) {
                datasetStatisticsResponses{
                    datasetId
                    name
                    unit
                    warmingScenario
                    midValue
                    highValue
                    mapCategory
                }
            }
        }
    """
    )
    #print(query)

    access_token = hf.get_pf_token()
    url = pf_api_url + "/graphql"
    headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + access_token
        }
    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )

    response = str(response.json()).replace("'", '"')
    response = response.replace("None", "null")

    parsed_output = hf.json_to_dataframe(response, address=address, country=country)

    if units.lower() in ('f', 'fahrenheit'):
        parsed_output.loc[parsed_output.unit == '°C', 'midValue'] = (((parsed_output.loc[parsed_output.unit == '°C', 'midValue'].astype('float') * 9) / 5) + 32).round()
        parsed_output.loc[parsed_output.unit == '°C', 'highValue'] = (((parsed_output.loc[parsed_output.unit == '°C', 'highValue'].astype('float') * 9) / 5) + 32).round()
        parsed_output.loc[parsed_output.unit == 'mm', 'midValue'] = (parsed_output.loc[parsed_output.unit == 'mm', 'midValue'].astype('float') / 25.4).round(1)
        parsed_output.loc[parsed_output.unit == 'mm', 'highValue'] = (parsed_output.loc[parsed_output.unit == 'mm', 'highValue'].astype('float') / 25.4).round(1)
        parsed_output.loc[parsed_output.unit == '°C', 'unit'] = '°F'
        parsed_output.loc[parsed_output.unit == 'mm', 'unit'] = 'inches'

    print("got output of pf_data_new")

    #summary = summary_completion(str(address) + " " + str(country))

    return parsed_output 