import requests
import json
from datetime import datetime
from langchain_core.tools import tool

# API configuration (public key from buster.lu open source project)
API_BASE = "https://cdt.hafas.de/opendata/apiserver"
API_KEY = "acf20309-d2af-46ed-b128-dd1b195fbc7d"

def format_duration(duration_str):
    # Hafas duration is often in PT1H20M format or similar
    if not duration_str:
        return "N/A"
    return duration_str.replace("PT", "").replace("H", "h ").replace("M", "m").strip()

def get_stop_id(lat: float, lon: float) -> str:
    """Helper to resolve coordinates to the nearest stop ID (extId)."""
    url = f"{API_BASE}/location.nearbystops"
    params = {
        "accessId": API_KEY,
        "format": "json",
        "originCoordLat": lat,
        "originCoordLong": lon,
        "maxNo": 1
    }
    headers = {
        "User-Agent": "UniLuAssistant/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "identity"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            stops = data.get("stopLocationOrCoordLocation", [])
            if stops and "stopLocation" in stops[0]:
                return stops[0]["stopLocation"]["extId"]
    except Exception:
        pass
    return None

def request_mobilitet(arrival_time: str, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> str:
    # First, try to resolve coordinates to stop IDs as many HAFAS instances prefer them
    origin_id = get_stop_id(origin_lat, origin_lon)
    dest_id = get_stop_id(dest_lat, dest_lon)

    url = f"{API_BASE}/trip"
    params = {
        "accessId": API_KEY,
        "format": "json",
        "searchForArrival": 1,
        "time": arrival_time,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "numF": 3
    }

    if origin_id and dest_id:
        params["originId"] = origin_id
        params["destId"] = dest_id
    else:
        # Fallback to coordinates if IDs couldn't be resolved
        params["originCoordLat"] = origin_lat
        params["originCoordLong"] = origin_lon
        params["originCoordName"] = "Start"
        params["destCoordLat"] = dest_lat
        params["destCoordLong"] = dest_lon
        params["destCoordName"] = "Finish"

    headers = {
        "User-Agent": "UniLuAssistant/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "identity"
    }

    try:
        with requests.Session() as session:
            resp = session.get(url, params=params, headers=headers, timeout=15)

        if resp.status_code != 200:
            # If trip endpoint fails, try the newer travelplanner endpoint as a fallback
            fallback_url = "https://travelplanner.mobiliteit.lu/hafas/restproxy/trip"
            resp = session.get(fallback_url, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                return f"Error: The Mobiliteit API returned status code {resp.status_code}. It might be temporarily unavailable."

        data = resp.json()
        if "Trip" not in data:
            return "No transit routes found for the given locations and time."

        trips = data["Trip"]
        result = [f"### 🚌 Recommended Routes to arrive by {arrival_time}\n"]

        for i, trip in enumerate(trips[:3]):
            duration = trip.get("duration", "")
            legs = trip.get("LegList", {}).get("Leg", [])
            if not legs: continue

            start_time = legs[0].get("Origin", {}).get("time", "N/A")
            end_time = legs[-1].get("Destination", {}).get("time", "N/A")

            lines = []
            for leg in legs:
                if leg.get("type") == "JNY":
                    line = leg.get("Product", {}).get("name", "").strip()
                    if line: lines.append(line)

            lines_str = " ➔ ".join(lines) if lines else "Walking/Direct"
            result.append(f"**Option {i + 1}**:")
            result.append(f"- **Departure**: {start_time} | **Arrival**: {end_time}")
            result.append(f"- **Duration**: {format_duration(duration)}")
            result.append(f"- **Route**: {lines_str}\n")

        return "\n".join(result)

    except requests.exceptions.ChunkedEncodingError:
        return "The Mobiliteit API is currently having connection issues. Please try again in a moment."
    except Exception as e:
        return f"An error occurred while fetching transit data: {str(e)}"



# a = request_mobilitet("20:00", 49.504, 5.949, 49.626, 6.159)
# print(a)

@tool
def get_transit_route(arrival_time: str, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> str:
    """
    Queries the Mobiliteit.lu API to find public transport routes between two coordinates in Luxembourg.
    
    Args:
        arrival_time: The time you want to arrive at the destination (format: HH:MM, e.g., '09:00').
        origin_lat: Latitude of your starting point.
        origin_lon: Longitude of your starting point.
        dest_lat: Latitude of your destination.
        dest_lon: Longitude of your destination.
    
    Returns:
        A formatted string describing the best transit options.
    """
    return request_mobilitet(arrival_time, origin_lat, origin_lon, dest_lat, dest_lon)




