import praw
import random
from gtts import gTTS
from dotenv import load_dotenv
import os

load_dotenv()

id = os.getenv('REDDIT_CLIENT_ID')
secret = os.getenv('REDDIT_CLIENT_SECRET')
agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent)

def get_random_story():
    hostsub = random.choice(['askreddit', 'stories', 'offmychest', 'nosleep', 'creepypasta', 'Paranormal', 'shortscarystories'])
    submissions = reddit.subreddit(hostsub).hot(limit=20)
    try:
        submission = random.choice([sub for sub in submissions if sub.selftext != ''])
        return submission.title + "\n\n" + submission.selftext
    except IndexError:
        return "No suitable stories found."
    
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save("random_story.mp3")
    print("MP3 saved as random_story")

text_to_speech(get_random_story())