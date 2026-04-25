from datetime import datetime

import requests
from langchain_core.tools import tool

url = "https://studentparticipation.uni.lu/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}
def request_events():
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open("events.html", "w", encoding="utf-8") as file:
                file.write(response.text)
            return response.text
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error saving file: {e}")

def request_event(url):
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error saving file: {e}")

from bs4 import BeautifulSoup
import json
from collections import defaultdict

def get_events_for_this_month():
    request_events()
    # Load the HTML content
    file_path = 'events.html'
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Use defaultdict to automatically handle creating lists for new date keys
    events_by_date = defaultdict(list)

    # Find all event containers
    event_containers = soup.find_all('div', class_='em-cal-event-content')

    for event in event_containers:
        # Extract Date to use as the Key
        date_tag = event.find('div', class_='em-event-date')
        date_key = date_tag.get_text(strip=True) if date_tag else "Unknown Date"

        # Extract Title
        title_tag = event.find('div', class_='em-event-title')
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Extract Link
        link_tag = title_tag.find('a') if title_tag else None
        link = link_tag['href'] if link_tag else "N/A"

        # Extract Time
        time_tag = event.find('div', class_='em-event-time')
        time = time_tag.get_text(strip=True) if time_tag else "N/A"

        # Extract Location
        location_tag = event.find('div', class_='em-event-location')
        location = location_tag.get_text(strip=True) if location_tag else "N/A"

        # Extract Category
        category_tag = event.find('ul', class_='event-categories')
        category = category_tag.get_text(strip=True) if category_tag else "General"

        # Extract Description snippet
        desc_tag = event.find('div', class_='em-item-desc')
        description = desc_tag.get_text(strip=True) if desc_tag else "N/A"

        day_of_week = "Unknown"
        try:
            if " - " in date_key:
                start_d_str, end_d_str = date_key.split(" - ")
                event_start = datetime.strptime(start_d_str, "%d/%m/%y" if len(start_d_str.split('/')[-1]) == 2 else "%d/%m/%Y")
                event_end = datetime.strptime(end_d_str, "%d/%m/%y" if len(end_d_str.split('/')[-1]) == 2 else "%d/%m/%Y")
                day_of_week = f"{event_start.strftime('%A')} - {event_end.strftime('%A')}"
            else:
                event_start = datetime.strptime(date_key, "%d/%m/%Y")
                day_of_week = event_start.strftime('%A')
        except Exception:
            pass

        # Append event details to the list for this specific date
        events_by_date[date_key].append({
            "title": title,
            "time": time,
            "location": location,
            "category": category,
            "description": description,
            "url": link,
            "day_of_week": day_of_week
        })

    # Convert defaultdict to a standard dict for JSON serialization
    final_json_data = dict(events_by_date)

    # Output the results to a file
    # output_file = 'events_by_date.json'
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(final_json_data, f, indent=4)

    print(f"Successfully grouped events for {len(final_json_data)} unique dates.")
    return final_json_data

def filter_upcoming_events(events_dict, start_date=None, end_date=None):
    print(start_date, end_date)
    # Get the current date (ignoring time for a fair comparison)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    filter_start = today
    if start_date:
        try:
            filter_start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except Exception:
            pass
            
    filter_end = None
    if end_date:
        try:
            filter_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
        except Exception:
            pass

    upcoming_events = {}

    for date_str, events in events_dict.items():
        # Handle Date Ranges (e.g., '13/04/2026 - 24/05/2026')
        if " - " in date_str:
            start_d_str, end_d_str = date_str.split(" - ")
            event_start = datetime.strptime(start_d_str, "%d/%m/%y" if len(start_d_str.split('/')[-1]) == 2 else "%d/%m/%Y")
            event_end = datetime.strptime(end_d_str, "%d/%m/%y" if len(end_d_str.split('/')[-1]) == 2 else "%d/%m/%Y")
        else:
            # Handle Single Dates (e.g., '31/03/2026')
            event_start = datetime.strptime(date_str, "%d/%m/%Y")
            event_end = event_start

        # If the event overlaps with the requested interval [filter_start, filter_end]
        if event_end >= filter_start:
            if isinstance(filter_end, datetime):
                if event_start <= filter_end:
                    upcoming_events[date_str] = events
            else:
                upcoming_events[date_str] = events

    return upcoming_events

from typing import Optional

@tool
def get_upcoming_events(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Use this tool whenever a student asks about upcoming events, parties, activities, or what to do.
    This fetches the latest events from studentparticipation.uni.lu.
    You can specify `start_date` and `end_date` in `YYYY-MM-DD` format to filter events.
    For example, if the user asks for events "next week", calculate the exact start and end dates based on today's date and pass them.
    If the user asks for a specific day, pass that day as both `start_date` and `end_date`.
    """
    import json
    return json.dumps(filter_upcoming_events(get_events_for_this_month(), start_date, end_date))





def parse_event_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract Title from the <h1> with entry-title class
    title = soup.find('h1', class_='entry-title').get_text(strip=True)

    # Extract Date and Time from the em-event-info div
    # In this file, date and time are inside <li> tags within em-event-info
    event_info = soup.find('div', class_='em-event-info')
    date = "Not found"
    time = "Not found"
    if event_info:
        list_items = event_info.find_all('li')
        for item in list_items:
            text = item.get_text(strip=True)
            if "Date:" in text:
                date = text.replace("Date:", "").strip()
            elif "Time:" in text:
                time = text.replace("Time:", "").strip()

    # Extract Location from the em-location-data div
    location_div = soup.find('div', class_='em-location-data')
    location = location_div.get_text(strip=True) if location_div else "Not found"

    # Extract Full Description (usually in the entry-content div)
    description_div = soup.find('div', class_='entry-content')
    description = description_div.get_text(separator='\n', strip=True) if description_div else "Not found"

    return {
        "title": title,
        "date": date,
        "time": time,
        "location": location,
        "description": description
    }

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
