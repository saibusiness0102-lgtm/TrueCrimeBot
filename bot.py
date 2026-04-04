# ============================================
# ARCHIVE OF ENIGMAS - VIRAL OPTIMIZED BOT
# 15-min videos | Thumbnails | SEO | Polls
# ============================================

import os
import json
import random
import requests
import textwrap
import feedparser
import wikipedia
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from gtts import gTTS
from groq import Groq
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config


# ============================================
# STEP 1 - FETCH STORY
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
                if len(content) > 300:
                    print(f"✅ RSS story found: {entry.title}")
                    return {
                        "title": entry.title,
                        "content": content[:5000],
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
            "content": page.content[:6000],
            "source": "Wikipedia",
            "url": page.url
        }
    except Exception as e:
        print(f"⚠️ Wikipedia error: {e} — using fallback")
        return {
            "title": "The Zodiac Killer",
            "content": "The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s. The killer's identity remains unknown to this day despite an extensive investigation.",
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
# STEP 2 - GENERATE VIRAL SCRIPT (15 MINS)
# ============================================

def generate_script(story):
    print("\n✍️  Step 2: Generating 15-minute viral script...")

    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""
You are the writer for "Archive of Enigmas" — a top true crime YouTube channel with millions of subscribers.
Write a COMPLETE, DETAILED 15-minute video script (~2200 words) about this case.

Story Title: {story['title']}
Story Content: {story['content']}

STRICT SCRIPT STRUCTURE (follow this exactly):

[HOOK - 60 seconds]
Start with the most shocking/disturbing moment of the story. 
Drop the viewer directly into the action. No intro yet.
Example: "The detective had seen hundreds of crime scenes. But nothing prepared him for what he found that October morning..."

[INTRO STING - 15 seconds]
"Welcome to Archive of Enigmas — where we explore true crime, unsolved mysteries, and the darkest corners of human nature. I'm your host, and today's case will leave you questioning everything you thought you knew."

[CHAPTER 1: THE BACKGROUND - 3 minutes]
Set the scene. Who are the victims? What was life like before?
Make viewers care about the people involved.
End with: "But then... everything changed."

[CHAPTER 2: THE CRIME - 4 minutes]  
Describe what happened in chilling detail.
Use atmospheric descriptions. Build tension slowly.
Include specific dates, locations, details.
Add [PAUSE] markers for dramatic effect.

[CHAPTER 3: THE INVESTIGATION - 4 minutes]
How did authorities respond? What clues were found?
What theories emerged? Were there suspects?
Include any twists or unexpected discoveries.

[CHAPTER 4: THE AFTERMATH - 2 minutes]
What happened next? Was anyone caught? 
What impact did this have on the community?
For unsolved cases — what do investigators believe today?

[ENGAGEMENT BREAK - 30 seconds]
"Before we get to the most disturbing part of this story — I want to hear from YOU. 
Drop in the comments: Do you think [insert relevant question about the case]?
And if you're new here — hit that subscribe button. We upload new cases every single day."

[CHAPTER 5: THE TWIST/THEORIES - 2 minutes]
The most shocking revelation, theory, or unanswered question.
What keeps investigators awake at night about this case?

[OUTRO - 60 seconds]
"This case remains one of the most [chilling/bizarre/heartbreaking] in history.
The question of [key mystery] may never be answered.
What do YOU think happened? Let us know in the comments below.
If you found this case fascinating — our next video covers something even darker.
Like this video if it gave you chills, subscribe for daily mysteries, and we'll see you in the shadows."

WRITING RULES:
- Write AT LEAST 2200 words total
- Use second person — "you" — to pull viewer in
- Every chapter must end with a cliffhanger line
- Include specific names, dates, places — details make it real
- Use short punchy sentences for dramatic moments
- Vary sentence length for natural rhythm
- Sound like a human storyteller, not Wikipedia
- Add [PAUSE] for dramatic effect throughout

After the full script, add:
---METADATA---
TITLE: (Clickbait title under 70 chars. Use emotion: "The [Case] That SHOCKED The World" or "Nobody Believed Her... Until It Was Too Late")
DESCRIPTION: (300 word SEO description. Include: case summary, keywords, timestamps, call to action, channel description)
TAGS: (20 specific tags, comma separated)
POLL_QUESTION: (One yes/no or multiple choice question for YouTube community poll)
POLL_OPTIONS: (2-4 poll answer options, pipe separated e.g. Option A|Option B|Option C)
PINNED_COMMENT: (Engaging first comment to pin — ask a question to drive comments)
THUMBNAIL_TEXT: (3-5 word bold text for thumbnail overlay. Shocking/emotional.)
THUMBNAIL_MOOD: (One word: dark/red/blue/dramatic)
"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.85
    )

    full_response = response.choices[0].message.content

    # Split script and metadata
    if "---METADATA---" in full_response:
        script, metadata_raw = full_response.split("---METADATA---", 1)
    else:
        script = full_response
        metadata_raw = ""

    # Parse metadata
    metadata = {}
    for line in metadata_raw.strip().split("\n"):
        for key in ["TITLE", "DESCRIPTION", "TAGS", "POLL_QUESTION",
                    "POLL_OPTIONS", "PINNED_COMMENT", "THUMBNAIL_TEXT", "THUMBNAIL_MOOD"]:
            if line.startswith(f"{key}:"):
                metadata[key.lower()] = line.replace(f"{key}:", "").strip()

    # Fallbacks
    metadata.setdefault("title", story["title"])
    metadata.setdefault("description", f"True crime story about {story['title']}")
    metadata.setdefault("tags", "true crime,mystery,unsolved,dark cases,crime stories")
    metadata.setdefault("thumbnail_text", "SHOCKING CASE")
    metadata.setdefault("thumbnail_mood", "dark")
    metadata.setdefault("poll_question", "Do you think this case will ever be solved?")
    metadata.setdefault("poll_options", "Yes, definitely|Maybe someday|No, never|Already solved")
    metadata.setdefault("pinned_comment", f"What do YOU think really happened? Drop your theory below 👇")

    # Build hashtags
    title_lower = story["title"].lower()
    niche_tags = config.NICHE_HASHTAGS.get("default", [])
    for keyword, tags in config.NICHE_HASHTAGS.items():
        if keyword in title_lower:
            niche_tags = tags
            break

    hashtags = " ".join(config.BASE_HASHTAGS + niche_tags)
    metadata["hashtags"] = hashtags

    # Build full SEO description
    tags_list = [t.strip() for t in metadata["tags"].split(",")][:20]

    # Add timestamps to description
    full_description = f"""{metadata['description']}

⏱️ TIMESTAMPS:
0:00 - The Shocking Opening
1:00 - Introduction
2:00 - Background & Victims  
5:00 - The Crime
9:00 - The Investigation
13:00 - The Aftermath
14:00 - The Twist
15:00 - Conclusion

🔔 Subscribe for daily true crime & unsolved mysteries → {config.CHANNEL_HANDLE}
👍 Like if this case gave you chills
💬 Drop your theory in the comments

{hashtags}

© {config.CHANNEL_NAME} — All content is for educational purposes."""

    metadata["full_description"] = full_description
    metadata["tags_list"] = tags_list

    word_count = len(script.split())
    print(f"✅ Script generated ({word_count} words — ~{word_count//150} mins of content)")
    return script.strip(), metadata


