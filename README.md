# Prompted Reels 🎥🤖

**Prompted Reels** is an AI-powered pipeline for creating faceless short-form videos (Reels, Shorts, TikToks) from scripts. It combines voice synthesis, visual matching, and LLM-powered scene generation to automate the video creation process.

---

## 🚀 Getting Started

### 1. Clone the Project

```bash
git clone https://github.com/yourusername/prompted-reels.git
cd prompted-reels
```

---

## 🐍 Backend Setup (FastAPI)

### 2. Create Python Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file and fill in:

```env
PEXELS_API_KEY=your_pexels_key
TEXT2VIDEO_API_KEY=your_open_sora_or_gen2_key
ELEVEN_LABS_API_KEY=your_eleven_labs_key
LLM_API_KEY=your_llm_key  # DeepSeek or Claude
OPENAI_API_KEY=your_openai_key  # For GPT-4o reranking
```

### 5. Start the FastAPI Server

```bash
uvicorn api.main:app --reload
```

---

## 🖥️ Frontend Setup (React)

### 1. Navigate to Frontend Directory

```bash
cd frontend  # or the directory where your frontend lives
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Run the Development Server

```bash
npm run dev
```

This will start the frontend on `http://localhost:5173` (default for Vite or similar tooling).

Make sure your backend FastAPI server is also running on port 8000 to enable API calls.

---

## 📊 Architecture Overview

```mermaid
graph TD
    A[Script Input] --> B[Split into Blocks]
    B --> C[TTS: ElevenLabs API or GPT-SoVITS]
    B --> D[LLM generates visual prompt]
    D --> E[Pexels API fetch]
    E --> F[Download + Trim Videos]
    F --> G[Visual Reranker (GPT-4o + Thumbnails)]
    C --> H[Final Composition]
    G --> H
    H --> I[Render Final Reel]
```

---

## 🎤 Voice Generation (TTS)

### 1. ElevenLabs (Recommended)

* High-quality, real-time speech synthesis
* Custom voices or stock narrator

Request example:

```bash
POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id>
Authorization: Bearer $ELEVEN_LABS_API_KEY
```

### 2. GPT-SoVITS

* Alternative open-source model for voice cloning
* Can be self-hosted and fine-tuned on character voices

---

## 🎮 Visual Matching

### Scene Planning with GPT-4o

Each narration block is passed through an LLM to generate a sequence of specific visual scenes using the `plan_visual_scenes` function (see `api/services/scene_planner.py`).

The LLM receives:

* The full narration block
* Optional user prompt or visual guidance
* Total narration duration (e.g., 8 seconds)

The model returns a structured JSON list like:

```json
[
  { "description": "man brushing teeth in mirror", "target_sec": 4 },
  { "description": "alarm clock ringing at 6 AM", "target_sec": 4 }
]
```

Each description is then used to search for relevant stock videos using the Pexels API.

### Pexels API Integration

We fetch top-matching free stock video clips based on these LLM-generated descriptions and trim them to match the assigned duration. Embedding-based similarity is used to choose top candidates.

```

### Pexels API Integration
We fetch top-matching free stock video clips and trim them to fit the target duration. The best match is selected using embedding-based similarity.

---

## 🌍 Video Reranking with GPT-4o

In `api/services/video_reranker.py`, we use GPT-4o to select the best-matching video from a set of candidates based on the narration block, LLM-generated scene description, optional user prompt, and available Pexels metadata.

**Flow:**
1. Send narration block, scene description, and user prompt
2. Attach candidate video thumbnails as visual proxies
3. Provide metadata for each video (title, tags, duration, etc.)
4. GPT-4o uses visual and textual context to select the best-matching video index (0-based)

This adds a final semantic filter to ensure the most contextually accurate video clip is selected for each block, combining both visual inspection and metadata reasoning from the Pexels API.

---

## 🎨 Final Composition

### 1. Block-Level Output
Each narration block produces:
- `audio/block_0.mp3`
- `video/block_0.mp4`

### 2. Stitching
Using FFmpeg or `moviepy`, we merge blocks into:
- `full_video.mp4`
- `subtitles.srt` (optional)

---

## 📁 Project Folder Structure

```

my\_project/
├── audio/
│   ├── block\_0.mp3
│   └── block\_1.mp3
├── video/
│   ├── block\_0.mp4
│   └── block\_1.mp4
├── processed.json
└── full\_video.mp4

```

---



## 🌱 Future Roadmap

- [ ] Music/ambient background support
- [ ] Subtitle alignment improvements
- [ ] Optional B-roll layering
- [ ] Platform publishing (YouTube, TikTok)

---

## 🙌 Credits
Tharun Chaparala

```