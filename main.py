import praw
import random
from gtts import gTTS
from dotenv import load_dotenv
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
import glob
import time
random.seed(time.time())

load_dotenv()

id = os.getenv('REDDIT_CLIENT_ID')
secret = os.getenv('REDDIT_CLIENT_SECRET')
agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

def get_random_story():
    hostsub = random.choice(['askreddit', 'stories', 'offmychest', 'nosleep', 'creepypasta', 'Paranormal', 'shortscarystories', 'AmItheAsshole', 'confession'])
    subreddit = reddit.subreddit(hostsub).hot(limit=20)
    print(hostsub)
    try:
        submission = random.choice([sub for sub in subreddit if sub.selftext != ''])
        return submission.title + "\n\n" + submission.selftext
    except IndexError:
        return "No suitable stories found."
    
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save("random_story.mp3")
    print("MP3 saved as random_story")

def choose_vid_folder(root_folder='./Videos'):
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



def build_video(audio_path, video_folder, output_file="final_video.mp4"):
    audio = AudioFileClip(audio_path)
    vid = get_gameplay(video_folder, audio.duration)
    final = vid.with_audio(audio)
    final.write_videofile(output_file, codec="libx264",threads=12,bitrate="8000k",fps=30)
    print(f"Final video saved as {output_file}")

text_to_speech(get_random_story())
build_video("random_story.mp3",choose_vid_folder())