# ============================================
# STEP 3 - GENERATE VOICEOVER
# ============================================

def generate_voiceover(script):
    print("\n🎙️  Step 3: Generating voiceover...")

    clean_script = script.replace("[PAUSE]", "...").replace("[HOOK", "").replace("[INTRO", "")
    # Remove chapter headers from TTS
    import re
    clean_script = re.sub(r'\[.*?\]', '', clean_script)
    clean_script = re.sub(r'\n{3,}', '\n\n', clean_script)

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, "voiceover.mp3")

    # Split into chunks for gTTS (handles long text better)
    max_chars = 5000
    chunks = [clean_script[i:i+max_chars] for i in range(0, len(clean_script), max_chars)]

    audio_clips = []
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(config.OUTPUT_FOLDER, f"chunk_{i}.mp3")
        tts = gTTS(text=chunk, lang=config.TTS_LANGUAGE, slow=False)
        tts.save(chunk_path)
        audio_clips.append(chunk_path)
        print(f"  🎙️ Chunk {i+1}/{len(chunks)} done")

    # Merge audio chunks
    if len(audio_clips) == 1:
        import shutil
        shutil.copy(audio_clips[0], audio_path)
    else:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for clip_path in audio_clips:
            combined += AudioSegment.from_mp3(clip_path)
        combined.export(audio_path, format="mp3")

    # Cleanup chunks
    for clip_path in audio_clips:
        try:
            os.remove(clip_path)
        except:
            pass

    print(f"✅ Voiceover saved!")
    return audio_path


