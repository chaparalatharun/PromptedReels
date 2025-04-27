import os
import json
from engine.text_parser import split_script_to_chunks, split_scene_to_chunks


def parse_script_line(line):
    ret = {"character": "",
            "picture": "random",
           }
    if ":" in line:
        name, line = line.split(":", 1)
        ret["character"] = name.strip()
    ret["text"] = line
    return ret

def parse_scene_line(line):
    ret = {}
    if len(line.split(";;;")) > 1:
        scene, move_prompt = line.split(";;;")
        ret["scene"] = scene
        ret["move_prompt"] = move_prompt
    else:
        ret["scene"] = line
    return ret




def create_project(name, theme, script,scene):
    path = create_fn(name)
    script_chunks = split_script_to_chunks(script)
    scene_chunks = split_scene_to_chunks(scene)
    script_data = [parse_script_line(c) for c in script_chunks]
    scene_data =  [parse_scene_line(c) for c in scene_chunks]

    json_data = {
        "title": name,
        "theme": theme,
        "script": script_data,
        "scene" : scene_data
    }
    save_json(json_data, os.path.join(path, "input.json"))
    return f"Created project '{name}' with {len(script_data)} script_data, with {len(scene_data)} scene_data."

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