import praw
import random
from dotenv import load_dotenv
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, concatenate_audioclips, TextClip
from moviepy.video.fx import FadeIn, FadeOut, Resize
import glob
import time
from PIL import Image, ImageDraw, ImageFont
import textwrap
import boto3
from pydub import AudioSegment
from io import BytesIO
import whisper_timestamped as whisper_ts
random.seed(time.time())

load_dotenv()

id = os.getenv('REDDIT_CLIENT_ID')
secret = os.getenv('REDDIT_CLIENT_SECRET')
agent = os.getenv('REDDIT_USER_AGENT')
amazon_id=os.getenv('AMAZON_POLLY_ACCESS')
amazon_secret=os.getenv('AMAZON_POLLY_SECRET')
region='us-east-2'
gameplay_folder = os.getenv('ROOT_GAMEPLAY_FOLDER')
arial_font_location = os.getenv('ARIAL_FONT_LOCATION')
save_folder = os.getenv('SAVE_FOLDER_LOCATION')

polly = boto3.client(
    'polly',
    aws_access_key_id=amazon_id,
    aws_secret_access_key=amazon_secret,
    region_name=region
)

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

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
    hostsub = random.choice(['all', 'offmychest', 'nosleep', 'creepypasta', 'shortscarystories', 'confession', 'AskReddit'])
    subreddit = reddit.subreddit(hostsub).hot(limit=20)
    print(hostsub)
    submission = random.choice([sub for sub in subreddit])
    if len(submission.selftext) > 9000:
        return None, None, None
    if submission.subreddit.display_name in ['AskReddit', 'AskMen', 'AskWomen']:
        return handle_comments(submission)
    return submission.title, submission.selftext, submission.id

def make_phrase_clips(groups, title_length, font_path=arial_font_location):
    clips = []
    for group in groups:
        i = 0
        for word in group["words"]:
            word_text = " ".join([w["text"] for w in group["words"][:i+1]])
            word_start = word["start"]
            word_end = word["end"]
            txt_clip = (TextClip(font=font_path,
                                 text=word_text,
                                 font_size=100,
                                 color='white',
                                 stroke_color='black',
                                 stroke_width=10,
                                 method='label',
                                 duration= word_end - word_start
                                 )
                                 .with_position('center')
                                 .with_start(word_start + title_length))
            i += 1
            clips.append(txt_clip)
    return clips

def transcribe_audio(audio_path):
    model = whisper_ts.load_model("base")
    result = whisper_ts.transcribe(model, audio_path)
    words = []
    for segment in result["segments"]:
        words.extend(segment["words"])
    return words

def group_words(words):
    grouped = []
    i = 0
    while i < len(words):
        start_time = words[i]["start"]
        time = 0
        group = []
        while time < 0.4:
            end_time = words[i]["end"]
            group.append(words[i])
            i += 1
            time = end_time - start_time
            if i >= len(words):
                break
        if not group:
            break
        text = ' '.join([w["text"].strip() for w in group])
        start = group[0]["start"]
        end = group[-1]["end"]
        grouped.append({
            "text": text,
            "start": start,
            "end": end,
            "words": group
        })
    return grouped

def text_to_speech(text, output_path):
    chunks = textwrap.wrap(text, width=2900, break_long_words=False, break_on_hyphens=False)
    combined = AudioSegment.empty()
    i = 1
    for chunk in chunks:
        print(f"🧩 Processing chunk {i}/{len(chunks)}...")
        response = polly.synthesize_speech(
            Text=chunk,
            OutputFormat='pcm',
            VoiceId='Matthew'
        )
        audio_bytes = BytesIO(response["AudioStream"].read())
        audio_chunk = AudioSegment(
            data=audio_bytes.read(),
            sample_width=2,
            frame_rate=16000,
            channels=1
        )
        combined += audio_chunk
        i += 1
    combined.set_frame_rate(44100).set_sample_width(2).set_channels(1).export(output_path, format='wav')
    print(f"✅ Final audio saved as {output_path}")


def choose_vid_folder(root_folder=gameplay_folder):
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
    font_path=arial_font_location,
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
    
    whisper_results = transcribe_audio(story_audio_path)
    groups = group_words(whisper_results)
    subtitles = make_phrase_clips(groups, title_audio.duration)

    audio = concatenate_audioclips([title_audio, story_audio])

    final_vid = CompositeVideoClip([background_gameplay.with_audio(audio), title_card.with_start(0)] + subtitles)

    final_vid.write_videofile(output_path, codec="libx264",threads=12,bitrate="8000k",fps=30)
    print(f"Final video saved as {output_path}")

mp4_path = os.path.join(save_folder, "final_video.mp4")
stitle = None
while not stitle:
    stitle, sstory, sid = get_random_story()

generate_title_card_png(stitle)

title_audio_path = os.path.join(save_folder, "title_audio.wav")
story_audio_path = os.path.join(save_folder, "story_audio.wav")

build_video(stitle, sstory, title_audio_path, story_audio_path, mp4_path)