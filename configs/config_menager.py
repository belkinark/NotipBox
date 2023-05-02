import json

def message_get(field_name: str):
    with open("configs/messages.json", encoding="utf-8") as filename:
        file_json = json.load(filename)
        if field_name in file_json:
            return file_json[field_name]
        return '%not found%'

def config_get(field_name: str):
    with open("configs/config.json", encoding="utf-8") as filename:
        file_json = json.load(filename)
        if field_name in file_json:
            return file_json[field_name]
        return '%not found%'
