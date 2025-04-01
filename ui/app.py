import os
import gradio as gr

from ui.stage1_create import build_stage1_ui
from ui.stage2_generate import build_stage2_ui
from ui.stage3_compose import build_stage3_ui
from ui.stage4_edit import build_stage4_ui

with gr.Blocks() as demo:
    with gr.Tab("Stage 1: Create Project"):
        build_stage1_ui()

    with gr.Tab("Stage 2: Generate Media"):
        build_stage2_ui()

    with gr.Tab("Stage 3: Compose Video"):
        build_stage3_ui()

    with gr.Tab("Stage 4: Edit Script"):
        build_stage4_ui()


def launch_app():
    demo.launch(
        share=True,
        allowed_paths=["."]
    )
