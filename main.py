import praw
import random
from gtts import gTTS
from dotenv import load_dotenv
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, concatenate_audioclips
from moviepy.video.fx import FadeIn, FadeOut, Resize
import glob
import time
from PIL import Image, ImageDraw, ImageFont
import textwrap
random.seed(time.time())

load_dotenv()

id = os.getenv('REDDIT_CLIENT_ID')
secret = os.getenv('REDDIT_CLIENT_SECRET')
agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

save_folder = "D:/Videos/GeneratedVids"
os.makedirs(save_folder, exist_ok=True)

def handle_comments(submission):
    body = submission.selftext
    submission.comment_sort = "top"
    submission.comments.replace_more(limit=None)
    t20 = submission.comments[:20]
    stories = [com for com in t20 if len(com.body) > 250]
    i = 1
    while len(body) < 1000:
        if not stories:
            return None, None, None
        comment = random.choice(stories)
        stories.remove(comment)
        body += f"\n\n{i}.\n{comment.body}"
        i += 1
    return submission.title, body, submission.id

def get_random_story():
    hostsub = random.choice(['all', 'offmychest', 'nosleep', 'creepypasta', 'shortscarystories', 'AmItheAsshole', 'confession', 'AskReddit'])
    subreddit = reddit.subreddit(hostsub).hot(limit=20)
    print(hostsub)
    submission = random.choice([sub for sub in subreddit])
    if len(submission.selftext) > 9000:
        return None, None, None
    if submission.subreddit.display_name in ['AskReddit', 'AskMen', 'AskWomen']:
        return handle_comments(submission)
    return submission.title, submission.selftext, submission.id
    
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

def generate_title_card_png(
    title_text,
    output_path="titlecard.png",
    width=1560,
    font_path="C:/Windows/Fonts/arial.ttf",
    font_size=110,
    padding=40,
    max_chars_per_line=26
):
    top = Image.open("top.png")
    middle = Image.open("middle.png")
    bottom = Image.open("bottom.png")

    lines = textwrap.wrap(title_text, width=max_chars_per_line, break_long_words=False)
    line_height = font_size + 20
    text_height = line_height * len(lines)

    stretched_middle = middle.resize((width, text_height+80))

    total_height = top.height + stretched_middle.height + bottom.height
    canvas = Image.new("RGBA", (width, total_height))
    canvas.paste(top, (0, 0))
    canvas.paste(stretched_middle, (0, top.height))
    canvas.paste(bottom, (0, top.height + stretched_middle.height))

    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(canvas)
    y = top.height + padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill="white")
        y += line_height

    canvas.save(output_path)
    return output_path

def build_video(stitle, sstory, title_audio_path, story_audio_path, output_path):
    text_to_speech(stitle, title_audio_path)
    text_to_speech(sstory, story_audio_path)

    title_audio = AudioFileClip(title_audio_path)
    story_audio = AudioFileClip(story_audio_path)

    total_length = title_audio.duration + story_audio.duration
    background_gameplay = get_gameplay(choose_vid_folder(),total_length)

    title_card = (ImageClip('./titlecard.png')
                .with_duration(title_audio.duration)
                .with_position('center')
                .with_effects([Resize(0.4), FadeIn(0.3), FadeOut(0.3)]))

    audio = concatenate_audioclips([title_audio, story_audio])

    final_vid = CompositeVideoClip([background_gameplay.with_audio(audio), title_card.with_start(0)])

    final_vid.write_videofile(output_path, codec="libx264",threads=12,bitrate="8000k",fps=30)
    print(f"Final video saved as {output_path}")

mp4_path = os.path.join(save_folder, "final_video.mp4")
stitle = None
while not stitle:
    stitle, sstory, sid = get_random_story()

generate_title_card_png(stitle)

title_audio_path = os.path.join(save_folder, "title_audio.mp3")
story_audio_path = os.path.join(save_folder, "story_audio.mp3")


text_to_speech(stitle, title_audio_path)
text_to_speech(sstory, story_audio_path)
#build_video(stitle, sstory, title_audio_path, story_audio_path, mp4_path)