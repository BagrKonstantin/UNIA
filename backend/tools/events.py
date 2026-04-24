from langchain_core.tools import tool

@tool
def get_upcoming_events() -> str:
    """
    Get a list of upcoming student events or parties from studentparticipation.uni.lu when a student is bored or looking for activities.
    """
    return (
        "Upcoming Events at Uni.lu:\n"
        "- ESN Welcome Party (Tomorrow 20:00 at Rives de Clausen, Luxembourg City)\n"
        "- Hackathon Networking Event (Today 18:00 at Maison du Savoir, Belval)\n"
        "- Board Game Night by Student Lounge (Friday 19:00 at Student Lounge Belval)\n"
    )
