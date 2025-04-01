import os
import gradio as gr
from engine.project_manager import load_json, save_json
from audio_engine.audio_generator import generate_tts_audio

projects_dir = "projects"
LINES_PER_PAGE = 5
MAX_AUDIO_PREVIEWS = 3

def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]

def load_script_for_edit(project_name):
    if not project_name:
        return None
    project_path = os.path.join(projects_dir, project_name)
    for filename in ["processed.json", "input.json"]:
        filepath = os.path.join(project_path, filename)
        if os.path.isfile(filepath):
            return load_json(filepath)
    return None

def save_script_to_disk(project_name, data):
    if not project_name:
        return "No project selected."
    project_path = os.path.join(projects_dir, project_name)
    save_json(data, os.path.join(project_path, "processed.json"))
    return "Saved successfully!"

def regenerate_line(project_name, line_index, text, video):
    if not project_name:
        return f"No project selected."
    data = load_script_for_edit(project_name)
    if not data:
        return "Could not load project data."

    if line_index < 0 or line_index >= len(data["script"]):
        return f"Invalid line index {line_index}"

    data["script"][line_index]["text"] = text
    data["script"][line_index]["video"] = video

    project_path = os.path.join(projects_dir, project_name)

    single_line_data = {
        "title": data["title"],
        "script": [data["script"][line_index]]
    }

    generate_tts_audio(single_line_data, project_path, reGen=True)
    data["script"][line_index]["audio"] = single_line_data["script"][0]["audio"]

    save_json(data, os.path.join(project_path, "processed.json"))
    return f"Line {line_index+1} regenerated. Audio={data['script'][line_index]['audio']}"

def go_to_page(project_name, new_page, edit_data_state):
    if not edit_data_state:
        return 0
    total_lines = len(edit_data_state["script"])
    max_page = (total_lines - 1) // LINES_PER_PAGE
    return max(0, min(new_page, max_page))

def save_all_edits_to_disk(project_name, edit_data_state):
    if not edit_data_state:
        return "No data in memory to save."
    return save_script_to_disk(project_name, edit_data_state)



