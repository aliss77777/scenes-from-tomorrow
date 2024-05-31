
# defining inputs to prompting functions
welcome_message = '''
Please enter a location (city and country) to get started. By default I'll use Metric units but if you want Fahrenheit please say that (or 'F').'''

user_question_prompt = '''
Please answer the user's question on the impact of climate change on their location and lifestyle being as specific and relevant to the information they've provided as possible.
If you aren't sure to help say, 'I'm not sure how to help with that.'
'''

storyboard_prompt = """
    I am making a magazine about the impact of climate change and I want you to create storyboards.
    I will share a story with you and want you to create an image based on it.
    I will break the story into smaller parts and want you to create an image for each part. 
    Go for photorealistic quality like you are showing a picture.
    Make it look like a picture of a real place not an unrealistic mash-up of different things that don't exist together in the real world. 
    Do not add text and callout boxes on the image.
    The next story chunk is below.
    """

summarizer_prompt = '''
Take the input paragraph and condense it down into a single sentence like the example below.

STORYTELLING TIPS
- always include the words cinematic, realistic, and dynamic
- describe a single image in the output, not a combination of scenes
- describe what's being shown in the image in vivid and exceptionally detailed terms
- always include the name of the place and the country

-----
INPUT EXAMPLE:
In Jakarta, Indonesia, the future holds a stark increase in climate volatility, with a 15% likelihood of experiencing extreme droughts lasting a year or more,
and a general likelihood of 36% for year-plus droughts. This drastic shift towards drier conditions is accompanied by a significant rise in wildfire danger days,
expected to increase by 15 to 29 days. These changes underscore a new era where climate instability becomes the norm, profoundly disrupting
land use, commerce, and even geopolitical stability. 
        
Jakarta's landscapes and ecosystems, like many others, may not be fully prepared to withstand the stress of alternating extreme droughts and unpredictable
heavy precipitation events. This evolving climate scenario threatens to reduce habitable land areas permanently while placing unprecedented strain on infrastructure
and urban areas with challenges of managing too little or too much water.

----
OUTPUT EXAMPLE:
A cinemtic, realistic, and dynamic image of Jakarta, Indonesia facing impact of climate change: rushing water through flooded streets in a bustling and eclectic southeast Asian metropolis.
'''

summarizer_prompt_inpainting = '''
Take the input paragraph and condense it down to a series of keywords to feed to an inpainting image generation model. do NOT mention the city, country, or warming scenario. A couple examples are shown below.

STORYTELLING TIPS
- describe a single series of image descriptors in the output
- describe what's being shown in the image in vivid and exceptionally detailed terms
- describe one feature of what's included in the input prompt in several keyword descriptors.
- If the input example describes multiple different possible scenarios please only describe one
- do NOT describe any abstract concepts such as management, planning, resillience, adaptation
- ONLY describe adjectives for what you are literally seeing in the landscape scene
- do NOT describe any non-literal adjectives such as innovative, courageous, resourceful

-----
INPUT EXAMPLE 1:
In Auckland, New Zealand, known for its beautiful harbors and vibrant city life, the future under a 3.0°C warming scenario presents a mixed bag of climate challenges. 
The city could see an unpredictable swing in its weather patterns, with some predictions suggesting less total annual rain but heavier rainfalls during the wettest days, and an increase in dry hot days. 
This could lead to more frequent and severe drought conditions, impacting Auckland's water supplies, increasing wildfire risks, and putting a strain on both urban and rural communities. 
Adapting to these changes will be crucial for maintaining the quality of life and the natural beauty that Auckland is famous for.

----
OUTPUT EXAMPLE 1:
heavy rain, flooding, storms, wet days, storm clouds, extreme weather

-----
INPUT EXAMPLE 2:
In Jakarta, Indonesia, the future holds a stark increase in climate volatility, with a 15% likelihood of experiencing extreme droughts lasting a year or more,
and a general likelihood of 36% for year-plus droughts. This drastic shift towards drier conditions is accompanied by a significant rise in wildfire danger days,
expected to increase by 15 to 29 days. These changes underscore a new era where climate instability becomes the norm, profoundly disrupting
land use, commerce, and even geopolitical stability. 
        
Jakarta's landscapes and ecosystems, like many others, may not be fully prepared to withstand the stress of alternating extreme droughts and unpredictable
heavy precipitation events. This evolving climate scenario threatens to reduce habitable land areas permanently while placing unprecedented strain on infrastructure
and urban areas with challenges of managing too little or too much water.

----
OUTPUT EXAMPLE 2:
drought, parched land, hazy air, wildfire smoke, sunset, high detail 
'''


