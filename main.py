import praw
import random
from dotenv import load_dotenv
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, concatenate_audioclips, TextClip, CompositeAudioClip
from moviepy.video.fx import FadeIn, FadeOut, Resize
import glob
import time
from PIL import Image, ImageDraw, ImageFont
import textwrap
import boto3
from pydub import AudioSegment
from io import BytesIO
import whisper_timestamped as whisper_ts
import re
from pydub.effects import speedup
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle
from datetime import datetime, timedelta, timezone
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
bad_words  = os.getenv("BAD_WORDS", "").split(",")

polly = boto3.client(
    'polly',
    aws_access_key_id=amazon_id,
    aws_secret_access_key=amazon_secret,
    region_name=region
)

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

os.makedirs(save_folder, exist_ok=True)

scopes = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", scopes
            )
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_video(video_path, title, description, category_id, privacy_status, upload_time):
    youtube = authenticate_youtube()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["redditstories", "stories", "satisfying", "minecraft"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    if privacy_status == "private" and upload_time:
        body["status"]["publishAt"] = upload_time
        print(f"⏰ Scheduled for: {upload_time}")

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    
    print(f"✅ Upload complete: https://youtube.com/watch?v={response['id']}")

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

def censor(text, bad_roots):
    pattern = re.compile(
        r'\w*(' + '|'.join(re.escape(root) for root in bad_roots) + r')\w*',
        re.IGNORECASE
    )

    def censor_match(m):
        word = m.group()
        for root in bad_roots:
            index = word.lower().find(root)
            if index != -1:
                censored = (
                    word[:index] +  # prefix
                    word[index] + '*' * (len(root) - 1) +  # censored root
                    word[index + len(root):]  # suffix
                )
                return censored
        return word

    return pattern.sub(censor_match, text)

def get_random_story(used_ids_path):
    if not os.path.exists(used_ids_path):
        open(used_ids_path, 'w').close()
    with open(used_ids_path, 'r') as f:
        used_ids = set(line.strip() for line in f.readlines())
    hostsub = random.choice(['nosleep', 'offmychest', 'creepypasta', 'shortscarystories', 'confession', 'AskReddit', 'TrueOffMyChest', 'TIFU'])
    subreddit = reddit.subreddit(hostsub).top(limit=20, time_filter='month')
    print(hostsub)
    submission = random.choice([sub for sub in subreddit])
    if len(submission.selftext) > 15000 or submission.stickied or submission.id in used_ids or submission.over_18:
        return None, None, None
    if submission.subreddit.display_name in ['AskReddit', 'AskMen', 'AskWomen']:
        return handle_comments(submission)
    elif submission.selftext < 800:
        return None, None, None
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
        while time < 0.35:
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
    combined = speedup(combined, 1.1)
    combined = combined.set_frame_rate(44100).set_sample_width(2).set_channels(1)
    combined.export(output_path, format='wav')
    print(f"✅ Final audio saved as {output_path}")

def get_music(length, path='D:/Videos/BackgroundG/backmusic.mp3'):
    clips = []
    total = 0
    while total < length:
        clip = AudioFileClip(path).with_volume_scaled(0.06)
        clips.append(clip)
        total += clip.duration
    final = concatenate_audioclips(clips).subclipped(0, length)
    return final

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

def segment_by_rules(words, title_duration):
    parts = []
    i = 0
    while i < len(words):
        start = words[i]['start']
        remain = words[i:]
        end = remain[-1]['end']
        time_left = end - start

        if time_left > 240 - title_duration:
            cutoff = start + 180 - title_duration - 2
        elif time_left >= 180 - title_duration - 2:
            cutoff = start + 120
        else:
            cutoff = end
        
        segment_words = []
        while i < len(words) and words[i]['end'] <= cutoff:
            segment_words.append(words[i])
            i += 1
        parts.append(segment_words)
        print(f"added {i} words in this segment")
    print(f"there are {len(parts)} segments")
    return parts

def export_audio_segments(segments, full_story, output_dir):
    output_paths = []
    i = 0
    for words in segments:
        start_ms = 0 if i == 0 else int(words[0]['start'] * 1000)
        end_ms = int(words[-1]['end'] * 1000)
        chunk = full_story[start_ms:] if i == len(segments) - 1 else full_story[start_ms:end_ms]
        path = os.path.join(output_dir, f"story_audio{i}.wav")
        chunk.export(path, format="wav")
        output_paths.append(path)
        i += 1
    return output_paths

def build_video(title_audio_path, story_audio_path, output_path):
    title_audio = AudioFileClip(title_audio_path)
    story_audio = AudioFileClip(story_audio_path)

    total_length = title_audio.duration + story_audio.duration
    background_gameplay = get_gameplay(choose_vid_folder(),total_length)
    music = get_music(total_length)

    title_card = (ImageClip('./titlecard.png')
                .with_duration(title_audio.duration)
                .with_position('center')
                .with_effects([Resize(0.4), FadeIn(0.3), FadeOut(0.3)]))
    
    whisper_results = transcribe_audio(story_audio_path)
    groups = group_words(whisper_results)
    subtitles = make_phrase_clips(groups, title_audio.duration)

    audio = concatenate_audioclips([title_audio, story_audio])
    final_audio = CompositeAudioClip([audio, music])

    final_vid = CompositeVideoClip([background_gameplay.with_audio(final_audio), title_card.with_start(0)] + subtitles)

    final_vid.write_videofile(output_path, codec="libx264",threads=12,bitrate="8000k",fps=30)
    print(f"Final video saved as {output_path}")

def truncate_title(title, max_length = 100):
    title = title.strip()
    if len(title) <= max_length:
        return title
    
    cutoff = title[:max_length]
    if " " in cutoff:
        cutoff = cutoff.rsplit(" ", 1)[0]

    return cutoff

def finalize(title, story, title_audio_path, fulls_audio_path, save_folder):
    text_to_speech(title, title_audio_path)
    text_to_speech(story, fulls_audio_path)
    title_audio = AudioSegment.from_wav(title_audio_path)
    story_audio = AudioSegment.from_wav(story_audio_path)
    story_words = transcribe_audio(story_audio_path)
    segments = segment_by_rules(story_words, title_audio.duration_seconds)
    audio_paths = export_audio_segments(segments, story_audio, save_folder)

    video_paths = []
    i = 0
    while i < len(segments):
        part_audio_path = audio_paths[i]
        part_title = f"{('Part ' + str(i+1) + ': ') if i > 0 else ''}{title}"
        yttitle = truncate_title(part_title)
        generate_title_card_png(part_title)
        part_output_path = os.path.join(save_folder, f"video_part{i+1}.mp4")
        build_video(title_audio_path, part_audio_path, part_output_path)
        video_paths.append((part_output_path, yttitle))
        i += 1

    i = 0
    for (vpath, vtitle) in video_paths:
        privacy = "public" if i == 0 else "private"
        uploadt = None
        hours = 12*i
        if i != 0:
            uploadt = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")

        print(f"\n📝 Uploading {vtitle}...")
        upload_video(vpath, vtitle, title, "22", privacy, uploadt)
        i += 1

stitle = None
used_ids_path = "used_ids.txt"
attempts = 0
while not stitle and attempts < 5:
    stitle, sstory, sid = get_random_story(used_ids_path)
    attempts += 1

stitle = censor(stitle, bad_words)
sstory = censor(sstory, bad_words)

title_audio_path = os.path.join(save_folder, "title_audio.wav")
story_audio_path = os.path.join(save_folder, "story_audio.wav")

finalize(stitle, sstory, title_audio_path, story_audio_path, save_folder)

with open(used_ids_path, "a") as f:
    f.write(sid + "\n")