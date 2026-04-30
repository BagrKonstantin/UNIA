import json

from langchain_core.tools import tool
from bs4 import BeautifulSoup
import requests
from datetime import datetime

allergenes = {
    "1": "Céréales contenant du gluten (Blé, Seigle, Orge, Avoine, Épeautre, Kamut)",
    "2": "Crustacés",
    "3": "Œufs",
    "4": "Poissons",
    "5": "Arachides",
    "6": "Soja",
    "7": "Lait (Lactose)",
    "8": "Fruits à coque (Amandes, Noisettes, Noix, Pistaches, etc.)",
    "9": "Céleri",
    "10": "Moutarde",
    "11": "Graines de sésame",
    "12": "Anhydride sulfureux et sulfites (>10mg/kg)",
    "13": "Lupin",
    "14": "Mollusques"
}


def get_today_menu(campus, date):
    with open('data/campus_menus.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    menu = json_data[campus.lower()][date]
    return menu


@tool
def get_canteen_menu(location: str = "belval", date: str = datetime.today().strftime("%Y-%m-%d")) -> str:
    """
    Get the menu for a campus canteen (e.g. food in 'Belval', 'Kirchberg', 'Limpertsberg') for a specific date in 'YYYY-MM-DD' format.
    Returns the list of available meals.

    ALLERGEN POLICY: DO NOT mention allergens in your response if the user didn't ask about them. 
    If the user states they have an allergy, you MUST use the returned allergens string and match their allergies with this allergen dictionary:

    1: Céréales contenant du gluten (Blé, Seigle, Orge, Avoine, Épeautre, Kamut),
    2: Crustacés,
    3: Œufs,
    4: Poissons,
    5: Arachides,
    6: Soja,
    7: Lait (Lactose),
    8: Fruits à coque (Amandes, Noisettes, Noix, Pistaches, etc.),
    9: Céleri,
    10: Moutarde,
    11: Graines de sésame,
    12: Anhydride sulfureux et sulfites (>10mg/kg),
    13: Lupin,
    14: Mollusques

    Then completely filter out and DO NOT mention meals that the user cannot eat.
    """
    return get_today_menu(location, date)