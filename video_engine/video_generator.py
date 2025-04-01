import os
import requests
from video_engine.llm_prompt import get_video_query_from_llm, ask_llm_decision
from video_engine.pexels_api import get_pexels_video_url

def generate_video_clip(data, project_path, reGen=True, theme=""):
    output_name = os.path.basename(project_path)
    output_video = os.path.join(project_path, "video")
    os.makedirs(output_video, exist_ok=True)

    for index, block in enumerate(data["script"]):
        script = block["text"]
        video_filename = f"{output_name}_{index + 1}.mp4"
        video_file_path = os.path.join(output_video, video_filename)

        if os.path.exists(video_file_path) and not reGen:
            print(f"Video exists, skipping: {video_file_path}")
            data["script"][index]["video"] = f"video/{video_filename}"
            continue

        # Ask LLM for decision
        print(f"[LLM] Deciding method for: {script}")
        decision = ask_llm_decision(script, theme)
        block["video_generation_method"] = decision

        if decision == "search":
            query = get_video_query_from_llm(script, theme)
            print(f"[Pexels] Searching video with query: {query}")
            video_url = get_pexels_video_url(query)
            block["video_search_prompt"] = query
            block["video_search_result"] = video_url if video_url else "Not Found"

            if not video_url:
                print(f"❌ No video found for script: {script}")
                continue

            try:
                print(f"⬇️ Downloading video: {video_url}")
                video_response = requests.get(video_url)
                video_response.raise_for_status()
                with open(video_file_path, "wb") as f:
                    f.write(video_response.content)
                block["video"] = f"video/{video_filename}"
                print(f"✅ Saved video: {video_file_path}")
            except Exception as e:
                print(f"❌ Error downloading video: {e}")
        else:
            print(f"🧪 Text-to-video generation not implemented yet. Skipping: {script}")
            block["video"] = "t2v_not_implemented"

    return data
