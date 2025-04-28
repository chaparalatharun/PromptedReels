import os
import gradio as gr
import requests
from engine.project_manager import load_json, save_json
from video_engine import get_text_to_image_prompt_from_llm, generate_dalle3_image_url

projects_dir = "projects"
BLOCKS_PER_PAGE = 5

CHAR_PROFILE_PATH = "./config/character_profiles.json"
CHARACTER_PROFILES = load_json(CHAR_PROFILE_PATH) if os.path.exists(CHAR_PROFILE_PATH) else {}

VIDEO_EFFECTS = [
    "None", "Zoom In", "Zoom Out", "Move Left", "Move Right", "Rotate", "Fade In", "Fade Out"
]

def get_project_choices():
    return [p for p in os.listdir(projects_dir) if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))]

def refresh_dropdown_and_reset():
    return gr.update(choices=get_project_choices(), value=None)

def auto_generate_and_save_prompt(scene_describe, chars_selected_keys, idx, project_name):
    selected_char_profiles = {key: CHARACTER_PROFILES[key] for key in chars_selected_keys if key in CHARACTER_PROFILES}
    new_prompt = get_text_to_image_prompt_from_llm(scene_describe, selected_char_profiles)
    input_path = os.path.join(projects_dir, project_name, "input.json")
    data = load_json(input_path)
    if len(data["scene"]) > idx:
        data["scene"][idx]["generate_image"] = new_prompt
        save_json(data, input_path)
    return new_prompt

def autofill_title(project_name):
    if not project_name:
        return gr.update(value="")
    input_path = os.path.join(projects_dir, project_name, "input.json")
    if os.path.exists(input_path):
        data = load_json(input_path)
        return gr.update(value=data.get("theme", ""))
    return gr.update(value="")


def load_page(project_name, ps):
    path = os.path.join(projects_dir, project_name, "input.json")
    data = load_json(path)
    scenes = data.get("scene", [])
    scripts = data.get("script", [])

    # 脚本选择列表
    script_choices = [f"{i}: {block.get('text', '')[:30]}" for i, block in enumerate(scripts)]

    page_blocks = scenes[ps:ps + BLOCKS_PER_PAGE]

    outputs = []

    for i in range(BLOCKS_PER_PAGE):
        idx = ps + i
        if i < len(page_blocks):
            block = page_blocks[i]
            matches = block.get("matches", [])

            # 提取 match 的脚本索引 和 特效
            selected_idxs = [f"{m['script_idx']}: {scripts[m['script_idx']]['text'][:30]}" if m['script_idx'] < len(
                scripts) else str(m['script_idx']) for m in matches]
            selected_effects = [m.get("effect", "None") for m in matches]

            # ---- 一行的输出 ----
            outputs.append(gr.update(value=f"**[{idx}]**"))  # idx_label (Markdown)
            outputs.append(gr.update(value=block.get("mode", "generate_image")))  # mode (Dropdown)
            outputs.append(gr.update(value=block.get("generate_image", "")))  # prompt (Textbox)
            outputs.append(gr.update(value=block.get("scene", "")))  # scene (Textbox)

            # image path preview (Image)
            image_rel_path = block.get("image")
            image_full_path = os.path.join(projects_dir, project_name, image_rel_path) if image_rel_path else None
            outputs.append(gr.update(value=image_full_path))

            # match_select (Dropdown, multiselect)
            outputs.append(gr.update(choices=script_choices, value=selected_idxs))

            # effect_selects (5个Dropdown)
            for j in range(5):
                if j < len(selected_effects):
                    outputs.append(gr.update(choices=VIDEO_EFFECTS, value=selected_effects[j]))
                else:
                    outputs.append(gr.update(choices=VIDEO_EFFECTS, value="None"))
        else:
            # ---- 不足一页，用空的补齐 ----
            outputs.append(gr.update(value=f"**[{idx}]**"))  # idx_label
            outputs.append(gr.update(value=""))  # mode
            outputs.append(gr.update(value=""))  # prompt
            outputs.append(gr.update(value=""))  # scene
            outputs.append(gr.update(value=None))  # image
            outputs.append(gr.update(choices=[], value=[]))  # match_select
            outputs.extend([gr.update(choices=VIDEO_EFFECTS, value="None") for _ in range(5)])  # 5个effect_select补空

    # 最后加上总scene数量，用来翻页控制
    outputs.append(len(scenes))

    return outputs


def save_all_blocks(project_name, ps, *block_values):
    input_path = os.path.join(projects_dir, project_name, "input.json")
    data = load_json(input_path)
    scenes = data.get("scene", [])

    for i in range(BLOCKS_PER_PAGE):
        idx = ps + i
        base = i * (9)  # 每行：mode, prompt, scene, match_select, 5个effect_select
        mode = block_values[base + 0]
        prompt = block_values[base + 1]
        scene_text = block_values[base + 2]
        selected_idxs = block_values[base + 3] or []
        selected_effects = block_values[base + 4:base + 9]

        if prompt or scene_text or selected_idxs:
            while len(scenes) <= idx:
                scenes.append({})
            image = scenes[idx].get("image", None)
            matches = []
            for j, sid in enumerate(selected_idxs):
                try:
                    sid = int(str(sid).split(":")[0])
                    effect = selected_effects[j] if j < len(selected_effects) else "None"
                    matches.append({"script_idx": sid, "effect": effect})
                except Exception as e:
                    print(f"Warning parsing match: {e}")

            scenes[idx] = {
                "mode": mode,
                "generate_image": prompt,
                "scene": scene_text,
                "image": image,
                "matches": matches
            }

    data["scene"] = scenes
    save_json(data, input_path)
    return "✅ Saved all blocks."

