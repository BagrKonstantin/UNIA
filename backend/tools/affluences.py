from langchain_core.tools import tool

@tool
def get_available_activities(time_slot: str) -> str:
    """
    Find available sport, fitness, or library activities during a specific time_slot (e.g., '11:45 to 14:00').
    Use this to recommend sports when the student has free time.
    """
    return (
        f"Activities found via Affluences for the time {time_slot}:\n"
        "- ID: SPORT-101 | Crossfit session at Belval Campus Gym (12:00 to 13:00)\n"
        "- ID: SPORT-102 | Yoga class at Kirberg Campus (12:30 to 13:30)\n"
        "- ID: LIB-ROOM-1  | Group study room in Luxembourg Learning Centre (Belval Library)\n"
    )

@tool
def book_resource(resource_id: str, time: str) -> str:
    """
    Books a specific resource (gym class, library room) using its ID for the given time.
    Always confirm with the user after successful booking.
    """
    return f"SUCCESS: Successfully booked {resource_id} at {time} under the student's account."
