from openai import AsyncOpenAI
from openai.types.beta.threads.run import Run
from openai.types.beta import Thread
from openai.types.beta.threads import (
    ImageFileContentBlock,
    TextContentBlock,
    Message,
)
import chainlit as cl
from typing import Optional, Dict
from chainlit.context import context

class DictToObject:
    """
    A utility class that converts a dictionary into an object with attributes
    corresponding to the dictionary keys.

    Attributes:
        dictionary (dict): The dictionary to convert.
    """
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)

async def stream_message(question_response, cl, initial_content=""):
    """
    Streams a message back to the user. 

    Since native streaming is not supported in assistants + chainlit v1, this function
    manually streams the content of a message to the user.

    Args:
        question_response: The response containing the message content to stream.
        cl: The Chainlit instance for sending messages.
        initial_content (str): Initial content to send before streaming starts.

    Returns:
        str: The complete streamed output.
    """
    msg = cl.Message(content=initial_content)
    await msg.send()

    next_output = ""

    for part in question_response:
        # Stream each token in the message to the user interface
        if token := part.choices[0].delta.content or "":
            next_output += token
            await msg.stream_token(token)

    await msg.update()
    return next_output

async def ask_to_continue():
    """
    Sends a message asking the user to continue or ask a question.

    Returns:
        cl.AskActionMessage: A Chainlit message instance prompting user action.
    """
    return await cl.AskActionMessage(
        content="Click to continue",
        actions=[
            cl.Action(name="keep_going", value="next", label="➡️ Let's keep going"),
            cl.Action(name="ask_question", value="question", label="︖ Ask a question")
        ],
        timeout=600
    ).send()

async def process_thread_message(message_references: Dict[str, cl.Message], thread_message):
    """
    Processes messages from a thread and updates or sends them to the user.

    Args:
        message_references (Dict[str, cl.Message]): A dictionary storing references to existing messages.
        thread_message: The thread message containing content to process.
    """
    for idx, content_message in enumerate(thread_message.content):
        id = thread_message.id + str(idx)
        if isinstance(content_message, TextContentBlock):
            # Update existing message if found, otherwise send a new message
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
            # Process image messages
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
                await message_references[id].send()
        else:
            print("Unknown message type", type(content_message))
