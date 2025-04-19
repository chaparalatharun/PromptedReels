import os
import json
from engine.text_parser import split_script_to_chunks


def parse_script_line(line):
    if ":" in line:
        name, content = line.split(":", 1)
        return {
            "character": name.strip(),
            "picture": "random",
            "text": content.strip()
        }
    else:
        return {
            "character": "",
            "picture": "random",
            "text": line.strip()
        }

def create_project(name, theme, script):
    path = create_fn(name)
    chunks = split_script_to_chunks(script)
    script_data = [parse_script_line(c) for c in chunks]

    json_data = {
        "title": name,
        "theme": theme,
        "script": script_data
    }
    save_json(json_data, os.path.join(path, "input.json"))
    return f"Created project '{name}' with {len(chunks)} chunks."

def create_fn(name):
    base = os.path.join("projects", name)
    os.makedirs(base, exist_ok=True)
    os.makedirs(os.path.join(base, "audio"), exist_ok=True)
    os.makedirs(os.path.join(base, "video"), exist_ok=True)
    os.makedirs(os.path.join(base, "image"), exist_ok=True)
    os.makedirs(os.path.join(base, "final"), exist_ok=True)
    return base

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)