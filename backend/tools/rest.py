from bs4 import BeautifulSoup
import json


def extract_weekly_menu(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # 1. Map the days of the week from the date-selector
    # These usually correspond to the order of the sliders
    days = []
    date_selector = soup.find('div', id='date-selector')
    if date_selector:
        # Finding all 'day' links to get names like "lun.", "mar.", etc.
        day_links = date_selector.find_all('a', class_='day')
        for link in day_links:
            days.append(link.get_text(strip=True))

    # 2. Extract menu data from each slider section
    # Each day is a top-level <div> inside the .menu-slider
    weekly_menu = {}
    slider_sections = soup.select('.menu-slider > div')

    for idx, section in enumerate(slider_sections):
        # Match section to day (handle index safety)
        day_label = days[idx] if idx < len(days) else f"Day {idx + 1}"
        day_data = {}

        # We only care about the formula/daily items (formulaeContainer)
        formulae = section.find('div', class_='formulaeContainer')
        if not formulae:
            continue

        current_course = "Unknown"
        items = []

        # Iterate through elements to group items by course
        for element in formulae.find_all(['div', 'span']):
            classes = element.get('class', [])

            # If it's a course name (e.g., Entrée, Végétarien)
            if 'course-name' in classes:
                # Save previous course if it had items
                if items:
                    day_data[current_course] = items

                current_course = element.get_text(strip=True)
                items = []

            # If it's a product name
            elif 'product-name' in classes:
                items.append(element.get_text(strip=True))

        # Append the last course found
        if items:
            day_data[current_course] = items

        weekly_menu[day_label] = day_data

    return weekly_menu


# Usage
file_name = 'restopolis_menu.html'
menu_result = extract_weekly_menu(file_name)

# Display as JSON
print(json.dumps(menu_result, indent=4, ensure_ascii=False))