from typing import Optional
from langchain_core.tools import tool

from backend.parcers.schedule import get_adjusted_dates, format_schedule


@tool
def get_user_schedule(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Get the student's existing schedule for an upcoming classes.
    You can specify `start_date` and `end_date` in `YYYY-MM-DD` format to filter classes.
    For example, if the user asks for classes "next week", calculate the exact start and end dates based on today's date and pass them.
    If the user asks for a specific day, pass that day as both `start_date` and `end_date`.
    """
    if start_date is None:
        start_date, end_date = get_adjusted_dates(start_date)
    print(f"Getting user's schedule... for {start_date} and {end_date}")
    try:
        schedule_data = format_schedule(start_date, end_date)
    except Exception as err:
        print(f"An error occurred: {err}")
        return f"Error during getting user's schedule: {err}"
    return str(schedule_data)
