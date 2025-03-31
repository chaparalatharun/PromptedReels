import os
import gradio as gr
from functools import partial

from engine.audio_generator import generate_tts_audio
from engine.video_generator import generate_video_clip
from engine.composer import compose_final_video
from engine.project_manager import create_project, save_json, load_json
from engine.text_parser import split_script_to_chunks

projects_dir = "projects"
LINES_PER_PAGE = 5

def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]

# ----------------------
# Stage 1: Create Project
# ----------------------
def create_fn(name, script):
    path = create_project(name)
    chunks = split_script_to_chunks(script)
    json_data = {"title": name, "script": [{"text": c} for c in chunks]}
    save_json(json_data, os.path.join(path, "input.json"))
    updated_choices = get_project_choices()
    return (
        f"Created project '{name}' with {len(chunks)} chunks.",
        gr.update(choices=updated_choices),
        gr.update(choices=updated_choices),
        gr.update(choices=updated_choices)
    )

# ----------------------
# Stage 2: Generate Media
# ----------------------
def generate_media(project_name, reGen_AU_checkbox, reGen_VI_checkbox, video_title):
    if not project_name:
        return "No project selected"
    project_path = os.path.join(projects_dir, project_name)
    input_path = os.path.join(project_path, "input.json")
    data = load_json(input_path)

    # Generate video
    generate_video_clip(data, project_path, reGen=reGen_VI_checkbox, theme=video_title)
    # Generate TTS
    generate_tts_audio(data, project_path, reGen=reGen_AU_checkbox)

    # Save processed
    save_json(data, os.path.join(project_path, "processed.json"))
    return f"Media generated for project: {project_name} (Regenerate audio={reGen_AU_checkbox}, video={reGen_VI_checkbox})"

# ----------------------
# Stage 3: Compose Video
# ----------------------
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

# --------------------------------------------------
# Helpers for Stage 4 (Paginated editing of the JSON)
# --------------------------------------------------

def load_script_for_edit(project_name):
    """
    Loads the JSON from disk and returns it.
    Prefer 'processed.json', else 'input.json'.
    """
    if not project_name:
        return None
    project_path = os.path.join(projects_dir, project_name)
    processed_path = os.path.join(project_path, "processed.json")
    input_path = os.path.join(project_path, "input.json")

    if os.path.isfile(processed_path):
        return load_json(processed_path)
    elif os.path.isfile(input_path):
        return load_json(input_path)
    else:
        return None

def save_script_to_disk(project_name, data):
    """ Save final data to processed.json """
    if not project_name:
        return "No project selected."
    project_path = os.path.join(projects_dir, project_name)
    save_json(data, os.path.join(project_path, "processed.json"))
    return "Saved successfully!"

def regenerate_line(project_name, line_index, text, video):
    """
    Re-generate TTS audio for a single line. Also can re-download video, if desired.
    But here we just treat 'video' as a path.
    If you want to do dynamic searching from text, call `generate_video_clip` partially.
    """
    if not project_name:
        return f"No project selected."

    data = load_script_for_edit(project_name)
    if not data:
        return "Could not load project data."

    # Update that line in memory
    if line_index < 0 or line_index >= len(data["script"]):
        return f"Invalid line index {line_index}"

    data["script"][line_index]["text"] = text
    data["script"][line_index]["video"] = video

    # We'll do partial TTS on just that line
    project_path = os.path.join(projects_dir, project_name)

    single_line_data = {
        "title": data["title"],
        "script": [ data["script"][line_index] ]
    }

    # Regenerate TTS just for that block
    generate_tts_audio(single_line_data, project_path, reGen=True)
    # Put new audio references back into the full data
    data["script"][line_index]["audio"] = single_line_data["script"][0]["audio"]

    # Save to disk
    save_json(data, os.path.join(project_path, "processed.json"))
    return f"Line {line_index+1} regenerated. Audio={data['script'][line_index]['audio']}"

