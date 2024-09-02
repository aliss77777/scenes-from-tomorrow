import os
import json
from typing import Dict, Optional
from openai import AsyncOpenAI
from openai.types.beta.threads.run import Run
from openai.types.beta import Thread
from openai.types.beta.threads import (
    ImageFileContentBlock,
    TextContentBlock,
    Message,
)
import chainlit as cl
from chainlit.context import context
import assistant_tools as at
import prompts as pr
import helper_functions as hf 
import datetime
import csv
from utils import DictToObject, stream_message, ask_to_continue, process_thread_message

# Initialize API client
api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)
assistant_id = os.environ.get("ASSISTANT_ID")

@cl.on_chat_start
async def start_chat():
    # Start a new chat session and set the thread context
    thread = await client.beta.threads.create()
    cl.user_session.set("thread", thread)
    await cl.Message(author="Climate Change Assistant", content=pr.welcome_message).send()

@cl.on_message
async def run_conversation(message_from_ui: cl.Message):
    # Initialize variables and fetch thread from user session
    thread = cl.user_session.get("thread")  # type: Thread

    # Create initial user message in thread
    init_message = await client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message_from_ui.content
    )

    # Display a loader message in UI
    loader_msg = cl.Message(author="Climate Change Assistant", content="")
    await loader_msg.send()

    # Create and poll a new run for the conversation
    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_id
    )

    message_references = {}  # Dictionary to store references to messages

    while True:
        print('Starting loop to check run updates...')
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )

        # Fetch the run steps in ascending order
        run_steps = await client.beta.threads.runs.steps.list(
            thread_id=thread.id, run_id=run.id, order="asc"
        )

        for step in run_steps.data:
            # Retrieve details for each run step
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread.id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details

            # Handle message creation steps
            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread.id,
                )
                await process_thread_message(message_references, thread_message)

            # Handle tool call steps
            if step_details.type == "tool_calls":
                loading_message = "Retrieving information, please stand by."
                loading_message_to_assistant = cl.Message(
                    author="Climate Change Assistant", content=loading_message
                )
                await loading_message_to_assistant.send()

                for tool_call in step_details.tool_calls:
                    # Convert tool call to object if it's a dictionary
                    if isinstance(tool_call, dict):
                        tool_call = DictToObject(tool_call)
                        if tool_call.type == "function":
                            tool_call.function = DictToObject(tool_call.function)
                        if tool_call.type == "code_interpreter":
                            tool_call.code_interpretor = DictToObject(tool_call.code_interpretor)

                    if (
                        tool_call.type == "function"
                        and len(tool_call.function.arguments) > 0
                    ):
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Check if tool call has been referenced before
                        if tool_call.id not in message_references:
                            message_references[tool_call.id] = cl.Message(
                                author=function_name,
                                content=function_args,
                                language="json",
                            )

                            # Perform actions based on function name
                            function_mappings = {
                                "get_pf_data_timeline": at.get_pf_data_timeline,
                            }

                            function_name = function_name.replace("_schema", "")

                            if function_name == "get_pf_data_timeline":
                                address = function_args['address']
                                country = function_args['country']
                                units = function_args.get('units', 'C')

                                print(f"Address: {address}, Country: {country}, Units: {units}")

                                parsed_output = at.get_pf_data_timeline(address, country, '1.5', units)

                                if parsed_output is not None:
                                    output = ""

                                    loading_message_to_assistant = cl.Message(
                                        author="Climate Change Assistant", content=pr.timeline_message
                                    )
                                    await loading_message_to_assistant.send()

                                    # filtering the results to describing current temperatures
                                    summary = hf.story_completion(
                                        pr.one_five_degree_prompt, units, 
                                        parsed_output[parsed_output.name.str.contains("10 hottest") | parsed_output.name.str.contains("Days above 35")]
                                    )

                                    next_output = await stream_message(summary, cl)
                                    output += next_output

                                    img_content, image_bytes = hf.get_image_response_SDXL(
                                            pr.image_prompt_SDXL + address + ' ' + country
                                            )
                                    img = cl.Image(
                                        content=image_bytes, name="image1", display="inline", size="large"
                                    )
                                    await cl.Message(author="Climate Change Assistant", content=' ', elements=[img]).send()

                                    res = await ask_to_continue()

                                    while res and res.get("value") == "question":
                                        question = await cl.AskUserMessage(content='How can I help?', timeout=180).send()
                                        question_response = hf.summary_completion(
                                            address, country, output, question['output']
                                        )
                                        next_output = await stream_message(question_response, cl)
                                        output += next_output
                                        res = await ask_to_continue()

                                    warming_scenario = ['2.0', '3.0']

                                    for i in range(len(warming_scenario)):
                                        parsed_output = at.get_pf_data_timeline(
                                            address, country, warming_scenario[i], 'C'
                                            )
                                        summary = hf.story_completion(
                                            pr.timeline_prompts[i], units, 
                                            parsed_output[parsed_output.name.str.contains('Change') | parsed_output.name.str.contains('Likelihood')]
                                        )
                                        next_output = await stream_message(summary, cl)
                                        output += next_output

                                        data_changes = parsed_output[
                                            parsed_output['name'].str.contains('Change') | 
                                            parsed_output['name'].str.contains('Likelihood')
                                        ].copy()
                                        inpainting_keywords = hf.generate_inpainting_keywords(data_changes)

                                        img_content, image_bytes = hf.get_image_response_SDXL(
                                            prompt=pr.image_prompt_SDXL + address + ' ' + country, 
                                            image_path=img_content, filtered_keywords=inpainting_keywords
                                        )
                                        img = cl.Image(
                                            content=image_bytes, name="image1", display="inline", size="large"
                                        )
                                        await cl.Message(author="Climate Change Assistant", content=' ', elements=[img]).send()

                                        res = await ask_to_continue()

                                        while res and res.get("value") == "question":
                                            question = await cl.AskUserMessage(content='How can I help?', timeout=180).send()
                                            question_response = hf.summary_completion(
                                                address, country, output, question['output']
                                            )
                                            next_output = await stream_message(question_response, cl)
                                            output += next_output
                                            res = await ask_to_continue()

                                    final_message_content = hf.summary_completion(
                                        address, country, output, 
                                        "Please give the user a personalized set of recommendations for how to adapt to climate change for their location and the questions they have asked (if any)."
                                    )
                                    next_output = await stream_message(final_message_content, cl)
                                    output += next_output

                                    res_want_feedback = await cl.AskActionMessage(
                                        content="Would you like to offer feedback?",
                                        actions=[
                                            cl.Action(name="yes", value="yes", label="✅ Yes"),
                                            cl.Action(name="no", value="no", label="🚫 No")
                                        ],
                                        timeout=180
                                    ).send()

                                    if res_want_feedback.get("value") == "yes":
                                        res_feedback = await cl.AskActionMessage(
                                            content="How was your experience?",
                                            actions=[
                                                cl.Action(name="good", value="good", label="😀 Good. I'm ready to take action"),
                                                cl.Action(name="IDK", value="IDK", label="😐 Not sure"),
                                                cl.Action(name="no_good", value="no_good", label="🙁 Not good"),
                                            ], 
                                            timeout=180
                                        ).send()

                                        if res_feedback.get("value") == "good":
                                            await cl.Message(author="Climate Change Assistant", content="Thanks for your feedback!").send()

                                        elif res_feedback.get("value") in ["no_good", "IDK"]:
                                            res_reason = await cl.AskUserMessage(content="Could you please tell us why?").send()
                                            await cl.Message(author="Climate Change Assistant", content="Thanks for your feedback!").send()

                                    await cl.Message(author="Climate Change Assistant", content=pr.next_steps).send()

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

        # Check if run has finished or failed, exit loop if so
        if run.status in ["cancelled", "failed", "completed", "expired"]:
            if run.status == "failed":
                print('Run failed: ', run)
            break
