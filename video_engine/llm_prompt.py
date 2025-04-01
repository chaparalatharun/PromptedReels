import os
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_API_TOKEN = os.getenv("LLM_API_TOKEN")
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_API_HEADERS = {
    "Authorization": f"Bearer {LLM_API_TOKEN}",
    "Content-Type": "application/json"
}

def ask_llm_decision(script_text, theme):
    prompt = (
        "Given the following script, decide whether we should:\n"
        "- search a video online from a stock video site (output: search)\n"
        "- or generate a video using a text-to-video model (output: generate)\n"
        "Only return 'search' or 'generate', no explanation.\n\n"
        f"Script: {script_text}\n"
        f"Theme: {theme}"
    )
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    try:
        response = requests.post(LLM_API_URL, json=payload, headers=LLM_API_HEADERS)
        response.raise_for_status()
        decision = response.json()["choices"][0]["message"]["content"].strip().lower()
        return "generate" if "generate" in decision else "search"
    except Exception as e:
        print(f"❌ LLM Decision Error: {e}")
        return "search"

def get_video_query_from_llm(script_text, theme):
    prompt = (
        "Given a text script clip, return a short query (within 10 English words) "
        "that can be used to search a relevant video from Pexels.\n"
        "No explanation, just the keywords.\n"
        f"Script:\n{script_text}\n"
        f"Video theme: {theme}\n"
    )
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "max_tokens": 512,
    }
    try:
        response = requests.post(LLM_API_URL, json=payload, headers=LLM_API_HEADERS)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ LLM Prompt Error: {e}")
        return "nature"
