# ============================================
# TRUE CRIME BOT - FULL PIPELINE
# Runs on GitHub Actions — No PC needed!
# ============================================

import os
import json
import random
import requests
import textwrap
import feedparser
import wikipedia
from gtts import gTTS
from groq import Groq
from moviepy.editor import *
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config


# ============================================
# STEP 1 - FETCH STORY (RSS + Wikipedia)
# ============================================

def fetch_from_rss():
    rss_feeds = [
        "https://www.crimeonline.com/feed/",
        "https://rss.app/feeds/truecrime.xml",
        "https://www.cbc.ca/cmlink/rss-canada-britishcolumbia"
    ]
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                content = entry.get("summary", "") or entry.get("description", "")
                if len(content) > 200:
                    print(f"✅ RSS story found: {entry.title}")
                    return {
                        "title": entry.title,
                        "content": content[:3000],
                        "source": "RSS",
                        "url": entry.link
                    }
        except:
            continue
    return None


def fetch_from_wikipedia():
    case = random.choice(config.WIKIPEDIA_CASES)
    try:
        print(f"📖 Fetching Wikipedia: {case}")
        page = wikipedia.page(case, auto_suggest=True)
        return {
            "title": page.title,
            "content": page.content[:3000],
            "source": "Wikipedia",
            "url": page.url
        }
    except Exception as e:
        print(f"⚠️ Wikipedia error: {e} — using fallback")
        return {
            "title": "The Zodiac Killer",
            "content": "The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s, who sent taunting letters to police and newspapers.",
            "source": "Fallback",
            "url": ""
        }


def fetch_story():
    print("\n🔍 Step 1: Fetching true crime story...")
    if not config.PREFER_WIKIPEDIA:
        story = fetch_from_rss()
        if story:
            return story
    return fetch_from_wikipedia()


# ============================================
# STEP 2 - GENERATE SCRIPT WITH GROQ (Free!)
# ============================================

def generate_script(story):
    print("\n✍️  Step 2: Generating script with Groq AI...")

    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""
You are a true crime YouTube narrator. Create an engaging 5-minute video script.

Story Title: {story['title']}
Story Content: {story['content']}

Requirements:
- Start with a powerful HOOK (first 15 seconds must grab attention)
- Dramatic, suspenseful narration style
- Use [PAUSE] markers for natural breaks
- Structure: Hook → Background → The Crime → Investigation → Resolution/Twist → Outro
- End with: "Like and subscribe for more true crime stories"

After the script add exactly this separator and metadata:
---METADATA---
TITLE: (catchy YouTube title under 60 characters)
DESCRIPTION: (150 word description with keywords)
TAGS: (10 relevant tags, comma separated)
"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.8
    )

    full_response = response.choices[0].message.content

    if "---METADATA---" in full_response:
        script, metadata_raw = full_response.split("---METADATA---")
    else:
        script = full_response
        metadata_raw = f"TITLE: {story['title']}\nDESCRIPTION: True crime story\nTAGS: true crime,mystery,unsolved"

    metadata = {}
    for line in metadata_raw.strip().split("\n"):
        if line.startswith("TITLE:"):
            metadata["title"] = line.replace("TITLE:", "").strip()
        elif line.startswith("DESCRIPTION:"):
            metadata["description"] = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("TAGS:"):
            metadata["tags"] = [t.strip() for t in line.replace("TAGS:", "").split(",")]

    print(f"✅ Script generated ({len(script.split())} words)")
    return script.strip(), metadata


# ============================================
# STEP 3 - GENERATE VOICEOVER (gTTS - Free!)
# ============================================

def generate_voiceover(script):
    print("\n🎙️  Step 3: Generating voiceover with gTTS...")

    clean_script = script.replace("[PAUSE]", "...")

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, "voiceover.mp3")

    tts = gTTS(
        text=clean_script,
        lang=config.TTS_LANGUAGE,
        slow=config.TTS_SLOW
    )
    tts.save(audio_path)

    print(f"✅ Voiceover saved!")
    return audio_path


