import requests
import json
import re
from bs4 import BeautifulSoup
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def request_workshops():
    try:
        url = f"https://www.uni.lu/life-en/classes-workshops/"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error saving file: {e}")



def parse_uni_workshops():

    soup = BeautifulSoup(request_workshops(), 'html.parser')

    # Mapping expected output categories to keywords found in the HTML titles
    # This handles "Arts & culture", "Sport", and "Wellbeing"
    category_map = {
        "arts & culture": "arts and culture",
        "sport": "sport",
        "wellbeing": "wellbeing"
    }

    results = {
        "arts and culture": [],
        "sport": [],
        "wellbeing": []
    }

    # The HTML groups events into accordion items
    sections = soup.find_all('div', class_='accordion__item')

    for section in sections:
        # Get the title of the section (e.g., "Arts & culture")
        title_tag = section.find('span', class_='accordion__title')
        if not title_tag:
            continue

        section_title = title_tag.get_text(strip=True).lower()

        # Determine which of our 3 categories this section belongs to
        current_cat = None
        for key, val in category_map.items():
            if key in section_title:
                current_cat = val
                break

        if current_cat:
            # Find all event cards in this section
            cards = section.find_all('div', class_='ulux-card')

            for card in cards:
                # 1. Parse Name
                name_tag = card.find('h3', class_='ulux-card__title')
                name = name_tag.get_text(strip=True) if name_tag else "N/A"

                # 2. Parse Description (Usually contains time/location)
                desc_tag = card.find('div', class_='card__function')
                description = desc_tag.get_text(strip=True, separator=" ") if desc_tag else ""

                # 3. Parse Link
                link_tag = card.find('a', href=True)
                link = link_tag['href'] if link_tag else ""

                results[current_cat].append({
                    "name": name,
                    "description": description,
                    "link": link
                })
    print(f"Successfully collected workshops")

    return results
