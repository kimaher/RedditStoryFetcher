# 🎬 Reddit Story to YouTube Shorts Automation

This project is a **fully automated pipeline** that turns long-form Reddit stories into **YouTube Shorts** and scheduled videos — complete with AI-generated voiceovers, animated subtitles, background gameplay, and automatic upload to YouTube.

> ⚡ **Manual workload reduced by 100%** — just run the script and everything is done: story selection, censorship, narration, editing, and upload scheduling.

---

## 📽️ Demo Output

Watch real examples of automatically generated videos here:  
➡️ [YouTube Channel](https://www.youtube.com/@Real_Reddit32)  
*(Each video was created and uploaded with a single script run — no manual editing involved.)*

---

## ✨ Features

- 🔥 Scrapes top Reddit posts or long-form comments from multiple subreddits
- 🧼 Censors inappropriate language via root-matching logic
- 🗣️ Uses **Amazon Polly** for realistic TTS narration
- 🧠 Transcribes narration using **Whisper timestamped** for word-level timing
- 📝 Generates animated subtitles synced to voiceover
- 🎮 Stitches random Minecraft gameplay clips for background footage
- 🎵 Loops soft background music underneath narration
- 📺 Builds a dynamic title card with stylized stretching
- 🎬 Splits stories into parts (if needed) with YouTube Shorts timing logic
- ⏰ Automatically uploads and schedules multi-part videos via YouTube API

---

## 🛠️ Tech Stack

- **Python 3**
- [PRAW](https://praw.readthedocs.io/) – Reddit API
- [Amazon Polly](https://aws.amazon.com/polly/) – Text-to-Speech
- [OpenAI Whisper Timestamped](https://github.com/linto-ai/whisper-timestamped) – Transcription
- [MoviePy](https://zulko.github.io/moviepy/) – Video editing
- [Pydub](https://github.com/jiaaro/pydub) – Audio handling
- [Google YouTube API](https://developers.google.com/youtube/registering_an_application) – Upload + Scheduling
- `dotenv`, `PIL`, `textwrap`, `glob`, and more for file and formatting logic

---

## 🚀 How It Works

1. **Story Selection**  
   Pulls a random top post from selected subreddits and appends long comments if needed. Saves submission id in text file to ensure the channel does not repost the same stories.

2. **Text Processing**  
   Filters profanity, wraps long lines, and splits the story for multi-part delivery.

3. **Narration**  
   Converts title and story to TTS audio using Amazon Polly.

4. **Video Generation**  
   - Title card image (stretchable background)
   - Voice + background gameplay
   - Whisper-transcribed subtitles timed to each word
   - Background music mixed in

5. **Upload**  
   Uses YouTube API to:
   - Upload part 1 publicly
   - Schedule remaining parts 12 hours apart (configurable)