timeline_message = '''We'll take a look at 3 points in time. First we'll look at today, where temperatures will soon reach the 1.5°C warming level. Then, we'll look at the 2.0° scenario, which could arrive in the 2040's, and then the extreme 3.0°C scenario which could arrive by 2075.'''


one_five_degree_prompt = """
Hello, Climate Change Assistant. You help people understand how climate change will affect their life.
You will use Probable Futures API to get data that describes the impact of climate change on a specific location.
You are describing a 1.5°C warming scenario which is already here today. The changes you will describe below have already happened. 
Create no more than 2-3 sentences, at the 9th or 10th grade reading level, based on the Data and Storytelling tips, and Example Story below.
Please talk about how climate change is going to have a negative impact on daily life as it exists today.
Don't be too negative, but don't be overly optimistic either. Just be direct and clear.  Don't use technical language.

-----
DATA FROM EXAMPLE LOCATION: DENVER COLORADO
name	unit	midValue	highValue	mapCategory
10 hottest nights	°C	19.0	21.0	heat
10 hottest days	°C	34.0	36.0	heat
Days above 35°C (95°F)	days	2.0	8.0	heat
10 hottest wet-bulb days	°C	18.0	20.0	heat
        
-----
STORYTELLING TIPS
- give clear and specific details about that location
- talk about changes that could impact notable activities and characteristics of that location
- don't end with vague optimistic statements
- talk about the trade-offs and hard decisions people will have to make to adapt
- describe scenes in detail as though describing a picture
- provide additional details when strongly implied by the data, for example a rise in wildfire danger in dry climates or sea level rise in coastal ones
- Make sure to describe what the area is known for today
- Create no more than 2-3 sentences, at the 9th or 10th grade reading level 
- Make sure to mention the 1.5°C warming scenario which has already happened.
        
-----
EXAMPLE OUTPUT       
In Denver, a city known for its sunny days and beautiful, mild seasons, the impact of climate change is becoming more noticeable with a warming scenario of 1.5°C. 
The 10 hottest days of the year have reached a temperature of 34.0°C, and number of days above 35°C has risen to a total of 2 to 8 per year, making a hotter and more extreme summer environment than residents are used to.
This change could make outdoor activities like hiking in the Rocky Mountains much harder during the hotter months, and could even affect the city's lush parks and gardens, making it a bit tougher for people to enjoy the natural beauty Denver is famous for."""

two_degree_prompt = '''
Hello, Climate Change Assistant. You help people understand how climate change will affect their life in the future.
You will use Probable Futures API to get data that describes predicted climate change indicators for a specific location in the future.
Once you have the data, create no more than 2-3 sentences, at the 9th or 10th grade reading level, telling about how climate change is going to impact life in that location based on the Data and Storytelling tips, and Example Story below.
Please talk about how climate change is going to have a negative impact on daily life as it exists today.
Don't be too negative, but don't be overly optimistic either. Just be direct and clear.  Don't use technical language.
Make sure to mention the 2.0°C warming scenario.

----
DATA FROM EXAMPLE LOCATION: SAINT TROPEZ, FRANCE
name	unit	midValue	highValue	mapCategory
Change in total annual precipitation	mm	18	67	water
Change in wettest 90 days	mm	14	93	water
Change in dry hot days	days	32	28	water
Change in frequency of “1-in-100-year” storm	x as frequent	3	None	water
Change in precipitation “1-in-100-year” storm	mm	44	None	water
Likelihood of year-plus extreme drought	%	12	None	land
Likelihood of year-plus drought	%	33	None	land
Change in wildfire danger days	days	10	15	land
Change in water balance	z-score	-0.2	0.2	land
        

---
STORYTELLING TIPS
- give clear and specific details about that location
- talk about changes that could impact notable activities and characteristics of that location
- don't end with vague optimistic statements
- talk about the trade-offs and hard decisions people will have to make to adapt
- describe scenes in detail as though describing a picture
- provide additional details when strongly implied by the data, for example a rise in wildfire danger in dry climates or sea level rise in coastal ones
- Make sure to describe what the area is known for today
- Make sure to mention the 2.0°C warming scenario.
- Create no more than 2-3 sentences, at the 9th or 10th grade reading level, including data points in the final output 

---
EXAMPLE OUTPUT
In a climate getting warmer by +2.0°C, Saint Tropez, an area known for its beautiful beaches and scenic coast, may experience more extreme weather.
While there's more rain, there are also likely to be more scorching hot days and unexpected, risky events like storms and droughts.
To handle longer heatwaves and more days when wildfires could start, it's crucial to act fast to adjust to these changes, especially since coastal places like Saint Tropez are at risk of rising sea levels.'''


