import os
import gradio as gr

from engine.MediaProcessor import MediaProcessor
from engine.project_manager import load_json, save_json

projects_dir = "projects"

def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]

def generate_media(project_name, reGen_AU_checkbox, reGen_IM_checkbox,reGen_VI_checkbox, video_title):
    if not project_name:
        return "No project selected"

    processor = MediaProcessor(
        project_name=project_name,
        projects_dir=projects_dir,
        reGen_audio=reGen_AU_checkbox,
        reGen_video=reGen_VI_checkbox,
        reGen_image=reGen_IM_checkbox,
        theme=video_title
    )

    processor.process_all()
    return f"✅ Media generated for project: {project_name} (Audio: {reGen_AU_checkbox}, Video: {reGen_VI_checkbox})"



def autofill_title(project_name):
    # 如果传入的是列表，取第一个元素
    if isinstance(project_name, list):
        project_name = project_name[0]
    if not project_name:
        return gr.update(value="")
    input_path = os.path.join(projects_dir, project_name, "input.json")
    if os.path.exists(input_path):
        data = load_json(input_path)
        title = data.get("theme", "")
        return gr.update(value=title)
    return gr.update(value="")


def refresh_dropdown_and_reset():
    choices = get_project_choices()
    return gr.update(choices=choices, value=None)



def build_stage2_ui():
    with gr.Blocks() as demo:
        project_selector2 = gr.Dropdown(label="Select Project", choices=get_project_choices(), interactive=True)
        refresh_btn = gr.Button("🔄 Refresh Project List")
        reGen_AU_checkbox = gr.Checkbox(label="Regenerate Media (audio)", value=True)
        reGen_IM_checkbox = gr.Checkbox(label="Regenerate Media (Image)", value=True)
        reGen_VI_checkbox = gr.Checkbox(label="Regenerate Media (video)", value=True)

        video_title = gr.Textbox(label="Video Title", interactive=True)
        generate_btn = gr.Button("Generate Audio & Video")
        gen_status = gr.Textbox(label="Generation Status")

        refresh_btn.click(
            fn=refresh_dropdown_and_reset,
            inputs=[],
            outputs=[project_selector2]
        )

        project_selector2.change(
            fn=autofill_title,
            inputs=[project_selector2],
            outputs=[video_title]
        )

        generate_btn.click(
            generate_media,
            inputs=[project_selector2, reGen_AU_checkbox,reGen_IM_checkbox, reGen_VI_checkbox, video_title],
            outputs=[gen_status]
        )
    return demo
