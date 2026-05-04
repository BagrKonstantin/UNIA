import requests
from langchain_core.tools import tool

from backend.parcers.affluences import request_sport_activities, get_available_events_with_times


@tool
def get_available_activities(date) -> str:
    """
    Find available sport, fitness activities for a specific date in 'YYYY-MM-DD' format.
    Returns the list of available activities.
    """
    return get_available_events_with_times(request_sport_activities(date))

@tool
def book_resource(resource_id: str, date: str, start_time: str, end_time: str) -> str:
    """
    Books a sport, fitness activities with resource_id, date in 'YYYY-MM-DD' format and start and end time in 'HH:MM' format.
    Always confirm with the user after successful booking.
    USER HAVE TO CONFIRM RESERVATION VIA EMAIL OR AFFLUENCE APP
    """
    response = register(resource_id, date, start_time, end_time)
    return response




def register(resource_id, date, start_time, end_time):
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
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
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