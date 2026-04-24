from langchain_core.tools import tool

@tool
def get_canteen_menu(location: str, date: str) -> str:
    """
    Get the menu for a campus canteen (e.g. food in 'Belval', 'Kirchberg', 'Limpertsberg') for a specific date.
    Returns the list of available meals, including steak, vegetarian options, etc.
    """
    # Mocked data from Restopolis for the hackathon
    if 'belval' in location.lower():
        return (
            f"Menu at Restopolis Belval (FoodHouse) on {date}:\n"
            "- Meal 1: Grilled Steak with French Fries and Salad (5.50 EUR for students)\n"
            "- Meal 2: Vegetarian Lasagna with Garlic Bread (4.50 EUR for students)\n"
            "- Food Truck: Burgers and Wraps available outside from 11:30 to 14:00."
        )
    return (
        f"Menu at Restopolis {location} on {date}:\n"
        "- Standard Student Meal: Chicken Breast with Rice\n"
        "- Vegetarian Option: Tofu Curry\n"
        "- Dessert: Apple Tart"
    )
