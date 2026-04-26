import requests
from langchain_core.tools import tool
import re
import json
from bs4 import BeautifulSoup

@tool
def get_available_activities(date) -> str:
    """
    Find available sport, fitness activities for a specific date in 'YYYY-MM-DD' format.
    Returns the list of available activities.
    """
    return get_available_events_with_times(request_sport_activities(date))

@tool
def book_resource(resource_id: str) -> str:
    """
    Books a sport, fitness activities with only resource_id that consists of 5 digits.
    Always confirm with the user after successful booking.
    USER HAVE TO CONFIRM RESERVATION VIA EMAIL OR AFFLUENCE APP
    """
    response = register(resource_id)
    return response



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


def register(resource_id):
    # Define the endpoint
    url = f"https://reservation.affluences.com/api/reserve/{resource_id}"

    # Define the headers
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "content-type": "application/json",
        "origin": "https://affluences.com",
        "priority": "u=1, i",
        "referer": "https://affluences.com/",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "x-service-name": "website",
    }

    # Define the payload (data)
    payload = {
        "auth_type": None,
        "email": "konstantin.bagrianskii.001@student.uni.lu",
        "date": "2026-04-27",
        "start_time": "18:30",
        "end_time": "20:30",
        "note": None,
        "user_firstname": "Konstantin",
        "user_lastname": "Bagrianskii",
        "user_phone": None,
        "person_count": 1,
        "custom_fields_inputs": [
            {
                "custom_field_id": 100,
                "input": "Student"
            }
        ]
    }

    # Execute the POST request
    try:
        response = requests.post(url, headers=headers, json=payload)

        # Check if the request was successful
        response.raise_for_status()

        # Print the response from the server
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())

        return response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if response := getattr(e, 'response', None):
            print("Server Error Message:", response.text)

        return response.text

# a = get_available_events_with_times(request_sport_activities("2026-04-27"))
# print(a)
# register(88004)