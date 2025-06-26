import praw
import random
from gtts import gTTS
from dotenv import load_dotenv
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, concatenate_audioclips, TextClip
from moviepy.video.fx import FadeIn, FadeOut, Resize
import glob
import time
random.seed(time.time())

load_dotenv()

id = os.getenv('REDDIT_CLIENT_ID')
secret = os.getenv('REDDIT_CLIENT_SECRET')
agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

save_folder = "D:/Videos/GeneratedVids"
os.makedirs(save_folder, exist_ok=True)

def get_random_story():
    hostsub = random.choice(['offmychest', 'nosleep', 'creepypasta', 'shortscarystories', 'AmItheAsshole', 'confession', 'AskReddit'])
    subreddit = reddit.subreddit(hostsub).hot(limit=20)
    print(hostsub)
    try:
        submission = random.choice([sub for sub in subreddit if sub.selftext != ''])
        return submission.title, submission.selftext, submission.id
    except IndexError:
        return None, None, None
    
def text_to_speech(text, output_path):
    tts = gTTS(text=text, lang='en')
    tts.save(output_path)
    print(f"MP3 saved as {output_path}")

def choose_vid_folder(root_folder='D:/Videos/BackgroundG'):
    subfolders = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    return random.choice(subfolders)

def get_gameplay(folder, length):
    files = glob.glob(os.path.join(folder, "*.mp4"))
    random.shuffle(files)
    clips = []
    total = 0
    for f in files:
        clip = VideoFileClip(f)
        clips.append(clip)
        total += clip.duration
        if total >= length:
            break
    final = concatenate_videoclips(clips).subclipped(0,length)
    return final

def build_video(stitle, sstory, title_audio_path, story_audio_path, output_path):
    text_to_speech(stitle, title_audio_path)
    text_to_speech(sstory, story_audio_path)

    title_audio = AudioFileClip(title_audio_path)
    story_audio = AudioFileClip(story_audio_path)

    total_length = title_audio.duration + story_audio.duration
    background_gameplay = get_gameplay(choose_vid_folder(),total_length)

    base_card = (ImageClip('./titlecard.png')
                .with_duration(title_audio.duration)
                .with_position('center')
                .with_effects([Resize(height=350), FadeIn(0.3), FadeOut(0.3)]))
    
    title_text = (
        TextClip(
            font="C:/Windows/Fonts/ARLRDBD.TTF",
            text=stitle,
            size=(int(base_card.w * 0.9), int(base_card.h * 0.7)),
            color='white',
            method='caption',
            text_align='center',
            duration=title_audio.duration,
        )
        .with_position(('center', int(base_card.h * 0.2)))
    )

    title_card = CompositeVideoClip([base_card, title_text]).with_effects([FadeIn(0.3), FadeOut(0.3)]).with_position('center')

    audio = concatenate_audioclips([title_audio, story_audio])

    final_vid = CompositeVideoClip([background_gameplay.with_audio(audio), title_card.with_start(0)])

    final_vid.write_videofile(output_path, codec="libx264",threads=12,bitrate="8000k",fps=30)
    print(f"Final video saved as {output_path}")

mp4_path = os.path.join(save_folder, "final_video.mp4")

stitle, sstory, sid = get_random_story()

title_audio_path = os.path.join(save_folder, "title_audio.mp3")
story_audio_path = os.path.join(save_folder, "story_audio.mp3")

build_video(stitle, sstory, title_audio_path, story_audio_path, mp4_path)