import json
import os
from langchain_core.tools import tool

@tool
def get_workshops(category: str = None) -> str:
    """
    Get general information and weekly schedules about repeating classes and workshops at Uni.lu.
    DO NOT use this tool if the user asks for classes/workshops on a specific day (e.g., "today", "tomorrow", "Friday"). 
    For specific dates, use get_available_activities instead.
    Categories include: 'arts and culture', 'sport', 'wellbeing'.
    If category is provided, returns only workshops of that type.
    Otherwise, returns all workshops.
    Provides name, description, schedule (often in description), and link.
    """

    
    with open('data/workshops.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if category:
        category = category.lower()
        if category in data:
            return json.dumps(data[category], indent=2, ensure_ascii=False)
        else:
            return f"Category '{category}' not found. Available categories: {', '.join(data.keys())}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)