def build_stage2_ui():
    with gr.Blocks() as demo:
        gr.Markdown("### 🎞️ Video Block Editor (Dynamic Match-Effect)")

        with gr.Row():
            project_selector = gr.Dropdown(label="Project", choices=get_project_choices(), interactive=True)
            refresh_btn = gr.Button("🔄")
            video_title = gr.Textbox(label="Video Title", interactive=True)
            load_btn = gr.Button("📂 Load")

        with gr.Row():
            ps = gr.Number(value=0, label="Start Index", interactive=False)
            total_blocks = gr.Textbox(label="Total Blocks", interactive=False)

        with gr.Row():
            save_all_btn = gr.Button("💾 Save All")
            global_status = gr.Textbox(label="", interactive=False)

        with gr.Row():
            global_char_selector = gr.CheckboxGroup(label="🔵 Global Character Selector", choices=list(CHARACTER_PROFILES.keys()), interactive=True)

        def layout_block(index):
            with gr.Row():
                idx_label = gr.Markdown(f"**[{index}]**")
            with gr.Row():
                mode = gr.Dropdown(choices=["generate_image", "generate_video", "manual_image", "search_video"], label="Mode")
                scene = gr.Textbox(label="Scene", lines=2)
                auto = gr.Button("✨ Auto")
                gen_image_btn = gr.Button("🎨 Generate Image")
                prompt = gr.Textbox(label="Prompt", lines=2)
            with gr.Row():
                match_select = gr.Dropdown(label="🎯 Match Script Lines", choices=[], multiselect=True)
            with gr.Row():
                effect_selects = [gr.Dropdown(choices=VIDEO_EFFECTS, label=f"Effect {i+1}") for i in range(5)]
            with gr.Row():
                image_preview = gr.Image(label="🖼️ Preview", interactive=False)

            return idx_label, mode, prompt, scene, auto, gen_image_btn, match_select, effect_selects, image_preview

        block_uis = [layout_block(i) for i in range(BLOCKS_PER_PAGE)]
        flat_inputs = []
        flat_outputs = []

        for block in block_uis:
            idx_label, mode, prompt, scene, auto, gen_image_btn, match_select, effect_selects, image_preview = block
            flat_inputs.extend([mode, prompt, scene, match_select] + effect_selects)
            flat_outputs.extend([idx_label, mode, prompt, scene, image_preview, match_select] + effect_selects)

        refresh_btn.click(refresh_dropdown_and_reset, [], [project_selector])
        project_selector.change(autofill_title, [project_selector], [video_title])
        load_btn.click(load_page, [project_selector, ps], flat_outputs + [total_blocks])

        for i, block in enumerate(block_uis):
            idx_label, mode, prompt, scene, auto, gen_image_btn, match_select, effect_selects, image_preview = block

            auto.click(auto_generate_and_save_prompt, inputs=[scene, global_char_selector, gr.State(i), project_selector], outputs=[prompt])

            def generate_image(local_idx, ps_value, project_name):
                global_idx = ps_value + local_idx
                input_path = os.path.join(projects_dir, project_name, "input.json")
                data = load_json(input_path)
                block = data["scene"][global_idx]
                prompt_text = block.get("generate_image", "")
                if not prompt_text:
                    print(f"No prompt found at block {global_idx}")
                    return None
                url = generate_dalle3_image_url(prompt_text)
                if not url:
                    print(f"Failed to generate image for block {global_idx}")
                    return None
                save_path = os.path.join(projects_dir, project_name, f"image/{global_idx}.png")
                try:
                    img_data = requests.get(url).content
                    with open(save_path, 'wb') as handler:
                        handler.write(img_data)
                    block["image"] = f"image/{global_idx}.png"
                    save_json(data, input_path)
                except Exception as e:
                    print(f"Error downloading image: {e}")
                    return None
                return save_path

            gen_image_btn.click(generate_image, inputs=[gr.State(i), ps, project_selector], outputs=[image_preview])

        save_all_btn.click(save_all_blocks, [project_selector, ps] + flat_inputs, [global_status])

        def step_page(current_ps, delta, total):
            new_ps = max(0, min(int(current_ps) + delta, max(0, int(total) - BLOCKS_PER_PAGE)))
            return gr.update(value=new_ps)

        prev_btn = gr.Button("⬅️ Prev Page")
        next_btn = gr.Button("➡️ Next Page")

        prev_btn.click(step_page, [ps, gr.State(-BLOCKS_PER_PAGE), total_blocks], [ps]).then(load_page, [project_selector, ps], flat_outputs + [total_blocks])
        next_btn.click(step_page, [ps, gr.State(BLOCKS_PER_PAGE), total_blocks], [ps]).then(load_page, [project_selector, ps], flat_outputs + [total_blocks])

    return demo