# ============================================
# STEP 3B - FALLBACK VOICEOVER (no pydub)
# ============================================

def generate_voiceover_simple(script):
    print("\n🎙️  Step 3: Generating voiceover (simple mode)...")

    import re
    clean_script = script.replace("[PAUSE]", "...")
    clean_script = re.sub(r'\[.*?\]', '', clean_script)

    # Trim to gTTS limit if needed
    if len(clean_script) > 9000:
        clean_script = clean_script[:9000]
        print("⚠️ Script trimmed to 9000 chars for gTTS")

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, "voiceover.mp3")

    tts = gTTS(text=clean_script, lang=config.TTS_LANGUAGE, slow=False)
    tts.save(audio_path)

    print(f"✅ Voiceover saved!")
    return audio_path


# ============================================
# STEP 4 - FETCH BACKGROUND FOOTAGE
# ============================================

def fetch_background_video(mood="dark"):
    print("\n🎬 Step 4: Fetching background footage...")

    mood_queries = {
        "dark": ["dark city night rain", "abandoned building fog", "dark forest night"],
        "red": ["red crime scene lights", "dark city red light", "blood red sky"],
        "blue": ["blue night city", "ocean dark night", "blue mystery forest"],
        "dramatic": ["stormy dark sky", "lightning storm night", "dramatic dark clouds"]
    }

    queries = mood_queries.get(mood, mood_queries["dark"])
    query = random.choice(queries)

    headers = {"Authorization": config.PEXELS_API_KEY}
    try:
        response = requests.get(
            f"https://api.pexels.com/videos/search?query={query}&per_page=10&min_duration=30",
            headers=headers
        )
        videos = response.json().get("videos", [])
        if videos:
            # Pick longer videos for better loops
            long_videos = [v for v in videos if v.get("duration", 0) >= 15]
            chosen = random.choice(long_videos if long_videos else videos)

            # Get highest quality file
            files = sorted(chosen["video_files"], key=lambda x: x.get("width", 0), reverse=True)
            video_url = files[0]["link"]

            video_path = os.path.join(config.OUTPUT_FOLDER, "background.mp4")
            with requests.get(video_url, stream=True) as r:
                with open(video_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"✅ Background footage downloaded! ({query})")
            return video_path
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")
    return None


# ============================================
# STEP 5 - CREATE VIRAL THUMBNAIL
# ============================================

