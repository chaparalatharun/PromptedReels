import os
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import requests

# 依赖外部对象
from video_engine.runway_api import generate_runway_video_from_image
from video_engine.siliconflow_api import generate_video_from_image_file, check_siliconflow_video_status
from runwayml import RunwayML

# 注意：这些全局对象需要初始化好
RUNWAY_CLIENT = RunwayML(api_key=os.getenv("RUNWAY_KEY"))
executor = ThreadPoolExecutor()
loop = asyncio.new_event_loop()
def start_loop(loop): asyncio.set_event_loop(loop); loop.run_forever()
threading.Thread(target=start_loop, args=(loop,), daemon=True).start()

async def poll_siliconflow_video(request_id, video_path):
    print(f"🧵 Polling SiliconFlow task {request_id}")
    for i in range(100):
        await asyncio.sleep(10)
        video_url = check_siliconflow_video_status(request_id)
        if video_url:
            try:
                video_data = requests.get(video_url)
                video_data.raise_for_status()
                with open(video_path, "wb") as f:
                    f.write(video_data.content)
                print(f"🎉 SiliconFlow video saved: {video_path}")
                return video_path
            except Exception as e:
                print(f"❌ Download error: {e}")
                return None
        print(f"⌛ Waiting... epoch {i}... for id:{request_id}")
    print(f"❌ SiliconFlow timeout for: {request_id}")
    return None

async def poll_runway_video(task_id, video_path):
    print(f"🧵 Polling Runway task {task_id}")
    for i in range(1000):
        await asyncio.sleep(10)
        try:
            result = RUNWAY_CLIENT.tasks.retrieve(task_id)
            status = result.status
            print(f"⌛ [{i}] Runway status: {status}")
            if status == "SUCCEEDED":
                video_url = result.output[0]
                video_data = requests.get(video_url)
                video_data.raise_for_status()
                with open(video_path, "wb") as f:
                    f.write(video_data.content)
                print(f"🎉 Runway video saved: {video_path}")
                return video_path
            elif status == "failed":
                print(f"❌ Runway task failed: {task_id}")
                return None
        except Exception as e:
            print(f"❌ Runway polling error: {e}")
            return None
    print(f"❌ Runway timeout for: {task_id}")
    return None

def generate_video_from_image(image_path: str, output_dir: str, prompt: str = "", use_runway: bool = False) -> str:
    """
    从一张图片生成视频，返回视频路径
    :param image_path: 输入图片路径
    :param output_dir: 输出视频保存的目录
    :param prompt: 用于生成的视频描述 prompt
    :param use_runway: 是否使用 runway（否则默认 siliconflow）
    :return: 保存下来的视频路径，失败返回 None
    """
    os.makedirs(output_dir, exist_ok=True)

    # 自动生成输出名字
    image_base = os.path.splitext(os.path.basename(image_path))[0]
    video_filename = f"{image_base}.mp4"
    video_path = os.path.join(output_dir, video_filename)

    if os.path.exists(video_path):
        print(f"✅ Video already exists: {video_path}")
        return video_path

    if use_runway:
        print(f"🚀 Submitting to Runway: {prompt}")
        try:
            task_id = generate_runway_video_from_image(prompt, image_path)
            future = asyncio.run_coroutine_threadsafe(
                poll_runway_video(task_id, video_path),
                loop
            )
            return future.result()  # 等待完成
        except Exception as e:
            print(f"❌ Runway submission error: {e}")
            return None
    else:
        print(f"🚀 Submitting to SiliconFlow: {prompt}")
        try:
            request_id = generate_video_from_image_file(prompt, image_path)
            if not request_id:
                print(f"❌ SiliconFlow submission failed")
                return None
            future = asyncio.run_coroutine_threadsafe(
                poll_siliconflow_video(request_id, video_path),
                loop
            )
            return future.result()
        except Exception as e:
            print(f"❌ SiliconFlow submission error: {e}")
            return None
