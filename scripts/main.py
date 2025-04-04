from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from utils import chat_w_memory, parse_pdf, generate_notes
from history import ChatHistory, connection
import uuid
import gradio as gr
import time
import requests as rq

class ChatInput(BaseModel):
    message: str

class NotesInput(BaseModel):
    file: str

class ApiOutput(BaseModel):
    response: str

def add_message(history: list, message: dict):
    for x in message["files"]:
        history.append({"role": "user", "content": {"path": x}})
    if message["text"] is not None:
        history.append({"role": "user", "content": message["text"]})
    return history, gr.MultimodalTextbox(value=None, interactive=False)

def route_to_api(files: list, messages: list):
    if len(files) > 0 and len(messages) >= 0:
        fl = files[0]
        response = rq.post("http://localhost:6500/notes", json=NotesInput(file=fl).model_dump())
        return response.json()["response"]
    elif len(files) == 0 and len(messages) > 0:
        response = rq.post("http://localhost:6500/chat", json=ChatInput(message=messages[0]).model_dump())
        return response.json()["response"]
    else:
        return "Please provide an input!"

def bot(history: list):
    messages = [history[i] for i in range(len(history)-1, -1, -1)]
    sliced_messages = []
    for message in messages:
        if message["role"] == "assistant":
            break
        else:
            sliced_messages.append(message)
    files_only = [d["content"][0] for d in sliced_messages if type(d["content"]) == tuple]
    messages_only = [d["content"] for d in sliced_messages if type(d["content"]) == str]
    response = route_to_api(files=files_only, messages=messages_only)
    history.append({"role": "assistant", "content": ""})
    for character in response:
        history[-1]["content"] += character
        time.sleep(0.001)
        yield history

with gr.Blocks(theme=gr.themes.Soft(), title="Pdf2Notes") as demo:
    title = gr.HTML("<h1 align='center'>Pdf2Notes</h1>\n<h2 align='center'>Convert PDF into Notes in seconds</h2>")
    chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, type="messages", min_height=700, min_width=700, label="Pdf2Notes Chat", show_copy_all_button=True)

    chat_input = gr.MultimodalTextbox(
        interactive=True,
        file_count="single",
        file_types=[".pdf",".PDF", ".docx", ".doc", ".DOCX", ".DOC", ".xlsx", ".csv", ".XSLX", ".CSV", ".pptx", ".PPTX"],
        placeholder="Enter message or upload file...",
        show_label=False,
        sources=["upload"],
    )

    chat_msg = chat_input.submit(
        add_message, [chatbot, chat_input], [chatbot, chat_input]
    )
    bot_msg = chat_msg.then(bot, chatbot, chatbot, api_name="bot_response")
    bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])

app = FastAPI(default_response_class=ORJSONResponse)
message_history = ChatHistory(connection=connection)
username = str(uuid.uuid4())

@app.post("/chat")
async def chat(inpt: ChatInput) -> ApiOutput:
    memory = message_history.get(username=username)
    if len(memory) == 0:
        response = await chat_w_memory([{"role": "system", "content": "You are a notes writing assistant. You are open to discussion based on the notes you took, modifying them based on user input. Please, dismiss every request which does not concern note taking or note modifications."}, {"role": "user", "content": inpt.message}])
        message_history.update(username=username, content= "You are a notes writing assistant. You are open to discussion based on the notes you took, modifying them based on user input. Please, dismiss every request which does not concern note taking or note modifications.", role="system")
        message_history.update(username=username, content=inpt.message, role="user")
        message_history.update(username=username, content=response, role="assistant")
    else:
        memory.append({"role": "user", "content": inpt.message})
        response = await chat_w_memory(memory)
        message_history.update(username=username, content=inpt.message, role="user")
        message_history.update(username=username, content=response, role="assistant")
    return ApiOutput(response=response)

@app.post("/notes")
async def notes(inpt: NotesInput) -> ApiOutput:
    fl = inpt.file
    parsed_file = await parse_pdf(fl)
    print("Parsed file!")
    extracted_notes = await generate_notes(parsed_file)
    print("Generated notes!")
    messages = message_history.get(username=username)
    if len(messages) == 0:
        message_history.update(username=username, content= "You are a notes writing assistant. You are open to discussion based on the notes you took, modifying them based on user input. Please, dismiss every request which does not concern note taking or note modifications.", role="system")
        message_history.update(username=username, content=f"Can you extract notes form this text?\n\n'''\n{parsed_file}\n'''", role="user") 
        message_history.update(username=username, content=extracted_notes, role="assistant") 
    else:
        message_history.update(username=username, content=f"Can you extract notes form this file?\n\n[attached file: '{fl}']", role="user") 
        message_history.update(username=username, content=extracted_notes, role="assistant") 
    return ApiOutput(response=extracted_notes)

app = gr.mount_gradio_app(app, demo, path="/app")