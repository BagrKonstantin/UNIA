import requests
from bs4 import BeautifulSoup
import re
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}
def request_sport_activities(data):
    try:
        url = f"https://affluences.com/en/sites/universite-du-luxembourg-1/student-services/reservation?type=3018&date={data}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open("sport.html", "w", encoding="utf-8") as file:
                file.write(response.text)
            return response.text
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error saving file: {e}")




def get_available_events_with_times(html):
    """
    Extracts events marked as 'available' along with their specific start times.
    """
    soup = BeautifulSoup(html, 'html.parser')
    available_events = []

    scripts = soup.find_all('script')

    for script in scripts:
        if not script.string or '"resource_id"' not in script.string:
            continue

        try:
            # Extract the JSON block
            match = re.search(r'(\{.*\})', script.string, re.DOTALL)
            if not match:
                continue

            data = json.loads(match.group(1))

            def find_available_resources(obj):
                if isinstance(obj, dict):
                    # Check if this is a resource with availability
                    if 'resource_id' in obj and obj.get('slots_state') == 'available':
                        # Extract the list of available start times
                        start_times = []
                        if 'hours' in obj and isinstance(obj['hours'], list):
                            for slot in obj['hours']:
                                if slot.get('state') == 'available':
                                    start_times.append(slot.get('hour'))

                        if start_times:
                            available_events.append({
                                'resource_id': obj.get('resource_id'),
                                'name': obj.get('resource_name'),
                                'times': start_times
                            })

                    # Search deeper in the dictionary
                    for value in obj.values():
                        find_available_resources(value)
                elif isinstance(obj, list):
                    for item in obj:
                        find_available_resources(item)

            find_available_resources(data)
        except (json.JSONDecodeError, Exception):
            continue

    # De-duplicate results by ID
    unique_events = {}
    for e in available_events:
        unique_events[e['resource_id']] = e

    return list(unique_events.values())