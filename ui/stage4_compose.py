import os
import gradio as gr
from engine.project_manager import load_json
from engine.composer import compose_final_video

projects_dir = "projects"

def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]

def compose(project_name):
    if not project_name:
        return "No project selected"
    project_path = os.path.join(projects_dir, project_name)
    data_path = os.path.join(project_path, "processed.json")
    if not os.path.isfile(data_path):
        data_path = os.path.join(project_path, "input.json")

    data = load_json(data_path)
    output_path = os.path.join(project_path, "final", "output.mp4")
    compose_final_video(data, project_path, output_path)
    return f"Final video created at: {output_path}"

def build_stage4_ui():
    project_selector3 = gr.Dropdown(label="Select Project", choices=get_project_choices())
    compose_btn = gr.Button("Compose Final Video")
    compose_output = gr.Textbox(label="Compose Status")

    compose_btn.click(
        compose,
        inputs=[project_selector3],
        outputs=[compose_output]
    )
