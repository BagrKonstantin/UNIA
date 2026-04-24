from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
import uuid

# Tool imports
from tools.schedule import get_user_schedule
from tools.restopolis import get_canteen_menu
from tools.affluences import get_available_activities, book_resource
from tools.events import get_upcoming_events
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
llm = ChatOllama(model="gemma-4-26b-a4b-thinking", temperature=0)

tools = [
    get_user_schedule,
    get_canteen_menu,
    get_available_activities,
    book_resource,
    get_upcoming_events,
    get_mental_health_specialists,
    get_transit_route,
]

llm_with_tools = llm.bind_tools(tools)

class ChatRequest(BaseModel):
    messages: list

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    lc_messages = []
    # Persona definition
    lc_messages.append(SystemMessage(content=(
        "You are an AI assistant for university students at uni.lu, participating in a hackathon. "
        "You help students with schedules, answering questions about university life, accommodation, "
        "finding places to eat via Restopolis, booking sports or library rooms via Affluences, "
        "finding events, finding mental health consultants, and building transit routes via Mobiliteit API. "
        "Always use your tools to provide actual, helpful data. If you register or book something, confirm it."
    )))
    
    for m in req.messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "tool":
            lc_messages.append(ToolMessage(content=content, tool_call_id=m.get("id", "")))

    # Agent Loop
    response = await llm_with_tools.ainvoke(lc_messages)
    
    while response.tool_calls:
        lc_messages.append(response)
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id = tc["id"]
            
            tool_mapping = {t.name: t for t in tools}
            if tool_name in tool_mapping:
                try:
                    result = tool_mapping[tool_name].invoke(tool_args)
                    lc_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
                except Exception as e:
                    lc_messages.append(ToolMessage(content=f"Error executing {tool_name}: {e}", tool_call_id=tool_id))
            else:
                lc_messages.append(ToolMessage(content=f"Tool {tool_name} not found.", tool_call_id=tool_id))
        
        # Invoke LLM again with the tool outputs
        response = await llm_with_tools.ainvoke(lc_messages)
        
    return {
        "role": "assistant",
        "content": response.content
    }
