import json

from langchain_core.tools import tool
from typing import Optional

from backend.parcers.events import request_event, parse_event_data, filter_upcoming_events


def get_events():
    with open('data/events.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    return json_data


@tool
def get_upcoming_events(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Use this tool whenever a student asks about upcoming events, parties, activities, or what to do.
    This fetches the latest events from studentparticipation.uni.lu.
    You can specify `start_date` and `end_date` in `YYYY-MM-DD` format to filter events.
    For example, if the user asks for events "next week", calculate the exact start and end dates based on today's date and pass them.
    If the user asks for a specific day, pass that day as both `start_date` and `end_date`.
    """
    return json.dumps(filter_upcoming_events(get_events(), start_date, end_date))


@tool
def get_event_details(url: str) -> str:
    """
    Get detailed information about a specific event using its URL.
    Use this tool when the user asks for more details (like description or exact location) about an event you listed.
    """
    import json
    html = request_event(url)
    if html:
        return json.dumps(parse_event_data(html))
    return json.dumps({"error": "Event details not found."})
