import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
import uuid
import json
import base64
from datetime import datetime

# Tool imports
from tools.schedule import get_user_schedule
from tools.restopolis import get_canteen_menu, get_information_about_canteens, get_allergens
from tools.affluences import get_available_activities, book_resource
from tools.events import get_upcoming_events, get_event_details
from tools.web_search import search_unilu, deep_search_unilu
from tools.library import get_available_slots, book_slot
from tools.workshops import get_workshops

app = FastAPI(title="Uni.lu Hackathon Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM initialized with the specific Gemma version chosen
llm = ChatOllama(model="gemma4:e4b", temperature=0)

tools = [
    get_user_schedule,
    get_canteen_menu,
    get_information_about_canteens,
    get_allergens,
    get_available_activities,
    book_resource,
    get_upcoming_events,
    get_event_details,
    search_unilu,
    deep_search_unilu,
    get_available_slots,
    book_slot,
    get_workshops,
    # get_mental_health_specialists,
    # get_transit_route,
]

llm_with_tools = llm.bind_tools(tools)

# In-memory storage for conversations
conversations: dict[str, list] = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id
    print(session_id)
    
    if session_id not in conversations:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")
        
        system_msg = SystemMessage(content=(
f"""
Role:
You are the official Uni.lu Student Concierge. Your mission is to provide seamless, real-time support for life at the University of Luxembourg, spanning academics, and well-being.

Operational Guidelines:
Language Matching: Detect the user’s input language and respond exclusively in that language. This is a strict requirement for all interactions.
Temporal Context: Today is {current_day}, {current_date}. Unless a different date is explicitly mentioned, always execute tool calls and provide answers relative to today.
Action Confirmation: Whenever a tool successfully registers a booking or completes an action, provide a clear, concise confirmation message.
Data Integrity: Do not hypothesize. If a tool is available, you must use it to fetch live data rather than relying on internal knowledge.

Tool Trigger Logic:
Dining: For queries regarding canteens, menus, or daily specials, use get_canteen_menu.
Campus Life: For events, parties, or social gatherings, use get_upcoming_events.
Wellness & Athletics: For sports, dance classes, or physical activities *with real-time availability*, use get_available_activities.
Workshops & Culture: For general information about workshops in arts and culture, sport, or wellbeing, including their weekly schedules and descriptions, use get_workshops.
Academics: For personalized course schedules, class locations, or timetables, use get_user_schedule.
General Inquiry: For broad questions about campus facilities or general uni life, use search_unilu.
Procedural Precision: For complex queries involving application deadlines, legal requirements, or specific administrative procedures, use deep_search_unilu to parse detailed web content.
"""
        ))
        conversations[session_id] = [system_msg]
        
    lc_messages = conversations[session_id]
    lc_messages.append(HumanMessage(content=req.message))


    async def event_stream():
        nonlocal lc_messages
        
        while True:
            chunks = []
            is_tool_call = False
            
            async for chunk in llm_with_tools.astream(lc_messages):
                chunks.append(chunk)
                if chunk.tool_call_chunks:
                    is_tool_call = True
                
                if not is_tool_call and chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
                    
            if not chunks:
                break
                
            # Combine chunks into a single AIMessage
            final_message = chunks[0]
            for c in chunks[1:]:
                final_message += c
                
            if final_message.tool_calls:
                lc_messages.append(final_message)
                
                # Notify frontend about tool execution
                tool_descriptions = {
                    "get_canteen_menu": "Looking up the menu",
                    "get_information_about_canteens": "Checking canteen schedule",
                    "get_allergens": "Getting allergens",
                    "get_upcoming_events": "Searching for events",
                    "get_event_details": "Getting event details",
                    "get_available_activities": "Searching for activities",
                    "book_resource": "Booking spot",
                    "get_user_schedule": "Getting your schedule",
                    "search_unilu": "Searching uni.lu website",
                    "deep_search_unilu": "Deeply scanning uni.lu for specific details",
                    "get_mental_health_specialists": "Finding health specialists",
                    "get_transit_route": "Finding transit routes",
                    "get_available_slots": "Finding available slots",
                    "book_slot": "Booking slot",
                    "get_workshops": "Getting workshop information",
                }
                for tc in final_message.tool_calls:
                    desc = tool_descriptions.get(tc['name'], f"Using tool {tc['name']}")
                    yield f"data: {json.dumps({'tool_call': desc})}\n\n"
                    print(f"\\n[AI Thought]: Calling tool '{tc['name']}' with args: {tc['args']}")
                    
                for tc in final_message.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    tool_id = tc["id"]
        
                    tool_mapping = {t.name: t for t in tools}
                    if tool_name in tool_mapping:
                        try:
                            result = tool_mapping[tool_name].invoke(tool_args)
                            print(f"[Observation]: {result}")
                            lc_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
                        except Exception as e:
                            lc_messages.append(ToolMessage(content=f"Error executing {tool_name}: {e}", tool_call_id=tool_id))
                    else:
                        lc_messages.append(ToolMessage(content=f"Tool {tool_name} not found.", tool_call_id=tool_id))
                        
                # Loop continues to invoke LLM with tool outputs
                continue
            else:
                # No tool calls, conversation turn is done
                lc_messages.append(final_message)
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    mime_type = "audio/wav"

    system_msg = SystemMessage(content=(
"""## Role
You are a high-precision transcription correction engine specializing in University of Luxembourg (Uni.lu) terminology.

## Objective
Convert raw, potentially noisy speech-to-text input into a clean, grammatically correct plain-text transcript. Your priority is to correctly identify and spell university-specific entities.

## Uni.lu Lexicon (Priority Correction)
- Campuses: Belval, Kirchberg, Limpertsberg.
- Buildings: Maison du Savoir (MSA), Maison des Arts et des Étudiants (MAE), Maison du Nombre, Maison de l'Innovation, Weicker Building.
- Facilities: LLC (Luxembourg Learning Centre), "cube" (study room), Restopolis (canteens), SEVE, Guichet Étudiant.
- Apps/Tech: Affluences (booking), Moodle, ServiceNow.
- Academic Units: FSTM, FDEF, FHSE, SnT, LCSB, C2DH.

## Strict Output Rules
1. Output ONLY the corrected transcript.
2. Do NOT include Markdown formatting (no bolding, no headers).
3. Do NOT add conversational responses, acknowledgments, or "Here is the transcript."
4. Ensure proper capitalization of all University entities.
5. Maintain the original language of the speaker (English, French, or German) but standardize the technical Uni.lu terms.
6. If a term is ambiguous, choose the one that fits the University context (e.g., if you hear "bell val," output "Belval").
"""
    ))
    
    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{audio_b64}"
                }
            }
        ]
    )
    
    response = llm.invoke([system_msg, message])
    return {"text": response.content}

if __name__ == "__main__":
    # Use the string "main:app" for reload to work correctly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)