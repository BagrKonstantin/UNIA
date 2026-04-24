from langchain_core.tools import tool

@tool
def get_user_schedule(date: str) -> str:
    """
    Get the student's existing schedule for a given date.
    Returns times when the student has classes and when they are free.
    date format should ideally be 'YYYY-MM-DD' or 'today'.
    """
    # Hardcoded dummy schedule for hackathon purposes
    return (
        f"Schedule for {date}:\n"
        "- 08:30 to 10:00: Mathematics Lecture (Belval Campus, MSA 3.520)\n"
        "- 10:15 to 11:45: Computer Science Lab (Belval Campus, MNO 1.040)\n"
        "- 11:45 to 14:00: FREE TIME\n"
        "- 14:00 to 15:30: Software Engineering (Belval Campus, MSA 4.100)\n"
        "- 15:30 onwards: FREE TIME"
    )
