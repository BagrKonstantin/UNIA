from datetime import datetime

import requests
from bs4 import BeautifulSoup



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
                    "allergens": [allergen for allergen in allergens.split(', ')]
                })

        # Append the last course found
        if items:
            day_data[current_course] = items

        weekly_menu[day_label] = day_data

    return weekly_menu

# Configuration of all campuses and their restaurants
CAMPUS_CONFIG = {
    "belval": {
        "Food House": {"res": "147", "ser": "53"},
        "Food Cafe": {"res": "148", "ser": "154"},
        "Food Lab Restaurant": {"res": "150", "ser": "156"},
        "Food Lab Cafeteria": {"res": "1320", "ser": "2366"},
        "Food Hub": {"res": "1362", "ser": "2410"},
        "Food Lounge Cafeteria": {"res": "1363", "ser": "2411"},
        "Food Zone": {"res": "149", "ser": "155"},
    },
    "kirchberg": {
        "Restaurant Altius": {"res": "164", "ser": "1183"},
        "Brasserie John’s": {"res": "160", "ser": "178"},
    },
    "limpertsberg": {
        "Um Weier Restaurant": {"res": "6", "ser": "59"},
    }
}

URL = "https://ssl.education.lu/eRestauration/CustomerServices/Menu"

def format_date_key(raw_date_str):
    """
    Converts 'lun., 04.05.' to '2026-05-04'
    Note: Assumes current year (2026) as per your prompt context.
    """
    try:
        # Extract the day and month (04.05)
        date_part = raw_date_str.split(',')[1].strip().strip('.')
        # Parse and add the year
        date_obj = datetime.strptime(f"{date_part}.{datetime.now().year}", "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        return raw_date_str

def scrape_all_campus_menus(date):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    date =  date_obj.strftime("%d.%m.%Y")
    master_json = {}

    for campus_name, restaurants in CAMPUS_CONFIG.items():
        master_json[campus_name] = {}

        for rest_name, ids in restaurants.items():
            print(f"Fetching {campus_name} - {rest_name}...")

            cookies = {
                'CustomerServices.Restopolis.SelectedRestaurant': ids['res'],
                'CustomerServices.Restopolis.SelectedService': ids['ser'],
                'CustomerServices.Restopolis.SelectedDate': date
            }

            try:
                response = requests.get(URL, cookies=cookies, timeout=10)
                if response.status_code == 200:
                    # Parse HTML using your existing function
                    weekly_raw = extract_weekly_menu(response.text)

                    # Convert keys to YYYY-MM-DD and nest under Restaurant Name
                    for date_key, menu_data in weekly_raw.items():
                        iso_date = format_date_key(date_key)

                        if iso_date not in master_json[campus_name]:
                            master_json[campus_name][iso_date] = {}

                        master_json[campus_name][iso_date][rest_name] = menu_data
                else:
                    print(f"Failed {rest_name}: {response.status_code}")
            except Exception as e:
                print(f"Error scraping {rest_name}: {e}")

    return master_json