def build_stage4_ui():
    project_selector4 = gr.Dropdown(
        label="Select Project",
        choices=get_project_choices()
    )
    load_btn = gr.Button("Load Script for Editing")

    edit_data_state = gr.State()
    page_state = gr.State(0)

    with gr.Row():
        prev_btn = gr.Button("Previous Page")
        next_btn = gr.Button("Next Page")
        save_page_btn = gr.Button("Save This Page Edits (in memory)")

    current_page_label = gr.Textbox(label="Current Page", interactive=False)

    line_textboxes, line_videos, line_audios = [], [], []
    line_video_previews, line_audio_previews = [], []
    line_regen_buttons, line_groups = [], []

    for i in range(LINES_PER_PAGE):
        with gr.Group(visible=False) as line_group:
            gr.Markdown(f"**Line {i + 1} (on this page)**")
            txt = gr.Textbox(label="Text", visible=False)
            vid_path = gr.Textbox(label="Video Path", visible=False)
            vid_player = gr.Video(label="Video Preview", visible=False)
            aud_path = gr.Textbox(label="Audio (comma-separated)", visible=False)
            aud_players = [gr.Audio(label=f"Audio Preview {j + 1}", visible=False) for j in range(MAX_AUDIO_PREVIEWS)]
            regen_btn = gr.Button(f"Regenerate line (slot {i + 1})")

        line_groups.append(line_group)
        line_textboxes.append(txt)
        line_videos.append(vid_path)
        line_audios.append(aud_path)
        line_video_previews.append(vid_player)
        line_audio_previews.append(aud_players)
        line_regen_buttons.append(regen_btn)

    def update_page_ui(edit_data, page_index, *line_inputs):
        if not edit_data:
            return [gr.update(visible=False, value="") for _ in line_inputs]

        script_blocks = edit_data["script"]
        total_lines = len(script_blocks)
        start_idx = page_index * LINES_PER_PAGE
        updates = []

        for i in range(LINES_PER_PAGE):
            line_num = start_idx + i
            if line_num < total_lines:
                block = script_blocks[line_num]
                video_path = block.get("video", "")
                audio_list = block.get("audio", [])
                video_preview_path = f"projects/{edit_data['title']}/{video_path}" if video_path else None
                audio_preview_paths = [f"projects/{edit_data['title']}/{a}" for a in audio_list]

                updates.append(gr.update(visible=True))  # group
                updates.append(gr.update(visible=True, value=block.get("text", "")))
                updates.append(gr.update(visible=True, value=video_path))
                updates.append(gr.update(visible=True, value=video_preview_path))
                updates.append(gr.update(visible=True, value=', '.join(audio_list)))
                for j in range(MAX_AUDIO_PREVIEWS):
                    if j < len(audio_preview_paths):
                        updates.append(gr.update(visible=True, value=audio_preview_paths[j]))
                    else:
                        updates.append(gr.update(visible=False, value=None))
            else:
                updates.extend([
                    gr.update(visible=False), gr.update(visible=False, value=""),
                    gr.update(visible=False, value=""), gr.update(visible=False, value=None),
                    gr.update(visible=False, value=""),
                ])
                updates.extend([gr.update(visible=False, value=None) for _ in range(MAX_AUDIO_PREVIEWS)])
        return updates

    def save_page_edits(project_name, edit_data_state, page_index, *line_values):
        if not edit_data_state:
            return edit_data_state, "No data loaded."
        data = edit_data_state
        script_blocks = data["script"]
        total_lines = len(script_blocks)
        start_idx = page_index * LINES_PER_PAGE

        for i in range(LINES_PER_PAGE):
            line_num = start_idx + i
            if line_num >= total_lines:
                break
            base = i * 3
            txt, vid, aud_str = line_values[base], line_values[base + 1], line_values[base + 2]
            aud_list = [s.strip() for s in aud_str.split(",") if s.strip()]
            script_blocks[line_num].update({"text": txt, "video": vid, "audio": aud_list})
        return data, f"Page {page_index+1} edits saved in memory."

    def regenerate_single_line(project_name, edit_data, page_idx, slot_index, text_value, video_value):
        if not edit_data:
            return "No data loaded."
        line_idx = page_idx * LINES_PER_PAGE + slot_index
        return regenerate_line(project_name, line_idx, text_value, video_value)

    def show_page_number(page_idx, edit_data):
        if not edit_data:
            return "Page 0 (no data)"
        total_lines = len(edit_data["script"])
        max_page = (total_lines - 1) // LINES_PER_PAGE if total_lines > 0 else 0
        return f"Page {page_idx+1} of {max_page+1}"

    save_all_btn = gr.Button("Save All to Disk")
    save_status = gr.Textbox(label="Status / Messages")

    page_inputs, page_outputs = [], []
    for i in range(LINES_PER_PAGE):
        page_inputs += [line_textboxes[i], line_videos[i], line_audios[i]]
        page_inputs += [line_video_previews[i]] + line_audio_previews[i]

        page_outputs += [line_groups[i], line_textboxes[i], line_videos[i]]
        page_outputs += [line_video_previews[i], line_audios[i]] + line_audio_previews[i]

    def on_load_click(proj):
        data = load_script_for_edit(proj)
        if not data:
            return None, 0, "No data loaded or no such project."
        return data, 0, f"Loaded {proj} with {len(data['script'])} lines."

    load_btn.click(
        fn=on_load_click,
        inputs=[project_selector4],
        outputs=[edit_data_state, page_state, save_status]
    ).then(
        fn=update_page_ui,
        inputs=[edit_data_state, page_state] + page_inputs,
        outputs=page_outputs
    ).then(
        fn=show_page_number,
        inputs=[page_state, edit_data_state],
        outputs=[current_page_label]
    )

    save_page_btn.click(
        fn=save_page_edits,
        inputs=[project_selector4, edit_data_state, page_state] + line_textboxes + line_videos + line_audios,
        outputs=[edit_data_state, save_status]
    ).then(
        fn=update_page_ui,
        inputs=[edit_data_state, page_state] + page_inputs,
        outputs=page_outputs
    ).then(
        fn=show_page_number,
        inputs=[page_state, edit_data_state],
        outputs=[current_page_label]
    )

    def next_page(project_name, data, current_page):
        return go_to_page(project_name, current_page + 1, data)

    next_btn.click(
        fn=save_page_edits,
        inputs=[project_selector4, edit_data_state, page_state] + line_textboxes + line_videos + line_audios,
        outputs=[edit_data_state, save_status]
    ).then(
        fn=next_page,
        inputs=[project_selector4, edit_data_state, page_state],
        outputs=[page_state]
    ).then(
        fn=update_page_ui,
        inputs=[edit_data_state, page_state] + page_inputs,
        outputs=page_outputs
    ).then(
        fn=show_page_number,
        inputs=[page_state, edit_data_state],
        outputs=[current_page_label]
    )

    def prev_page(project_name, data, current_page):
        return go_to_page(project_name, current_page - 1, data)

    prev_btn.click(
        fn=save_page_edits,
        inputs=[project_selector4, edit_data_state, page_state] + line_textboxes + line_videos + line_audios,
        outputs=[edit_data_state, save_status]
    ).then(
        fn=prev_page,
        inputs=[project_selector4, edit_data_state, page_state],
        outputs=[page_state]
    ).then(
        fn=update_page_ui,
        inputs=[edit_data_state, page_state] + page_inputs,
        outputs=page_outputs
    ).then(
        fn=show_page_number,
        inputs=[page_state, edit_data_state],
        outputs=[current_page_label]
    )

    save_all_btn.click(
        fn=save_all_edits_to_disk,
        inputs=[project_selector4, edit_data_state],
        outputs=[save_status]
    )

    for i in range(LINES_PER_PAGE):
        line_regen_buttons[i].click(
            fn=regenerate_single_line,
            inputs=[
                project_selector4,
                edit_data_state,
                page_state,
                gr.State(i),
                line_textboxes[i],
                line_videos[i],
            ],
            outputs=[]
        )
