import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
import uuid
from datetime import datetime

# Tool imports
from tools.schedule import get_user_schedule
from tools.restopolis import get_canteen_menu
from tools.affluences import get_available_activities, book_resource
from tools.events import get_upcoming_events, get_event_details
from tools.health import get_mental_health_specialists
from tools.mobility import get_transit_route

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
    get_available_activities,
    book_resource,
    get_upcoming_events,
    get_event_details,
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
    
    if session_id not in conversations:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")
        
        system_msg = SystemMessage(content=(
            "You are an AI assistant for university students at uni.lu. "
            "You help students with schedules, answering questions about university life, accommodation, "
            "finding places to eat via Restopolis, booking sports or library rooms via Affluences, "
            "finding events, finding mental health consultants, and building transit routes via Mobiliteit. "
            "Always use your tools to provide actual, helpful data. If you register or book something, confirm it. "
            "CRITICAL REQUIREMENT: You must always reply in the exact same language that the user used to ask the question. "
            "If the user asks about events, parties, or activities, you must use the get_upcoming_events tool. "
            "If the user asks about sport, dance or other sport related activities, you must use the get_available_activities tool. "
            "If the user asks about classes, schedule, courses you must use the get_user_schedule tool."
            f"CRITICAL TIMING INFO: Today is {current_day}, {current_date}. If the user does not specify a date, ALWAYS assume they mean today."
        ))
        conversations[session_id] = [system_msg]
        
    lc_messages = conversations[session_id]
    lc_messages.append(HumanMessage(content=req.message))


    # Agent Loop
    response = await llm_with_tools.ainvoke(lc_messages)
    print(response.content)

    while response.tool_calls:
        # --- PRINT CHAIN OF THOUGHT ---
        # This captures the LLM's reasoning/decision to use tools
        print(f"\n[AI Thought]: {response.content}")
        for tc in response.tool_calls:
            print(f"[Action]: Calling tool '{tc['name']}' with args: {tc['args']}")
        # ------------------------------

        lc_messages.append(response)
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id = tc["id"]

            tool_mapping = {t.name: t for t in tools}
            if tool_name in tool_mapping:
                try:
                    result = tool_mapping[tool_name].invoke(tool_args)
                    # Print the result from the "real world"
                    print(f"[Observation]: {result}")
                    lc_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
                except Exception as e:
                    lc_messages.append(ToolMessage(content=f"Error executing {tool_name}: {e}", tool_call_id=tool_id))
            else:
                lc_messages.append(ToolMessage(content=f"Tool {tool_name} not found.", tool_call_id=tool_id))

        # Invoke LLM again with the tool outputs
        response = await llm_with_tools.ainvoke(lc_messages)

    lc_messages.append(response)

    return {
        "role": "assistant",
        "content": response.content
    }


if __name__ == "__main__":
    # Use the string "main:app" for reload to work correctly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)