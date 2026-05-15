import json


def get_workshops():
    with open('data/workshps.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    return json_data