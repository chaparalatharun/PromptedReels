import os
import gradio as gr
from engine.project_manager import create_project, save_json
from engine.text_parser import split_script_to_chunks

projects_dir = "projects"

def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]

def create_fn(name, theme, script):
    path = create_project(name)
    chunks = split_script_to_chunks(script)
    json_data = {
        "title": name,
        "theme": theme,
        "script": [{"text": c} for c in chunks]
    }
    save_json(json_data, os.path.join(path, "input.json"))
    return f"Created project '{name}' with {len(chunks)} chunks."


def build_stage1_ui():
    with gr.Blocks() as demo:
        with gr.Row():
            project_name = gr.Textbox(label="Project Name")
            theme_input = gr.Textbox(label="Video Theme")
        script_input = gr.Textbox(label="Paste Script", lines=10)
        create_btn = gr.Button("Create Project")
        output = gr.Textbox(label="Status")

        create_btn.click(
            create_fn,
            inputs=[project_name, theme_input, script_input],
            outputs=[output]
        )
    return demo



