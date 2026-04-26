from langchain_core.tools import tool
from bs4 import BeautifulSoup
import json
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

url = "https://ssl.education.lu/eRestauration/CustomerServices/Menu/BtnChangeRestaurant?pRestaurantSelection=150"
cookies = {
    # 'CustomerServices.Restopolis.SelectedRestaurant': '150',
}
def request_weekly_menu():
    try:
        response = requests.get(url, cookies=cookies)

        if response.status_code == 200:
            # Save the HTML content to a file named 'menu.html'
            # with open("restopolis_menu.html", "w", encoding="utf-8") as file:
            #     file.write(response.text)
            return response.text
        else:
            print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Error saving file: {e}")


def extract_weekly_menu(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Map the days of the week from the date-selector
    days = []
    date_selector = soup.find('div', id='date-selector')
    if date_selector:
        day_links = date_selector.find_all('a', class_='day')
        for link in day_links:
            days.append(link.get_text(strip=True))

    # 2. Extract menu data from each slider section
    weekly_menu = {}
    slider_sections = soup.select('.menu-slider > div')

    for idx, section in enumerate(slider_sections):
        day_label = days[idx] if idx < len(days) else f"Day {idx + 1}"
        day_data = {}

        formulae = section.find('div', class_='formulaeContainer')
        if not formulae:
            continue

        current_course = "Unknown"
        items = []

        # Find all elements to iterate through them sequentially
        elements = formulae.find_all(['div', 'span'])

        for i, element in enumerate(elements):
            classes = element.get('class', [])

            # If it's a course name (e.g., Entrée, Végétarien)
            if 'course-name' in classes:
                if items:
                    day_data[current_course] = items
                current_course = element.get_text(strip=True)
                items = []

            # If it's a product name
            elif 'product-name' in classes:
                product_name = element.get_text(strip=True)
                allergens = ""

                # Look ahead to see if the next element is the allergens span
                if i + 1 < len(elements):
                    next_el = elements[i + 1]
                    if 'product-allergens' in next_el.get('class', []):
                        allergens = next_el.get_text(strip=True)

                # Store as a dictionary to include both name and allergens
                items.append({
                    "name": product_name,
                    "allergens": allergens
                })

        # Append the last course found
        if items:
            day_data[current_course] = items

        weekly_menu[day_label] = day_data

    return weekly_menu



def get_today_menu(today):
    weekly_menu = extract_weekly_menu(request_weekly_menu())
    # today = datetime.today().strftime('%d.%m')
    today = "24.04"
    for day in weekly_menu.keys():
        if today in day:
            return weekly_menu[day]




@tool
def get_canteen_menu(location: str = "belval", date: str = datetime.today().strftime('%d.%m')) -> str:
    """
    Get the menu for a campus canteen (e.g. food in 'Belval', 'Kirchberg', 'Limpertsberg') for a specific date in '%d.%m' format.
    Returns the list of available meals.
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
    ALLERGEN POLICY: DO NOT mention allergens in your response if the user didn't ask about them. 
    If the user states they have an allergy, you MUST use the returned allergens string and match their allergies with this allergen dictionary: 

    Then completely filter out and DO NOT mention meals that the user cannot eat.
    """
    # Mocked data from Restopolis for the hackathon
    if 'belval' in location.lower():
        return str(get_today_menu(date))
    raise ValueError(f"Invalid location: {location}")
    return (
        f"Menu at Restopolis {location} on {date}:\n"
        "- Standard Student Meal: Chicken Breast with Rice\n"
        "- Vegetarian Option: Tofu Curry\n"
        "- Dessert: Apple Tart"
    )