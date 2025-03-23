from llama_cloud_services import LlamaParse
from llama_index.llms.groq import Groq
import os
from dotenv import load_dotenv
from llama_index.core.schema import TextNode
from llama_index.core.llms import ChatMessage
from typing import List, Dict
from pydantic import BaseModel, Field
import json

load_dotenv()

class Notes(BaseModel):
    title: str = Field(description="Title for the notes")
    notes: str = Field(description="Notes")
    tags: List[str] = Field(description="List of tags describing the main concepts of the notes")

parser = LlamaParse(
    api_key = os.getenv("llamacloud_api_key"),
    result_type="markdown",
    use_vendor_multimodal_model=True,
    vendor_multimodal_model_name="gemini-2.0-flash-001",
)

llm = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("groq_api_key"))
llm_struct = llm.as_structured_llm(Notes)

async def get_text_nodes(json_list: List[dict]):
    text_nodes = []
    for idx, page in enumerate(json_list):
        text_node = TextNode(text=page["md"], metadata={"page": page["page"]})
        text_nodes.append(text_node)
    return text_nodes

async def parse_pdf(pdf_path: str) -> str:
    """A tool useful to parse a PDF document and load its parsed text to the context
    
    Args:
        pdf_path (str): path of the PDF document
    """
    json_objs = await parser.aget_json(pdf_path)
    json_list = json_objs[0]["pages"]
    docs = await get_text_nodes(json_list)
    dicts = [d.dict() for d in docs]
    text = "\n\n---\n\n".join([d["text"] for d in dicts])
    return text

async def generate_notes(text_input: str) -> str:
    messages = [ChatMessage.from_str(content="You are a notes writing assistant. When you are prompted with some text, you should extract notes from it, giving the notes an appropriate title and a list of tags regarding the concepts on which your notes focus", role="system"), ChatMessage.from_str(content=text_input, role="user"), ChatMessage.from_str(content="I see you provided me with a full text: do you want me to extract notes from it", role="assistant"), ChatMessage.from_str(content="Yes, I would like you to extract notes from it. You should extract notes in the following format:\n- A title for the notes\n- The notes themselves\n- A list of tags that captures the main concepts that your notes deal with", role="user")]
    response = await llm_struct.achat(messages=messages)
    json_response = json.loads(response.message.blocks[0].text)
    response = f"# {json_response['title']}\n\n**Tags**: {', '.join(json_response['tags'])}\n\n{json_response['notes']}"
    return response

async def chat_w_memory(message_history: List[Dict[str, str]]) -> str:
    messages = []
    for message in message_history:
        messages.append(ChatMessage.from_str(content=message['content'], role=message['role']))
    response = await llm.achat(messages)
    return response.message.blocks[0].text
