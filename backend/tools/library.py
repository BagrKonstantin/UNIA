from datetime import timedelta, datetime

import requests
from langchain_core.tools import tool

from backend.parcers.affluences import request_slots, get_available_slots_with_times


def merge_time_slots(data):
    def format_time(t_str):
        return datetime.strptime(t_str, "%H:%M")

    output = []

    for resource in data:
        times = sorted(resource['times'])
        if not times:
            output.append({**resource, 'times': []})
            continue

        merged_times = []
        # Initialize the first interval
        start_time = format_time(times[0])
        current_end = start_time

        for i in range(1, len(times)):
            next_time = format_time(times[i])

            # Check if the next time is exactly 30 minutes after the current end
            if next_time == current_end + timedelta(minutes=30):
                current_end = next_time
            else:
                # Close the current interval and start a new one
                # Adding 30 mins to end time to show the full duration of the last slot
                final_end = current_end + timedelta(minutes=resource['duration'])
                merged_times.append(f"{start_time.strftime('%H:%M')}-{final_end.strftime('%H:%M')}")

                start_time = next_time
                current_end = next_time

        # Append the last remaining interval
        final_end = current_end + timedelta(minutes=resource['duration'])
        merged_times.append(f"{start_time.strftime('%H:%M')}-{final_end.strftime('%H:%M')}")

        # Create a copy of the resource with the new merged times
        new_resource = resource.copy()
        new_resource['times'] = merged_times
        output.append(new_resource)

    return output

def round_down_30(time_str):
    # Convert string to datetime object
    t = datetime.strptime(time_str, "%H:%M")

    # Calculate how many minutes past the last 30-minute mark
    remainder = t.minute % 30

    # Subtract the remainder to round down
    rounded_time = t - timedelta(minutes=remainder)

    return rounded_time.strftime("%H:%M")

def round_up_30(time_str):
    # Convert string to datetime object
    t = datetime.strptime(time_str, "%H:%M")

    # Calculate how many minutes to the next 30-minute mark
    remainder = t.minute % 30

    if remainder == 0:
        return t.strftime("%H:%M")

    # Add the difference to reach the next 30-minute mark
    rounded_time = t + timedelta(minutes=(30 - remainder))

    return rounded_time.strftime("%H:%M")


@tool
def get_available_slots(date, is_group_work: bool) -> str:
    """
    Find available slots in the library for individual or group work for a specific date in 'YYYY-MM-DD' format.
    Returns the list of available slots.
    """
    return merge_time_slots(get_available_slots_with_times(request_slots(date, is_group_work)))

@tool
def book_slot(resource_id: str, date: str, start_time: str, end_time: str) -> str:
    """
    Books a library spot using resource_id, date ('YYYY-MM-DD'), start_time ('HH:MM'), and end_time ('HH:MM').

    Strict Booking Rules:
    30-Minute Alignment: All timestamps must be a multiple of 30 minutes (e.g., :00 or :30).
    Rounding Logic: If a user provides a time that does not align with a 30-minute block, you must round the start_time DOWN to the previous 30-minute mark (e.g., 12:45 becomes 12:30) and round the end_time UP to the next 30-minute mark.
    Duration: The total booking duration must be at least 30 minutes.
    Auto-Selection: If the user does not specify a room or resource_id, identify and book any available suitable slot.
    Confirmation: You must inform the user that their reservation is pending and must be confirmed via the email sent to their inbox.
    Error handling: If you get error while trying tp book a room, tell user the reason and offer solutions if the reason is not technical
    """
    start_time = round_down_30(start_time)
    end_time = round_up_30(end_time)
    print("rounded time:", start_time, end_time)
    response = book_library_slot(resource_id, date, start_time, end_time)
    return response

def book_library_slot(resource_id, date, start_time, end_time):
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
        "user_phone": None,
        "person_count": 1,
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