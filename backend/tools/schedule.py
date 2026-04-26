from typing import Optional

import requests
import json
import datetime

from langchain_core.tools import tool



def get_academic_year():
    """Calculates the academic year string based on current date."""
    now = datetime.datetime.now()
    # If we are in September or later, the year starts now.
    # Otherwise, we are in the second half of the previous year's cycle.
    if now.month >= 9:
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"

def format_to_iso_zulu(start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
    return start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"), end_date.strftime("%Y-%m-%dT23:59:59.000Z")

def get_dynamic_request(start_date=None, end_date=None):
    # 1. Load Cookies
    try:
        with open("uni_cookies.json", "r") as f:
            cookies_dict = json.load(f)
    except FileNotFoundError:
        return "Error: Run the cookie extractor first."

    # 2. Generate Dynamic Time Parameters
    # Format: YYYY-MM-DDTHH:MM:SS.000Z
    # now = datetime.datetime.now(datetime.UTC)
    # start_date = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # end_date = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    start_date, end_date = format_to_iso_zulu(start_date, end_date)
    print(start_date, end_date)

    # 3. Construct Dynamic URL
    academic_year = get_academic_year()
    url = f"https://inscription.uni.lu/Inscriptions/Student/api/seances/student/{academic_year}"

    params = {
        "startDate": start_date,
        "endDate": end_date
    }

    # 4. Headers (Same as before)
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Referer": "https://inscription.uni.lu/Inscriptions/Student/GuichetEtudiant/Agenda",
        "X-Correlation-ID": "e3e6f338-b2b0-483e-874e-3281947faee0" # Ideally generate a new UUID here
    }

    # Add the Anti-Forgery token to headers if it exists in cookies
    token = cookies_dict.get("__RequestVerificationToken_L0luc2NyaXB0aW9ucw2")
    if token:
        headers["RequestVerificationToken"] = token

    # 5. Execute
    response = requests.get(url, headers=headers, params=params, cookies=cookies_dict)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Error {response.status_code}: {response.text}"



def get_courses():
    # 1. Load cookies from your JSON file
    with open("uni_cookies.json", "r") as f:
        cookies_dict = json.load(f)

    # 2. Define the URL
    url = "https://inscription.uni.lu/Inscriptions/Student/api/courses/student/2025-2026"

    # 3. Define the headers (excluding the Cookie header, as we pass that separately)
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7",
        "Connection": "keep-alive",
        "Referer": "https://inscription.uni.lu/Inscriptions/Student/GuichetEtudiant/Agenda?start=1777154400000",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "X-Correlation-ID": "166cc21e-0c5e-4171-b562-43575e5eee3d",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    # 4. Execute the request
    try:
        response = requests.get(url, headers=headers, cookies=cookies_dict)

        # Check if the request was successful
        response.raise_for_status()

        # Parse and print the JSON data
        data = response.json()
        return data

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

def map_courses(start_date, end_date):
    course_mapping = get_courses()
    schedule_data = get_dynamic_request(start_date, end_date)


    name_lookup = {item['IdCours']: item['Libelle'] for item in course_mapping}

    # 2. Update the Seances in the first JSON
    for seance in schedule_data["Seances"]:
        course_id = seance.get("IdCours")
        # Add the name if found in lookup, otherwise set as Unknown
        seance["SubjectName"] = name_lookup.get(course_id, "Unknown Course")

    # 3. Output the result
    return schedule_data


def format_schedule(start_date_str, end_date_str):
    data = map_courses(start_date_str, end_date_str)
    print(data)
    # Parse dates
    start_dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_dt = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

    # Combine Seances and Events into one list
    all_items = data.get('Seances', []) + data.get('Events', [])

    # Group items by date
    schedule_map = {}
    for item in all_items:
        # Extract date from ISO string (e.g., '2026-04-27')
        day = datetime.datetime.fromisoformat(item['Start']).date()
        if day not in schedule_map:
            schedule_map[day] = []
        schedule_map[day].append(item)

    # Sort items within each day by start time
    for day in schedule_map:
        schedule_map[day].sort(key=lambda x: x['Start'])

    output = []
    output.append(f"📅 **Schedule**")

    # Iterate through every day in the range
    current_day = start_dt
    while current_day <= end_dt:
        date_header = current_day.strftime("%A, %d %B %Y")
        output.append(f"\n### {date_header}")

        if current_day in schedule_map:
            for item in schedule_map[current_day]:
                start_t = datetime.datetime.fromisoformat(item['Start']).strftime("%H:%M")
                end_t = datetime.datetime.fromisoformat(item['End']).strftime("%H:%M")

                # Determine title (SubjectName for classes, Title for events)
                name = item.get('SubjectName') or item.get('Title', 'Unknown')
                type_label = item.get('Type', 'EV')
                room = item.get('Room', 'N/A')

                # Emoji mapping based on type
                emoji = "📖" # Default
                if type_label == 'CM': emoji = "👨‍🏫"  # Lecture
                if type_label == 'TP': emoji = "💻"  # Practical
                if type_label == 'TD': emoji = "✍️"  # Tutorial
                if type_label == 'EV': emoji = "💡"  # Event/Office Hour

                status = "❌ (CANCELLED)" if item.get('Cancelled') else ""

                line = f"{emoji} **[{start_t} - {end_t}]** {name} ({type_label}) | 📍 {room} {status}"
                output.append(line)
        else:
            output.append("🥳 **No classes today! Party time!**")

        current_day += datetime.timedelta(days=1)

    return "\n".join(output)

def get_adjusted_dates(start_date=None):
    print("ADJUSTING TIME")
    # 1. If start_date is None, use today
    if start_date is None:
        start_date = datetime.datetime.now()

    # 2. If it's Saturday (5) or Sunday (6), move it to Monday
    # .weekday() returns 0-6 (Mon-Sun)
    if start_date.weekday() == 5:  # Saturday
        start_date += datetime.timedelta(days=2)
    elif start_date.weekday() == 6:  # Sunday
        start_date += datetime.timedelta(days=1)

    # 3. Calculate next Friday
    # We find how many days away Friday (4) is.
    # (4 - current_weekday) % 7 gives the days to the NEXT Friday.
    # If today is Friday, this logic returns 7 days from now.
    days_until_friday = (4 - start_date.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7

    end_date = start_date + datetime.timedelta(days=days_until_friday)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

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