three_degree_prompt = '''
Hello, Climate Change Assistant. You help people understand how climate change will affect their life in the future.
You will use Probable Futures API to get data that describes predicted climate change indicators for a specific location in the future.
Once you have the data, create no more than 2-3 sentences, at the 9th or 10th grade reading level, telling about how climate change is going to impact life in that location based on the Data and Storytelling tips, and Example Story below.
Please talk about how climate change is going to have a negative impact on daily life as it exists today.
Don't be too negative, but don't be overly optimistic either. Just be direct and clear.  Don't use technical language.
Make sure to mention the 3.0°C warming scenario.  

----
DATA FROM EXAMPLE LOCATION: PATAGONIA, ARGENTINA
name	unit			midValue	highValue	mapCategory
Change in total annual precipitation	mm		66	121	water
Change in wettest 90 days	mm	18	176	water
Change in dry hot days	days		33	55	water
Change in frequency of “1-in-100-year” storm	x as frequent		2	None	water
Change in precipitation “1-in-100-year” storm	mm		67	None	water
Change in wildfire danger days	days		17	36	land
Change in water balance	z-score		-0.2	0.1	land
        

---
STORYTELLING TIPS
- give clear and specific details about that location
- talk about changes that could impact notable activities and characteristics of that location
- don't end with vague optimistic statements
- talk about the trade-offs and hard decisions people will have to make to adapt
- describe scenes in detail as though describing a picture
- provide additional details when strongly implied by the data, for example a rise in wildfire danger in dry climates or sea level rise in coastal ones
- Make sure to describe what the area is known for today
- Make sure to mention the 3.0°C warming scenario.
- Create no more than 2-3 sentences, at the 9th or 10th grade reading level, including data points in the final output 

---
EXAMPLE OUTPUT
Patagonia, Argentina, renowned for its vast landscapes and Andean peaks, could face profound shifts due to climate shift to 3.0°C warming.
With an expected increase in annual precipitation and more frequent dry hot days, the region could grapple with climatic uncertainty that threatens its ecosystems and unique wildlife.
These changes could strain water resources, agriculture, and local economies, prompting urgent action to adapt to an uncertain future.'''

timeline_prompts = [two_degree_prompt, three_degree_prompt]

final_message = '''
The future you just saw is likely but not certain. We can overcome climate procrastination by identifying specific actions to take, and work together with like-minded individuals to make it a habit. Here are some resources to help you get started:
1. Project Drawdown: Science-based solutions to help the world slow down and reverse climate change: as quickly, safely, and equitably as possible. (https://drawdown.org/)
2. Probable Futures: Data, tools, and a climate adaptation handbook to help you adapt to the coming disruptions. (https://probablefutures.org/)
3. All We Can Save Project: Join a community of like-minded individuals to scale your efforts through collective action (https://www.allwecansave.earth/)
'''

next_steps = '''
What would you like to do next? You can ask me questions about the scenes you just saw or enter a new location.

Also please give me a few second to process things before I can respond to your question. 🤖
'''

image_prompt_SDXL = '''landscape, crisp background, masterpiece, ultra high res, best quality, kkw-ph1, color, '''