def create_thumbnail(metadata, story):
    print("\n🖼️  Step 5a: Creating viral thumbnail...")

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    thumb_path = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")

    # YouTube thumbnail size
    W, H = 1280, 720
    mood = metadata.get("thumbnail_mood", "dark")

    # Base gradient background
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Mood-based gradient colors
    mood_colors = {
        "dark": [(20, 0, 0), (60, 10, 10)],
        "red": [(80, 0, 0), (20, 0, 0)],
        "blue": [(0, 10, 40), (0, 30, 80)],
        "dramatic": [(10, 0, 20), (40, 0, 60)]
    }
    colors = mood_colors.get(mood, mood_colors["dark"])

    # Draw gradient
    for y in range(H):
        ratio = y / H
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Add noise texture for cinematic feel
    noise = np.random.randint(0, 15, (H, W, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise)
    img = Image.blend(img, noise_img, 0.05)
    draw = ImageDraw.Draw(img)

    # Red dramatic light sweep
    for i in range(200):
        alpha = int(40 * (1 - i/200))
        x = W // 2 + i * 3
        draw.line([(x, 0), (W // 2, H)], fill=(150, 0, 0))

    # Vignette effect
    vignette = Image.new("RGB", (W, H), (0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    for i in range(200):
        alpha = i
        vignette_draw.rectangle([i, i, W-i, H-i], outline=(alpha, alpha, alpha))
    img = Image.blend(img, vignette, 0.4)
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_xl = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 90)
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 60)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 36)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 28)
    except:
        font_xl = font_lg = font_md = font_sm = ImageFont.load_default()

    # Channel name — top left
    draw.text((30, 20), config.CHANNEL_NAME.upper(), font=font_sm, fill=(200, 200, 200))

    # Main thumbnail text — centered, bold, dramatic
    thumb_text = metadata.get("thumbnail_text", "SHOCKING CASE").upper()
    words = thumb_text.split()

    # Split into max 2 lines
    if len(words) <= 2:
        lines = [thumb_text]
    else:
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]

    # Draw each line centered with shadow
    y_start = H // 2 - (len(lines) * 95) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_xl)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2

        # Multiple shadow layers for depth
        for offset in range(6, 0, -1):
            draw.text((x + offset, y_start + offset), line, font=font_xl, fill=(0, 0, 0))

        # Red outline
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            draw.text((x+dx, y_start+dy), line, font=font_xl, fill=(180, 0, 0))

        # White main text
        draw.text((x, y_start), line, font=font_xl, fill=(255, 255, 255))
        y_start += 100

    # Case name subtitle
    case_name = story["title"][:40] + ("..." if len(story["title"]) > 40 else "")
    bbox = draw.textbbox((0, 0), case_name, font=font_md)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    draw.text((x+1, y_start+15+1), case_name, font=font_md, fill=(0,0,0))
    draw.text((x, y_start+15), case_name, font=font_md, fill=(220, 180, 0))

    # Bottom bar
    draw.rectangle([(0, H-60), (W, H)], fill=(15, 0, 0))
    draw.text((30, H-45), "TRUE CRIME • UNSOLVED MYSTERIES • DARK CASES", font=font_sm, fill=(150, 150, 150))

    # Red accent line
    draw.rectangle([(0, H-62), (W, H-60)], fill=(200, 0, 0))

    # Save
    img.save(thumb_path, "JPEG", quality=95)
    print(f"✅ Thumbnail created!")
    return thumb_path


# ============================================
# STEP 6 - ASSEMBLE VIDEO
# ============================================

def assemble_video(audio_path, background_path, metadata, story):
    print("\n🎞️  Step 6: Assembling final video...")

    audio = AudioFileClip(audio_path)
    duration = audio.duration
    print(f"  ⏱️ Video duration: {duration/60:.1f} minutes")

    # Background
    if background_path and os.path.exists(background_path):
        bg = VideoFileClip(background_path).without_audio()
        if bg.duration < duration:
            loops = int(duration / bg.duration) + 2
            bg = concatenate_videoclips([bg] * loops)
        bg = bg.subclip(0, duration).resize((1280, 720))
    else:
        bg = ColorClip(size=(1280, 720), color=(8, 0, 0), duration=duration)

    # Dark overlay (heavier for readability)
    overlay = ColorClip(size=(1280, 720), color=(0,0,0), duration=duration).set_opacity(0.6)

    # PIL-based title card (first 6 seconds)
    def make_title_frame(t):
        img = Image.new("RGB", (1280, 720), (5, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 58)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 30)
            font_channel = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
        except:
            font_title = font_sub = font_channel = ImageFont.load_default()

        # Channel name top
        draw.text((30, 20), config.CHANNEL_NAME.upper(), font=font_channel, fill=(180, 180, 180))

        # Title word wrap
        title = metadata.get("title", story["title"])
        words = title.split()
        lines, current = [], ""
        for word in words:
            if len(current + word) < 32:
                current += word + " "
            else:
                lines.append(current.strip())
                current = word + " "
        if current:
            lines.append(current.strip())

        y = 720//2 - (len(lines)*70)//2
        for line in lines:
            bbox = draw.textbbox((0,0), line, font=font_title)
            w = bbox[2]-bbox[0]
            x = (1280-w)//2
            # Shadow
            draw.text((x+3, y+3), line, font=font_title, fill=(0,0,0))
            # Red outline
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((x+dx, y+dy), line, font=font_title, fill=(160,0,0))
            # White text
            draw.text((x, y), line, font=font_title, fill=(255,255,255))
            y += 72

        # Tagline
        tagline = "TRUE CRIME • UNSOLVED MYSTERIES"
        bbox = draw.textbbox((0,0), tagline, font=font_sub)
        w = bbox[2]-bbox[0]
        draw.text(((1280-w)//2, 720-80), tagline, font=font_sub, fill=(180, 0, 0))

        # Bottom watermark
        wm = config.CHANNEL_HANDLE
        bbox = draw.textbbox((0,0), wm, font=font_channel)
        w = bbox[2]-bbox[0]
        draw.text((1280-w-20, 720-35), wm, font=font_channel, fill=(120,120,120))

        return np.array(img)

    # PIL-based lower-third watermark (subtle, throughout video)
    def make_watermark_frame(t):
        img = Image.new("RGBA", (1280, 60), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 22)
        except:
            font = ImageFont.load_default()
        draw.text((20, 18), f"🔴 {config.CHANNEL_NAME}  •  Subscribe for daily mysteries", font=font, fill=(200,200,200,160))
        return np.array(img.convert("RGB"))

    title_clip = VideoClip(make_title_frame, duration=6)
    watermark_clip = VideoClip(make_watermark_frame, duration=duration).set_position(("left", "bottom")).set_opacity(0.5)

    # Combine
    final = CompositeVideoClip([bg, overlay, title_clip.set_start(0), watermark_clip])
    final = final.set_audio(audio)

    output_path = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast",
        bitrate="2000k"
    )

    print(f"✅ Video assembled! ({duration/60:.1f} mins)")
    return output_path


# ============================================
# STEP 7 - UPLOAD TO YOUTUBE WITH FULL SEO
# ============================================

def upload_to_youtube(video_path, thumbnail_path, metadata):
    print("\n📤 Step 7: Uploading to YouTube with full SEO...")

    token_data = json.loads(config.YOUTUBE_TOKEN)
    credentials = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes")
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        print("🔄 Token refreshed!")

    youtube = build("youtube", "v3", credentials=credentials)

    # Upload video
    request_body = {
        "snippet": {
            "title": metadata.get("title", "True Crime Story")[:100],
            "description": metadata.get("full_description", metadata.get("description", "")),
            "tags": metadata.get("tags_list", [])[:500],
            "categoryId": "25",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    video_response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    ).execute()

    video_id = video_response.get("id")
    print(f"✅ Video uploaded! ID: {video_id}")

    # Upload custom thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("✅ Custom thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail upload failed: {e}")

    # Add pinned comment
    pinned = metadata.get("pinned_comment", "What do YOU think happened? Drop your theory! 👇")
    try:
        comment_response = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": f"🔴 {pinned}\n\n💬 Every theory is welcome — drop it below!\n\n🔔 Subscribe for a new dark case EVERY DAY → {config.CHANNEL_HANDLE}"
                        }
                    }
                }
            }
        ).execute()

        comment_id = comment_response["snippet"]["topLevelComment"]["id"]

        # Pin the comment
        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="published"
        ).execute()
        print("✅ Pinned comment added!")
    except Exception as e:
        print(f"⚠️ Comment failed: {e}")

    print(f"\n🎉 LIVE at: https://youtube.com/watch?v={video_id}")
    return video_id


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline():
    print("=" * 55)
    print("🚀 ARCHIVE OF ENIGMAS — Viral Pipeline Starting")
    print("=" * 55)

    try:
        # Step 1: Fetch story
        story = fetch_story()

        # Step 2: Generate viral 15-min script
        script, metadata = generate_script(story)

        # Step 3: Voiceover
        try:
            audio_path = generate_voiceover(script)
        except Exception as e:
            print(f"⚠️ pydub not available, using simple mode: {e}")
            audio_path = generate_voiceover_simple(script)

        # Step 4: Background footage
        mood = metadata.get("thumbnail_mood", "dark")
        background_path = fetch_background_video(mood)

        # Step 5: Thumbnail
        thumbnail_path = create_thumbnail(metadata, story)

        # Step 6: Assemble video
        video_path = assemble_video(audio_path, background_path, metadata, story)

        # Step 7: Upload with full SEO
        video_id = upload_to_youtube(video_path, thumbnail_path, metadata)

        print("\n" + "=" * 55)
        print(f"🎉 SUCCESS! Video live: https://youtube.com/watch?v={video_id}")
        print(f"📊 Title: {metadata.get('title', 'N/A')}")
        print(f"🏷️  Tags: {len(metadata.get('tags_list', []))} tags added")
        print(f"🖼️  Custom thumbnail: uploaded")
        print(f"📌 Pinned comment: added")
        print("=" * 55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    run_pipeline()