# UI logic to show/hide lines from current page
def update_page_ui(edit_data, page_index, *line_inputs):
    """
    Updates the UI for the given page_index.
    Each line has a group (group, text, video, audio) — need to show/hide all.
    `line_inputs` contains all elements in the order:
    [group0, text0, video0, audio0, group1, text1, video1, audio1, ...]
    """
    if not edit_data:
        return [
            gr.update(visible=False, value="") for _ in line_inputs
        ]

    script_blocks = edit_data["script"]
    total_lines = len(script_blocks)
    start_idx = page_index * LINES_PER_PAGE
    end_idx = start_idx + LINES_PER_PAGE

    updates = []
    for i in range(LINES_PER_PAGE):
        line_num = start_idx + i
        base_idx = i * 4  # group + 3 components

        if line_num < total_lines:
            block = script_blocks[line_num]
            updates.append(gr.update(visible=True))  # group
            updates.append(gr.update(visible=True, value=block.get("text", "")))  # text
            updates.append(gr.update(visible=True, value=block.get("video", "")))  # video
            audio_list = block.get("audio", [])
            audio_str = ", ".join(audio_list) if audio_list else ""
            updates.append(gr.update(visible=True, value=audio_str))  # audio
        else:
            updates.append(gr.update(visible=False))  # group
            updates.append(gr.update(visible=False, value=""))  # text
            updates.append(gr.update(visible=False, value=""))  # video
            updates.append(gr.update(visible=False, value=""))  # audio

    return updates

def save_page_edits(
    project_name,
    edit_data_state,
    page_index,
    # For each of the 5 lines, we have (text,video,audio)
    *line_values
):
    """
    Merges the current page's textboxes back into the in-memory data.
    line_values is 15 items (5 lines * 3 fields each).
    """
    if not edit_data_state:
        return edit_data_state, "No data loaded."

    data = edit_data_state
    script_blocks = data["script"]
    total_lines = len(script_blocks)

    start_idx = page_index * LINES_PER_PAGE

    # line_values is: (text0, video0, audio0, text1, video1, audio1, ...)
    for i in range(LINES_PER_PAGE):
        line_num = start_idx + i
        if line_num >= total_lines:
            break

        base = i * 3
        txt = line_values[base+0]
        vid = line_values[base+1]
        aud_str = line_values[base+2]

        script_blocks[line_num]["text"] = txt
        script_blocks[line_num]["video"] = vid
        aud_list = [s.strip() for s in aud_str.split(",") if s.strip()]
        script_blocks[line_num]["audio"] = aud_list

    # updated data in memory
    return data, f"Page {page_index+1} edits saved in memory. (Not yet written to disk!)"

def go_to_page(project_name, new_page, edit_data_state):
    """
    Just returns the new page index (clamped).
    We'll let the UI .update(...) show the final page index.
    """
    if not edit_data_state:
        return 0  # no data
    total_lines = len(edit_data_state["script"])
    max_page = (total_lines - 1) // LINES_PER_PAGE  # integer division
    # clamp
    if new_page < 0:
        new_page = 0
    if new_page > max_page:
        new_page = max_page
    return new_page

def save_all_edits_to_disk(project_name, edit_data_state):
    if not edit_data_state:
        return "No data in memory to save."

    # Actually write to processed.json
    msg = save_script_to_disk(project_name, edit_data_state)
    return msg

