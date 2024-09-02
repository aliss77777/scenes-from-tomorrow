from typing_extensions import override
from openai import AssistantEventHandler

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
from typing import Dict
from chainlit.context import context

class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)

async def stream_message(question_response, cl, initial_content=""):
    '''handler to stream a message back to user. native streaming not supported in assistants + chainlit v1'''
    msg = cl.Message(content=initial_content)
    await msg.send()

    next_output = ""

    for part in question_response:
        if token := part.choices[0].delta.content or "":
            next_output += token
            await msg.stream_token(token)

    await msg.update()
    return next_output

async def ask_to_continue():
    '''a button for the user to click to continue '''
    return await cl.AskActionMessage(
        content="Click to continue ",
        actions=[
            cl.Action(name="keep_going", value="next", label="➡️ Let's keep going"),
            cl.Action(name="ask_question", value="question", label="︖ Ask a question")
        ],
        timeout=600
    ).send()

async def process_thread_message(message_references: Dict[str, cl.Message], thread_message):
    for idx, content_message in enumerate(thread_message.content):
        id = thread_message.id + str(idx)
        if isinstance(content_message, TextContentBlock):
            if id in message_references:
                msg = message_references[id]
                msg.content = content_message.text.value
                await msg.update()
            else:
                message_references[id] = cl.Message(
                    author=thread_message.role, content=content_message.text.value
                )
                await message_references[id].send()
        elif isinstance(content_message, MessageContentImageFile):
            image_id = content_message.image_file.file_id
            response = await client.files.with_raw_response.retrieve_content(image_id)
            elements = [
                cl.Image(
                    name=image_id,
                    content=response.content,
                    display="inline",
                    size="large",
                ),
            ]
            if id not in message_references:
                message_references[id] = cl.Message(
                    author=thread_message.role,
                    content="",
                    elements=elements,
                )
                await message_references[id]. send()
        else:
            print("unknown message type", type(content_message))

class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
