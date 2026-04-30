import json

from backend.parcers.restopolis import scrape_all_campus_menus

full_menu_data = scrape_all_campus_menus("2026-04-27")

# Save to file
with open('data/campus_menus.json', 'w', encoding='utf-8') as f:
    json.dump(full_menu_data, f, ensure_ascii=False, indent=4)