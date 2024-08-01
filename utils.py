from openai import AsyncAssistantEventHandler, AsyncOpenAI
from openai.types.beta.threads.run import Run

from openai.types.beta import Thread
from openai.types.beta.threads import (
    ImageFileContentBlock,
    TextContentBlock,
    Message,
)
from literalai.helper import utc_now

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
    print('calling stream message function')
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

class EventHandler(AsyncAssistantEventHandler):

    def __init__(self, assistant_name: str) -> None:
        super().__init__()
        self.current_message: cl.Message = None
        self.current_step: cl.Step = None
        self.current_tool_call = None
        self.assistant_name = assistant_name

    async def on_text_created(self, text) -> None:
        self.current_message = await cl.Message(author=self.assistant_name, content="").send()

    async def on_text_delta(self, delta, snapshot):
        await self.current_message.stream_token(delta.value)

    async def on_text_done(self, text):
        await self.current_message.update()

    async def on_tool_call_created(self, tool_call):
        self.current_tool_call = tool_call.id
        self.current_step = cl.Step(name=tool_call.type, type="tool")
        self.current_step.language = "python"
        self.current_step.created_at = utc_now()
        await self.current_step.send()

    async def on_tool_call_delta(self, delta, snapshot): 
        if snapshot.id != self.current_tool_call:
            self.current_tool_call = snapshot.id
            self.current_step = cl.Step(name=delta.type, type="tool")
            self.current_step.language = "python"
            self.current_step.start = datetime.utcnow()
            await self.current_step.send()  
                 
        if delta.type == "code_interpreter":
            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        error_step = cl.Step(
                            name=delta.type,
                            type="tool"
                        )
                        error_step.is_error = True
                        error_step.output = output.logs
                        error_step.language = "markdown"
                        error_step.start = self.current_step.start
                        error_step.end = datetime.utcnow()
                        await error_step.send()
            else:
                if delta.code_interpreter.input:
                    await self.current_step.stream_token(delta.code_interpreter.input)

    async def on_tool_call_done(self, tool_call):
        self.current_step.end = utc_now()
        await self.current_step.update()

    async def on_image_file_done(self, image_file):
        image_id = image_file.file_id
        response = await async_openai_client.files.with_raw_response.content(image_id)
        image_element = cl.Image(
            name=image_id,
            content=response.content,
            display="inline",
            size="large"
        )
        if not self.current_message.elements:
            self.current_message.elements = []
        self.current_message.elements.append(image_element)
        await self.current_message.update()