# ============================================
# STEP 4 - FETCH BACKGROUND FOOTAGE (Pexels)
# ============================================

def fetch_background_video():
    print("\n🎬 Step 4: Fetching background footage from Pexels...")

    search_terms = ["dark city night", "mystery forest", "rainy street night", "abandoned building"]
    query = random.choice(search_terms)

    headers = {"Authorization": config.PEXELS_API_KEY}
    try:
        response = requests.get(
            f"https://api.pexels.com/videos/search?query={query}&per_page=5",
            headers=headers
        )
        videos = response.json().get("videos", [])
        if videos:
            video_url = random.choice(videos)["video_files"][0]["link"]
            video_path = os.path.join(config.OUTPUT_FOLDER, "background.mp4")
            with requests.get(video_url, stream=True) as r:
                with open(video_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("✅ Background footage downloaded!")
            return video_path
    except Exception as e:
        print(f"⚠️ Pexels error: {e} — using dark background fallback")
    return None


# ============================================
# STEP 5 - ASSEMBLE VIDEO (MoviePy)
# ============================================

def assemble_video(audio_path, background_path, metadata):
    print("\n🎞️  Step 5: Assembling final video...")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if background_path and os.path.exists(background_path):
        bg = VideoFileClip(background_path).without_audio()
        if bg.duration < duration:
            loops = int(duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * loops)
        bg = bg.subclip(0, duration).resize((1920, 1080))
    else:
        bg = ColorClip(size=(1920, 1080), color=(10, 10, 10), duration=duration)

    overlay = ColorClip(
        size=(1920, 1080), color=(0, 0, 0), duration=duration
    ).set_opacity(0.5)

    title_text = metadata.get("title", "True Crime Story")
    title_clip = (
        TextClip(
            textwrap.fill(title_text, 30),
            fontsize=70,
            color="white",
            font="Arial-Bold",
            stroke_color="black",
            stroke_width=2
        )
        .set_duration(5)
        .set_position("center")
        .fadein(1)
        .fadeout(1)
    )

    watermark = (
        TextClip(
            "True Crime Stories",
            fontsize=30,
            color="gray",
            font="Arial"
        )
        .set_duration(duration)
        .set_position(("right", "bottom"))
        .margin(right=20, bottom=20)
    )

    final = CompositeVideoClip([bg, overlay, title_clip, watermark])
    final = final.set_audio(audio)

    output_path = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast"
    )

    print(f"✅ Video assembled!")
    return output_path


# ============================================
# STEP 6 - UPLOAD TO YOUTUBE
# ============================================

def upload_to_youtube(video_path, metadata):
    print("\n📤 Step 6: Uploading to YouTube...")

    # Write client secrets from environment
    secrets_path = os.path.join(config.OUTPUT_FOLDER, "client_secrets.json")
    with open(secrets_path, "w") as f:
        f.write(config.YOUTUBE_CLIENT_SECRETS)

    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, scopes)
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)

    request_body = {
        "snippet": {
            "title": metadata.get("title", "True Crime Story"),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "categoryId": "25"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    ).execute()

    video_id = response.get("id")
    print(f"✅ Uploaded! Watch at: https://youtube.com/watch?v={video_id}")
    return video_id


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline():
    print("=" * 50)
    print("🚀 TRUE CRIME BOT — Starting Pipeline")
    print("=" * 50)

    try:
        story = fetch_story()
        script, metadata = generate_script(story)
        audio_path = generate_voiceover(script)
        background_path = fetch_background_video()
        video_path = assemble_video(audio_path, background_path, metadata)
        upload_to_youtube(video_path, metadata)

        print("\n" + "=" * 50)
        print("🎉 DONE! Video is live on YouTube!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    run_pipeline()
