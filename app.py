import os
import json
from typing import Dict

from openai import AsyncOpenAI
from openai.types.beta.threads.run import Run

from openai.types.beta import Thread
from openai.types.beta.threads import (
    ImageFileContentBlock,
    TextContentBlock,
    Message,
)

import chainlit as cl
from typing import Optional
from chainlit.context import context

import assistant_tools as at
import prompts as pr
import helper_functions as hf 
import datetime
import csv

from utils import DictToObject, stream_message, ask_to_continue, process_thread_message

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)
assistant_id = os.environ.get("ASSISTANT_ID")


@cl.on_chat_start
async def start_chat():
    thread = await client.beta.threads.create()
    cl.user_session.set("thread", thread)
    await cl.Message(author="Climate Change Assistant", content=pr.welcome_message).send()


@cl.on_message
async def run_conversation(message_from_ui: cl.Message):
    count = 0
    thread = cl.user_session.get("thread")  # type: Thread
    # Add the message to the thread

    init_message = await client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message_from_ui.content
    )

    # Send empty message to display the loader
    loader_msg = cl.Message(author="Climate Change Assistant", content="")
    await loader_msg.send()

    # Create the run
    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_id
    )

    message_references = {}  # type: Dict[str, cl.Message]

    # Periodically check for updates
    #running = True
    while True:
        print('starting while True loop')
        print(run)
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )

        # Fetch the run steps
        run_steps = await client.beta.threads.runs.steps.list(
            thread_id=thread.id, run_id=run.id, order="asc"
        )

        for step in run_steps.data:
            # Fetch step details
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread.id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details
            # Update step content in the Chainlit UI
            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread.id,
                )
                await process_thread_message(message_references, thread_message)

            print("line 116 about the call the tools call loop")
            count += 1
            print(str(count))

            if step_details.type == "tool_calls":
                loading_message = "Retrieving information, please stand by."
                loading_message_to_assistant = cl.Message(author="Climate Change Assistant", content=loading_message)
                await loading_message_to_assistant.send()  # output_message_to_assistant.send()

                for tool_call in step_details.tool_calls:
                    print('top of tool call loop line 119')

                    # IF tool call is a disctionary, convert to object
                    if isinstance(tool_call, dict):
                        print("here is a tool call at line 120")
                        print(tool_call)
                        tool_call = DictToObject(tool_call)
                        if tool_call.type == "function":
                            function = DictToObject(tool_call.function)
                            tool_call.function = function
                        if tool_call.type == "code_interpreter":
                            code_interpretor = DictToObject(tool_call.code_interpretor)
                            tool_call.code_interpretor = code_interpretor

                    print("here are step details at line 130")
                    print(step_details)
                    print("here is tool call at line 132")
                    print(tool_call)
                    
                    if (
                        tool_call.type == "function"
                        and len(tool_call.function.arguments) > 0
                                ):
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        if not tool_call.id in message_references:
                            message_references[tool_call.id] = cl.Message(
                                author=function_name,
                                content=function_args,
                                language="json",
                                #parent_id=context.session.root_message.id,
                            )
                            #await message_references[tool_call.id].send()

                            function_mappings = {
                                #"get_pf_data_handbook": at.get_pf_data_handbook,
                                "get_pf_data_timeline": at.get_pf_data_timeline,
                            }

                            # Not sure why, but sometimes this is returned rather than name
                            function_name = function_name.replace("_schema", "")

                            print(f"FUNCTION NAME: {function_name}")
                            print(function_args)

                            if function_name == "get_pf_data_timeline":

                                # Extract 'address' and 'country' values
                                address = function_args['address']
                                country = function_args['country']
                                units = function_args.get('units', 'C') #returns the specific value for 'units' else C if blank

                                print(f"Address: {address}, Country: {country}, Units: {units}")

                                parsed_output = at.get_pf_data_timeline(address, country, '1.5', units)

                                if parsed_output is not None:
                                    
                                    print(f"RUN STATUS: {run.status} from first timeline scene")
                                    print(run)
                                    
                                    
                                    # creating an initial output of what life is like today in that place
                                    output = ""

                                    loading_message_to_assistant = cl.Message(author="Climate Change Assistant", content=pr.timeline_message)
                                    await loading_message_to_assistant.send()

                                    # filtering the results to just show results describing average / baseline temperatures
                                    summary = hf.story_completion(pr.one_five_degree_prompt, units, parsed_output[parsed_output.name.str.contains("10 hottest") | parsed_output.name.str.contains("Days above 35")])

                                    next_output = await stream_message(summary, cl)

                                    output += next_output

                                    print(next_output) # hf.summarizer(output)
                                    img_content, image_bytes = hf.get_image_response_SDXL(pr.image_prompt_SDXL + address + ' ' + country) #hf.summarizer(output)
                                    #with open('feedback_logs/73ee4d67-4857-47ec-b835-5b1cfb570b20.png', 'rb') as file:
                                    #        img_content = file.read()
                                    img = cl.Image(content=image_bytes, name="image1", display="inline", size="large") # img_content
                                    print('\n Generating image, complete')
                                    image_message_to_assistant = cl.Message(author="Climate Change Assistant", content=' ', elements=[img])
                                    await image_message_to_assistant.send()

                                    #adding button to allow user to paginate the content
                                    res = await ask_to_continue()

                                    while res and res.get("value") == "question":

                                        question = await cl.AskUserMessage(content='How can I help?', timeout=180).send()
    
                                        # Use this to send the output of completion request into the next OpenAI API call.
                                        question_response = hf.summary_completion(address, country, output, question['output'])

                                        next_output = await stream_message(question_response, cl)

                                        output += next_output

                                           
                                        # Call the function again instead of duplicating the code block
                                        res = await ask_to_continue()
                                        

                                    warming_scenario = ['2.0', '3.0']
                                    
                                    #inpainting_keywords = ''

                                    for i in range(len(warming_scenario)):
                                        print(f"RUN STATUS: {run.status} from timeline scene # {i}")
                                        print(run)

                                        # going to force units to be C b/c otherwise it's breaking the logic for how the 2/3 image gets displayed
                                        parsed_output = at.get_pf_data_timeline(address, country, warming_scenario[i], 'C') #units
                                        
                                        # filterine results to talk about change from baseline 
                                        summary = hf.story_completion(pr.timeline_prompts[i], units, parsed_output[parsed_output.name.str.contains('Change') | parsed_output.name.str.contains('Likelihood')])
                                        next_output = await stream_message(summary, cl)

                                        output += next_output

                                        data_changes = parsed_output[parsed_output['name'].str.contains('Change') | parsed_output['name'].str.contains('Likelihood')].copy()
                                        #print(data_changes)
                                        inpainting_keywords = hf.generate_inpainting_keywords(data_changes) 

                                        img_content, image_bytes = hf.get_image_response_SDXL(prompt=pr.image_prompt_SDXL + address + ' ' + country, image_path = img_content, filtered_keywords=inpainting_keywords) #str(hf.summarizer(output))
                                        #with open('feedback_logs/73ee4d67-4857-47ec-b835-5b1cfb570b20.png', 'rb') as file:
                                        #   img_content = file.read()
                                        img = cl.Image(content=image_bytes, name="image1", display="inline", size="large") #img_content
                                        print('\n generating image, complete')
                                        image_message_to_assistant = cl.Message(author="Climate Change Assistant", content=' ', elements=[img])
                                        await image_message_to_assistant.send() 

                                        #adding button to allow user to paginate the content
                                        res = await ask_to_continue()

                                        while res and res.get("value") == "question":

                                            question = await cl.AskUserMessage(content='How can I help?', timeout=180).send()
        
                                            # Use this to send the output of completion request into the next OpenAI API call.
                                            question_response = hf.summary_completion(address, country, output, question['output'])

                                            next_output = await stream_message(question_response, cl)

                                            output += next_output

                                            
                                            # Call the function again instead of duplicating the code block
                                            res = await ask_to_continue()
                                            
                                        #else:
                                        #    run.status = "completed"
                                    
                                    
                                    final_message_content = hf.summary_completion(address, country, output, "Please give the user a personalized set of recommendations for how to adapt to climate change for their location and the questions they have asked (if any).")
                                    next_output = await stream_message(final_message_content, cl)
                                    output += next_output
                                    
                                    # Step 1: Ask users if they'd like to offer feedback
                                    res_want_feedback = await cl.AskActionMessage(content="Would you like to offer feedback?",
                                                                                actions=[
                                                                                    cl.Action(name="yes", value="yes", label="✅ Yes"),
                                                                                    cl.Action(name="no", value="no", label="🚫 No")],
                                                                                timeout=180).send()

                                    # Only proceed if they want to give feedback
                                    if res_want_feedback.get("value") == "yes":
                                        # Step 2: Ask "How was your experience?"
                                        res_feedback = await cl.AskActionMessage(content="How was your experience?",
                                                                                actions=[
                                                                                    cl.Action(name="good", value="good", label="😀 Good. I'm ready to take action"),
                                                                                    cl.Action(name="IDK", value="IDK", label="😐 Not sure"),
                                                                                    cl.Action(name="no_good", value="no_good", label="🙁 Not good"),], 
                                                                                timeout=180).send()

                                        if res_feedback.get("value") == "good":
                                            thank_you_message = cl.Message(author="Climate Change Assistant", content="Thanks for your feedback!")
                                            await thank_you_message.send()

                                        # Step 3: If "no good" or "not sure," ask why
                                        elif res_feedback.get("value") in ["no_good", "IDK"]:
                                            res_reason = await cl.AskUserMessage(content="Could you please tell us why?").send()

                                            # Step 4: Capture user open-ended comments and write to a CSV file // UPDATE: Literal.AI data layer handles this
                                            #filename = f"feedback_logs/feedback_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                            
                                            #with open(filename, "a", newline='') as csvfile:
                                            #    feedback_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                                            #    # Write column headers if the file is new/empty
                                            #    if csvfile.tell() == 0:
                                            #        feedback_writer.writerow(["Thread ID", "Feedback Value", "Reason Output"])
                                            #    # Assuming thread_id is available from earlier in your session
                                            #    thread = cl.user_session.get("thread")
                                            #    feedback_writer.writerow([thread.id, res_feedback.get('value'), res_reason['output'] if res_reason['output'] is not None else ''])
                                            
                                            thank_you_message = cl.Message(author="Climate Change Assistant", content="Thanks for your feedback!")
                                            await thank_you_message.send()
                                    
                                    next_steps = cl.Message(author="Climate Change Assistant", content=pr.next_steps)
                                    await next_steps.send()
                                    
                                    print('here is the bottom of the if feedback block')
                                    print(run.status)
                                    #run.status = "completed" 
                                
                                print('here is the bottom of the if pf.function is not none block')
                                print(run.status)
                                #run.status = "completed"

                                run = await client.beta.threads.runs.submit_tool_outputs_and_poll(
                                        thread_id=thread.id,
                                        run_id=run.id,
                                        tool_outputs=[
                                            {
                                                "tool_call_id": tool_call.id,
                                                "output": str(parsed_output),
                                            },
                                            ],
                                        )

                            print('here is the bottom of the IF tool call is function block')
                            #run.status = "completed"
                            print(run.status)
                            

        #await cl.sleep(1)  # Refresh every second

        if run.status == "completed":
            print(f"RUN STATUS: {run.status} from the bottom of the code")
            #running = False
            #run = await client.beta.threads.runs.cancel(
            #    thread_id=thread.id,
            #    run_id=run.id
            #    )
            print(run)
            break

        




        if run.status in ["cancelled", "failed", "completed", "expired"]:

            if run.status == "failed":
                print('here is the failed run: ', run)
            break
            print('completed')
