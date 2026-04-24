from langchain_core.tools import tool

@tool
def get_transit_route(origin: str, destination: str, arrival_time: str = None) -> str:
    """
    Queries Mobiliteit API to build transit routes (bus/train) from origin to destination.
    arrival_time is an optional time they need to be there (e.g., '12:00').
    Always use this when the user needs to travel somewhere.
    """
    # Mocking Mobiliteit routing
    return (
        f"Route from {origin} to {destination} (Mobiliteit):\n"
        "1. Walk 5 mins to nearest bus stop / train station from your location.\n"
        "2. Take Train/Bus line in the direction of your destination.\n"
        "3. Total journey duration: ~35 mins.\n"
        f"For exact live tracking, visit https://www.mobiliteit.lu/en/journey-planner/?from={origin.replace(' ', '+')}&to={destination.replace(' ', '+')}"
    )
