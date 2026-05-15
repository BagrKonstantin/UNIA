import json
import os
from langchain_core.tools import tool

@tool
def get_workshops(category: str = None) -> str:
    """
    Get information about workshops at Uni.lu.
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