with gr.Blocks() as demo:
    # --------------------------
    # Stage 1: Create Project UI
    # --------------------------
    with gr.Tab("Stage 1: Create Project"):
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
            outputs=[output, project_selector_stage2, project_selector_stage3, project_selector_stage4]
        )

    # --------------------------
    # Stage 2: Generate Media UI
    # --------------------------
    with gr.Tab("Stage 2: Generate Media"):
        project_selector2 = gr.Dropdown(label="Select Project", choices=get_project_choices())
        reGen_AU_checkbox = gr.Checkbox(label="Regenerate Media (audio)", value=True)
        reGen_VI_checkbox = gr.Checkbox(label="Regenerate Media (video)", value=True)
        video_title = gr.Textbox(label="Video Title")
        generate_btn = gr.Button("Generate Audio & Video")
        gen_status = gr.Textbox(label="Generation Status")

        generate_btn.click(
            generate_media,
            inputs=[project_selector2, reGen_AU_checkbox, reGen_VI_checkbox, video_title],
            outputs=[gen_status]
        )

    # --------------------------
    # Stage 3: Compose Video UI
    # --------------------------
    with gr.Tab("Stage 3: Compose Video"):
        project_selector3 = gr.Dropdown(label="Select Project", choices=get_project_choices())
        compose_btn = gr.Button("Compose Final Video")
        compose_output = gr.Textbox(label="Compose Status")

        compose_btn.click(
            compose,
            inputs=[project_selector3],
            outputs=[compose_output]
        )

    # -------------------------------------------------
    # Stage 4: Paginated JSON Edit (New Implementation)
    # -------------------------------------------------
    with gr.Tab("Stage 4: Edit Script"):
        project_selector4 = gr.Dropdown(
            label="Select Project",
            choices=get_project_choices()
        )
        load_btn = gr.Button("Load Script for Editing")

        # We'll store:
        #   1) The entire script JSON in memory
        #   2) The current page index
        edit_data_state = gr.State()
        page_state = gr.State(0)

        with gr.Row():
            prev_btn = gr.Button("Previous Page")
            next_btn = gr.Button("Next Page")
            save_page_btn = gr.Button("Save This Page Edits (in memory)")

        # Show the current page number
        current_page_label = gr.Textbox(label="Current Page", interactive=False)

        # We define 5 lines worth of (Text, Video, Audio) + a "Regenerate" button (optional)
        line_textboxes = []
        line_videos = []
        line_audios = []
        line_regen_buttons = []

        line_groups = []  # 新增

        for i in range(LINES_PER_PAGE):
            with gr.Group(visible=False) as line_group:
                gr.Markdown(f"**Line {i + 1} (on this page)**")
                txt = gr.Textbox(label="Text", visible=False)
                vid = gr.Textbox(label="Video", visible=False)
                aud = gr.Textbox(label="Audio (comma-separated)", visible=False)
                regen_btn = gr.Button(f"Regenerate line (this page slot {i + 1})")

            line_groups.append(line_group)  # 新增
            line_textboxes.append(txt)
            line_videos.append(vid)
            line_audios.append(aud)
            line_regen_buttons.append(regen_btn)


        # For each line's regen button, we define a callback:
        # We'll read the line's index in the global script as (page_state * LINES_PER_PAGE + i)
        # Then call regenerate_line(...) with the text, video, etc.
        def regenerate_single_line(
            project_name, edit_data, page_idx, slot_index,
            text_value, video_value
        ):
            """
            Regenerate TTS for the line at global index = page_idx*LINES_PER_PAGE + slot_index
            We'll first save the updated text/video in memory, then do the TTS call.
            """
            if not edit_data:
                return "No data loaded."

            line_idx = page_idx*LINES_PER_PAGE + slot_index
            return regenerate_line(project_name, line_idx, text_value, video_value)

        for i in range(LINES_PER_PAGE):
            line_regen_buttons[i].click(
                fn=regenerate_single_line,
                inputs=[
                    project_selector4,    # project_name
                    edit_data_state,      # entire data
                    page_state,           # current page
                    gr.State(i),          # slot index
                    line_textboxes[i],    # text
                    line_videos[i]        # video
                ],
                outputs=[]
            )

        with gr.Row():
            save_all_btn = gr.Button("Save All to Disk")
            save_status = gr.Textbox(label="Status / Messages")

        # Now define the callbacks for stage 4

        def on_load_click(proj):
            data = load_script_for_edit(proj)
            if not data:
                return None, 0, "No data loaded or no such project."
            return data, 0, f"Loaded {proj} with {len(data['script'])} lines."


        # We also need to re-render the UI whenever edit_data_state or page_state changes
        # We'll do that with a separate "update_page_ui" callback, triggered by a .change()
        # or a "then" chain. We'll chain them to the load_btn, next_btn, prev_btn, save_page_btn, etc.

        def show_page_number(page_idx, edit_data):
            """Just show 'Page X of Y' in a textbox."""
            if not edit_data:
                return "Page 0 (no data)"
            total_lines = len(edit_data["script"])
            max_page = (total_lines - 1) // LINES_PER_PAGE if total_lines > 0 else 0
            return f"Page {page_idx+1} of {max_page+1}"

        # after on_load_click sets data and page=0, we want to fill UI:
        load_btn.click(
            fn=on_load_click,
            inputs=[project_selector4],
            outputs=[edit_data_state, page_state, save_status]
        ).then(
            fn=update_page_ui,
            inputs=[edit_data_state, page_state] +
                   sum([[t, v, a] for t, v, a in zip(line_textboxes, line_videos, line_audios)], []),

            outputs=sum([[g, t, v, a] for g, t, v, a in zip(line_groups, line_textboxes, line_videos, line_audios)], [])
        ).then(
            fn=show_page_number,
            inputs=[page_state, edit_data_state],
            outputs=[current_page_label]
        )

        # Save page logic:
        #  1) merges current textboxes into memory
        #  2) returns updated memory
        save_page_btn.click(
            fn=save_page_edits,
            inputs=[
                project_selector4,
                edit_data_state,
                page_state
            ]
            + line_textboxes
            + line_videos
            + line_audios,
            outputs=[edit_data_state, save_status],
        ).then(
            fn=update_page_ui,
            inputs=[edit_data_state, page_state] +
                   sum([[t, v, a] for t, v, a in zip(line_textboxes, line_videos, line_audios)], []),

            outputs=sum([[g, t, v, a] for g, t, v, a in zip(line_groups, line_textboxes, line_videos, line_audios)], [])
        ).then(
            fn=show_page_number,
            inputs=[page_state, edit_data_state],
            outputs=[current_page_label]
        )

        # Next page logic:
        def next_page(project_name, data, current_page):
            return go_to_page(project_name, current_page+1, data)

        next_btn.click(
            fn=save_page_edits,
            inputs=[
                project_selector4,
                edit_data_state,
                page_state
            ]
            + line_textboxes
            + line_videos
            + line_audios,
            outputs=[edit_data_state, save_status],
        ).then(
            fn=next_page,
            inputs=[project_selector4, edit_data_state, page_state],
            outputs=[page_state],
        ).then(
            fn=update_page_ui,
            inputs=[edit_data_state, page_state] +
                   sum([[t, v, a] for t, v, a in zip(line_textboxes, line_videos, line_audios)], []),

            outputs=sum([[g, t, v, a] for g, t, v, a in zip(line_groups, line_textboxes, line_videos, line_audios)], [])
        ).then(
            fn=show_page_number,
            inputs=[page_state, edit_data_state],
            outputs=[current_page_label]
        )

        # Previous page logic:
        def prev_page(project_name, data, current_page):
            return go_to_page(project_name, current_page-1, data)

        prev_btn.click(
            fn=save_page_edits,
            inputs=[
                project_selector4,
                edit_data_state,
                page_state
            ]
            + line_textboxes
            + line_videos
            + line_audios,
            outputs=[edit_data_state, save_status],
        ).then(
            fn=prev_page,
            inputs=[project_selector4, edit_data_state, page_state],
            outputs=[page_state],
        ).then(
            fn=update_page_ui,
            inputs=[edit_data_state, page_state] +
                   sum([[t, v, a] for t, v, a in zip(line_textboxes, line_videos, line_audios)], []),

            outputs=sum([[g, t, v, a] for g, t, v, a in zip(line_groups, line_textboxes, line_videos, line_audios)], [])
        ).then(
            fn=show_page_number,
            inputs=[page_state, edit_data_state],
            outputs=[current_page_label]
        )

        # Save ALL to disk:
        save_all_btn.click(
            fn=save_all_edits_to_disk,
            inputs=[project_selector4, edit_data_state],
            outputs=[save_status]
        )


def launch_app():
    # add share=True for public link
    demo.launch(share=True)
