from langchain_core.tools import tool

@tool
def get_mental_health_specialists(symptom_or_need: str) -> str:
    """
    Finds mental health specialists or counseling options via go.karaconnect.com/p/unilu.
    Use this when the user says they feel bad, anxious, stressed, or need to talk.
    """
    return (
        "Mental Health Counseling available via Uni.lu (KaraConnect):\n"
        "- Psychologist Anna Smith (Available for Online Consultation Tomorrow at 14:00) | Focus: Stress Management, Anxiety\n"
        "- Counselor John Doe (Available for In-Person at Belval on Thursday at 10:00) | Focus: Generic Student Counseling\n"
        "To book, the student should visit https://go.karaconnect.com/p/unilu."
    )
