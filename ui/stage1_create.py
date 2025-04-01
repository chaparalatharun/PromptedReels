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

def create_fn(name, script):
    path = create_project(name)
    chunks = split_script_to_chunks(script)
    json_data = {"title": name, "script": [{"text": c} for c in chunks]}
    save_json(json_data, os.path.join(path, "input.json"))
    updated_choices = get_project_choices()
    return (
        f"Created project '{name}' with {len(chunks)} chunks.",
        *(gr.update(choices=updated_choices) for _ in range(3))
    )

def build_stage1_ui():
    with gr.Row():
        project_name = gr.Textbox(label="Project Name")
        script_input = gr.Textbox(label="Paste Script", lines=10)
    create_btn = gr.Button("Create Project")
    output = gr.Textbox(label="Status")

    project_selector_stage2 = gr.Dropdown(
        label="Select Project for Stage 2",
        choices=get_project_choices()
    )
    project_selector_stage3 = gr.Dropdown(
        label="Select Project for Stage 3",
        choices=get_project_choices()
    )
    project_selector_stage4 = gr.Dropdown(
        label="Select Project for Stage 4 (Edit JSON)",
        choices=get_project_choices()
    )

    create_btn.click(
        create_fn,
        inputs=[project_name, script_input],
        outputs=[
            output,
            project_selector_stage2,
            project_selector_stage3,
            project_selector_stage4
        ]
    )
