# 🎬 Reddit Story to YouTube Shorts Automation

This project is a **fully automated pipeline** that turns long-form Reddit stories into **YouTube Shorts** and scheduled videos — complete with AI-generated voiceovers, animated subtitles, background gameplay, and automatic upload to YouTube.

> ⚡ **Manual workload reduced by 100%** — just run the script and everything is done: story selection, censorship, narration, editing, and upload scheduling.

---

## 📽️ Demo Output

Watch real examples of automatically generated videos here:  
➡️ [YouTube Channel](https://www.youtube.com/@StorySelects)  
*(Each video was created and uploaded with a single script run — no manual editing involved.)*

---

## ✨ Features

- 🔥 Scrapes top Reddit posts or long-form comments from multiple subreddits
- 🤖 **Rewrites stories with OpenAI API** to make them copyright-safe while preserving tone and narrative flow
- 🧼 Censors inappropriate language via **root-matching** + **context-aware replacements**  
- 🗣️ **ElevenLabs AI voices** for highly realistic narration (gender matched to story author when possible)  
- 🧠 Transcribes narration using **Whisper timestamped** for word-level timing
- 📝 Generates animated subtitles synced perfectly to narration  
- 🎮 Stitches random satisfying clips for background footage
- 🎵 Loops background music with optional “scary” or “normal” tracks depending on subreddit content
- 📺 Builds a dynamic title card with stylized stretching animation
- 🎬 Splits long stories into multiple YouTube Shorts (or long-form videos) using custom duration rules
- ⏰ Automatically uploads and schedules multi-part videos via YouTube API

---

## 🛠️ Tech Stack

- **Python 3**
- [PRAW](https://praw.readthedocs.io/) – Reddit API
- [OpenAI API](https://platform.openai.com/) – Story rewriting, title generation, gender guessing
- [ElevenLabs](https://elevenlabs.io/) – Text-to-Speech
- [OpenAI Whisper Timestamped](https://github.com/linto-ai/whisper-timestamped) – Transcription
- [MoviePy](https://zulko.github.io/moviepy/) – Video editing
- [Pydub](https://github.com/jiaaro/pydub) – Audio handling
- [Google YouTube API](https://developers.google.com/youtube/registering_an_application) – Upload + Scheduling
- `dotenv`, `PIL`, `textwrap`, `glob`, and more for file and formatting logic

---

## 🚀 How It Works

1. **Story Selection**  
   - Pulls a random top Reddit story (or long comment if needed)
   - Ensures no reposts by saving used submission IDs

2. **Story Transformation (OpenAI)**  
   - Rewrites story to be copyright-safe and safe for YouTube
   - Generates click-worthy Reddit-style titles
   - Guesses narrator’s gender for voice selection

3. **Narration (ElevenLabs)**  
   - Converts title + story into lifelike AI narration
   - Adjusts pacing, consistency, and speed automatically

4. **Video Generation**  
   - Title card with animated stretching effect
   - Subtitles aligned to narration via Whisper transcription
   - Background gameplay stitched to match story length
   - Music mixed in (scary/normal modes)

5. **Upload (YouTube API)**  
   - Uploads part 1 publicly
   - Optionally schedules subsequent parts (e.g. every 24h) or uploaded extended version as long-form content
