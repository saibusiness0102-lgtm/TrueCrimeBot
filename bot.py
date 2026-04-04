# ============================================
# ARCHIVE OF ENIGMAS — CINEMATIC BOT
# Ken Burns slideshow | Real images | Docs style
# ============================================

import os
import re
import json
import math
import random
import shutil
import requests
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from gtts import gTTS
from groq import Groq
import feedparser
import wikipedia
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
    ]
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                content = entry.get("summary", "") or entry.get("description", "")
                if len(content) > 300:
                    print(f"✅ RSS story: {entry.title}")
                    return {"title": entry.title, "content": content[:5000], "source": "RSS"}
        except:
            continue
    return None


def fetch_from_wikipedia():
    case = random.choice(config.WIKIPEDIA_CASES)
    try:
        print(f"📖 Wikipedia: {case}")
        page = wikipedia.page(case, auto_suggest=True)
        return {"title": page.title, "content": page.content[:6000], "source": "Wikipedia"}
    except Exception as e:
        print(f"⚠️ Wikipedia fallback: {e}")
        return {
            "title": "The Zodiac Killer",
            "content": "The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s.",
            "source": "Fallback"
        }


def fetch_story():
    print("\n🔍 Step 1: Fetching story...")
    story = fetch_from_rss() if not config.PREFER_WIKIPEDIA else None
    return story or fetch_from_wikipedia()


# ============================================
# STEP 2 - EXTRACT VISUAL KEYWORDS
# ============================================

def extract_visual_keywords(story, metadata):
    """Extract image search terms from the story"""
    title = story["title"].lower()
    content = story["content"].lower()

    # Base atmospheric shots always included
    base_queries = [
        "dark rainy city night cinematic",
        "crime scene police investigation",
        "dark foggy forest mystery",
        "old newspaper crime headline vintage",
        "detective magnifying glass noir",
        "abandoned house mystery dark",
        "police car lights night blue red",
        "court room justice vintage",
        "dark alley fog night",
        "fingerprint crime evidence"
    ]

    # Case-specific queries
    specific_queries = []

    if any(w in title+content for w in ["murder", "kill", "dead", "death", "homicide"]):
        specific_queries += ["crime scene tape police", "forensic investigation dark", "murder mystery noir"]

    if any(w in title+content for w in ["missing", "disappear", "vanish", "gone"]):
        specific_queries += ["missing person poster", "search rescue forest", "empty dark road night"]

    if any(w in title+content for w in ["serial", "killer", "suspect"]):
        specific_queries += ["silhouette dark figure night", "wanted poster vintage", "detective board investigation"]

    if any(w in title+content for w in ["forest", "woods", "mountain", "rural"]):
        specific_queries += ["dark forest fog mystery", "wilderness night eerie"]

    if any(w in title+content for w in ["city", "urban", "street", "downtown"]):
        specific_queries += ["city night rain dark", "urban crime alley"]

    if any(w in title+content for w in ["water", "river", "lake", "ocean", "boat"]):
        specific_queries += ["dark river night fog", "lake mystery eerie"]

    if any(w in title+content for w in ["house", "home", "family", "suburb"]):
        specific_queries += ["suburban house dark night", "house crime scene tape"]

    # Combine — use specific first, then fill with base
    all_queries = specific_queries + base_queries
    return all_queries[:15]  # Max 15 queries


# ============================================
# STEP 3 - FETCH IMAGES FROM PEXELS
# ============================================

def fetch_images(queries, target_count=12):
    """Fetch multiple relevant images from Pexels"""
    print(f"\n🖼️  Step 3a: Fetching {target_count} cinematic images...")

    os.makedirs(os.path.join(config.OUTPUT_FOLDER, "images"), exist_ok=True)
    headers = {"Authorization": config.PEXELS_API_KEY}
    images = []
    used_ids = set()

    for query in queries:
        if len(images) >= target_count:
            break
        try:
            response = requests.get(
                f"https://api.pexels.com/v1/search?query={query}&per_page=3&orientation=landscape",
                headers=headers,
                timeout=10
            )
            photos = response.json().get("photos", [])
            for photo in photos:
                if len(images) >= target_count:
                    break
                if photo["id"] in used_ids:
                    continue
                used_ids.add(photo["id"])

                # Get large image URL
                img_url = photo["src"]["large2x"]
                img_response = requests.get(img_url, timeout=15)
                if img_response.status_code == 200:
                    img_path = os.path.join(config.OUTPUT_FOLDER, "images", f"img_{len(images):03d}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    images.append(img_path)
                    print(f"  ✅ Image {len(images)}: {query[:40]}")
        except Exception as e:
            print(f"  ⚠️ Image fetch error: {e}")
            continue

    print(f"✅ Fetched {len(images)} images!")
    return images


# ============================================
# STEP 4 - GENERATE SCRIPT
# ============================================

def generate_script(story):
    print("\n✍️  Step 2: Generating 15-minute viral script...")
    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""
You are the writer for "Archive of Enigmas" — a top true crime YouTube channel.
Write a COMPLETE 15-minute video script (~2200 words) about this case.

Story Title: {story['title']}
Story Content: {story['content']}

SCRIPT STRUCTURE:

[HOOK]
Most shocking moment. Drop viewer directly into action. 60 seconds.

[INTRO]
"Welcome to Archive of Enigmas — true crime, unsolved mysteries, dark cases. Today's story will leave you questioning everything."

[CHAPTER 1: BACKGROUND]
Set the scene. Who are the victims? Make viewers care.
End with a cliffhanger line.

[CHAPTER 2: THE CRIME]
What happened? Chilling detail. Build tension slowly. 4 minutes.
Add [PAUSE] markers for dramatic effect.

[CHAPTER 3: INVESTIGATION]
Police response, clues, suspects, theories, twists. 4 minutes.

[CHAPTER 4: AFTERMATH]
What happened next? Community impact. 2 minutes.

[ENGAGEMENT]
"Before the final twist — drop your theory in the comments. Do you think [relevant question]? Subscribe for daily cases."

[CHAPTER 5: TWIST/THEORIES]
Most shocking revelation or unanswered question. 2 minutes.

[OUTRO]
"What do YOU think happened? Comment below. Subscribe for daily mysteries."

RULES:
- 2200+ words minimum
- Use "you" to pull viewer in
- Every chapter ends with cliffhanger
- Specific names, dates, places
- Short punchy sentences for drama
- Sound like human storyteller

After script add:
---METADATA---
TITLE: (Clickbait title under 70 chars)
DESCRIPTION: (300 words SEO description with timestamps)
TAGS: (20 tags comma separated)
THUMBNAIL_TEXT: (3-5 shocking words for thumbnail)
THUMBNAIL_MOOD: (dark/red/blue/dramatic)
PINNED_COMMENT: (Engaging question to pin)
CHAPTERS: (YouTube chapter timestamps format, one per line like "0:00 The Shocking Opening")
"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.85
    )

    full_response = response.choices[0].message.content

    if "---METADATA---" in full_response:
        script, metadata_raw = full_response.split("---METADATA---", 1)
    else:
        script, metadata_raw = full_response, ""

    metadata = {}
    current_key = None
    current_val = []

    for line in metadata_raw.strip().split("\n"):
        matched = False
        for key in ["TITLE","DESCRIPTION","TAGS","THUMBNAIL_TEXT","THUMBNAIL_MOOD","PINNED_COMMENT","CHAPTERS"]:
            if line.startswith(f"{key}:"):
                if current_key:
                    metadata[current_key.lower()] = "\n".join(current_val).strip()
                current_key = key
                current_val = [line.replace(f"{key}:", "").strip()]
                matched = True
                break
        if not matched and current_key:
            current_val.append(line)

    if current_key:
        metadata[current_key.lower()] = "\n".join(current_val).strip()

    # Defaults
    metadata.setdefault("title", story["title"])
    metadata.setdefault("description", f"True crime story: {story['title']}")
    metadata.setdefault("tags", "true crime,mystery,unsolved,dark cases")
    metadata.setdefault("thumbnail_text", "SHOCKING CASE")
    metadata.setdefault("thumbnail_mood", "dark")
    metadata.setdefault("pinned_comment", "What do YOU think happened? Drop your theory below! 👇")

    # Build hashtags
    title_lower = story["title"].lower()
    niche_tags = config.NICHE_HASHTAGS.get("default", [])
    for keyword, tags in config.NICHE_HASHTAGS.items():
        if keyword in title_lower:
            niche_tags = tags
            break
    hashtags = " ".join(config.BASE_HASHTAGS + niche_tags)
    metadata["hashtags"] = hashtags

    # Build full description with timestamps + hashtags
    chapters = metadata.get("chapters", "0:00 Introduction\n2:00 The Crime\n6:00 Investigation\n11:00 Aftermath\n14:00 Conclusion")
    full_desc = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters}

🔔 Subscribe for daily true crime → {config.CHANNEL_HANDLE}
👍 Like if this gave you chills
💬 Drop your theory below!

{hashtags}

© {config.CHANNEL_NAME} — Educational purposes only."""

    metadata["full_description"] = full_desc
    metadata["tags_list"] = [t.strip() for t in metadata["tags"].split(",")][:20]

    wc = len(script.split())
    print(f"✅ Script: {wc} words (~{wc//150} mins)")
    return script.strip(), metadata


# ============================================
# STEP 5 - VOICEOVER
# ============================================

def generate_voiceover(script):
    print("\n🎙️  Step 5: Generating voiceover...")

    clean = re.sub(r'\[.*?\]', '', script)
    clean = clean.replace("[PAUSE]", "...").strip()
    clean = re.sub(r'\n{3,}', '\n\n', clean)

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, "voiceover.mp3")

    # Split into chunks
    max_chars = 4800
    chunks = []
    while len(clean) > max_chars:
        split_at = clean.rfind('. ', 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(clean[:split_at+1])
        clean = clean[split_at+1:].strip()
    if clean:
        chunks.append(clean)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        path = os.path.join(config.OUTPUT_FOLDER, f"chunk_{i}.mp3")
        gTTS(text=chunk, lang="en", slow=False).save(path)
        chunk_paths.append(path)
        print(f"  🎙️ Chunk {i+1}/{len(chunks)}")

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], audio_path)
    else:
        # Merge using moviepy AudioFileClip
        clips = [AudioFileClip(p) for p in chunk_paths]
        merged = concatenate_audioclips(clips)
        merged.write_audiofile(audio_path, logger=None)
        for c in clips:
            c.close()

    for p in chunk_paths:
        try:
            os.remove(p)
        except:
            pass

    print("✅ Voiceover done!")
    return audio_path


# ============================================
# STEP 6 - KEN BURNS CINEMATIC ENGINE
# ============================================

def apply_ken_burns(img_path, duration, direction=None):
    """
    Apply Ken Burns effect to an image — slow zoom + pan
    Returns a MoviePy VideoClip
    """
    try:
        pil_img = Image.open(img_path).convert("RGB")
    except:
        # Fallback black image
        pil_img = Image.new("RGB", (1920, 1080), (10, 5, 5))

    # Enhance image for cinematic look
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.2)
    enhancer = ImageEnhance.Color(pil_img)
    pil_img = enhancer.enhance(0.8)  # Slightly desaturate for dark feel

    # Resize to be larger than output for zoom room
    target_w, target_h = 1280, 720
    zoom_factor = 1.25
    work_w = int(target_w * zoom_factor)
    work_h = int(target_h * zoom_factor)

    # Maintain aspect ratio
    img_w, img_h = pil_img.size
    scale = max(work_w / img_w, work_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

    img_array = np.array(pil_img)

    # Random Ken Burns direction
    if direction is None:
        direction = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right", "diagonal"])

    fps = 24
    total_frames = int(duration * fps)

    def make_frame(t):
        progress = t / duration  # 0 to 1

        if direction == "zoom_in":
            # Start wide, zoom in to center
            scale = 1.0 + (0.25 * progress)
            cx, cy = new_w // 2, new_h // 2

        elif direction == "zoom_out":
            # Start close, zoom out
            scale = 1.25 - (0.25 * progress)
            cx, cy = new_w // 2, new_h // 2

        elif direction == "pan_left":
            scale = 1.15
            cx = int(new_w * 0.6 - new_w * 0.2 * progress)
            cy = new_h // 2

        elif direction == "pan_right":
            scale = 1.15
            cx = int(new_w * 0.4 + new_w * 0.2 * progress)
            cy = new_h // 2

        else:  # diagonal
            scale = 1.0 + (0.2 * progress)
            cx = int(new_w * 0.4 + new_w * 0.1 * progress)
            cy = int(new_h * 0.4 + new_h * 0.1 * progress)

        # Calculate crop box
        crop_w = int(target_w / scale)
        crop_h = int(target_h / scale)

        x1 = max(0, min(cx - crop_w // 2, new_w - crop_w))
        y1 = max(0, min(cy - crop_h // 2, new_h - crop_h))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        # Crop and resize to target
        cropped = img_array[y1:y2, x1:x2]
        frame_img = Image.fromarray(cropped).resize((target_w, target_h), Image.LANCZOS)

        return np.array(frame_img)

    clip = VideoClip(make_frame, duration=duration)
    return clip


def create_chapter_card(text, duration=2.5):
    """Create a dramatic chapter title card"""
    def make_frame(t):
        progress = min(t / 0.5, 1.0)  # Fade in over 0.5s
        fade_out = min((duration - t) / 0.5, 1.0) if t > duration - 0.5 else 1.0
        alpha = min(progress, fade_out)

        img = Image.new("RGB", (1280, 720), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Red accent line
        line_width = int(200 * alpha)
        draw.rectangle([(640 - line_width//2, 340), (640 + line_width//2, 343)], fill=(180, 0, 0))

        # Chapter text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 52)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
        except:
            font = font_sm = ImageFont.load_default()

        opacity = int(255 * alpha)
        color = (opacity, opacity, opacity)

        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((1280 - w) // 2, 360), text, font=font, fill=color)

        sub = config.CHANNEL_NAME.upper()
        bbox2 = draw.textbbox((0, 0), sub, font=font_sm)
        w2 = bbox2[2] - bbox2[0]
        draw.text(((1280 - w2) // 2, 300), sub, font=font_sm, fill=(int(140*alpha), 0, 0))

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


def add_cinematic_overlay(clip):
    """Add dark vignette + color grade overlay to a clip"""
    W, H = 1280, 720

    def overlay_frame(t):
        frame = np.zeros((H, W, 3), dtype=np.uint8)

        # Vignette (dark edges)
        for y in range(H):
            for x in range(W):
                dx = (x - W//2) / (W//2)
                dy = (y - H//2) / (H//2)
                dist = math.sqrt(dx*dx + dy*dy)
                vignette = max(0, min(1, 1 - (dist - 0.6) * 1.5))
                darkness = int(60 * (1 - vignette))
                frame[y, x] = [darkness, 0, 0]

        return frame

    # Create a static vignette frame
    vignette_img = Image.new("RGB", (W, H), (0, 0, 0))
    v_draw = ImageDraw.Draw(vignette_img)

    # Draw radial vignette
    for i in range(min(W, H) // 2, 0, -1):
        ratio = 1 - (i / (min(W, H) // 2))
        darkness = int(100 * ratio * ratio)
        v_draw.ellipse(
            [W//2 - i, H//2 - i, W//2 + i, H//2 + i],
            outline=(darkness, 0, 0)
        )

    vignette_array = np.array(vignette_img)
    vignette_clip = ImageClip(vignette_array, duration=clip.duration).set_opacity(0.5)

    return CompositeVideoClip([clip, vignette_clip])


# ============================================
# STEP 7 - ASSEMBLE CINEMATIC VIDEO
# ============================================

def assemble_cinematic_video(audio_path, image_paths, metadata, story):
    print("\n🎬 Step 7: Assembling cinematic documentary video...")

    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    print(f"  ⏱️ Total duration: {total_duration/60:.1f} minutes")
    print(f"  🖼️  Images available: {len(image_paths)}")

    if not image_paths:
        print("⚠️ No images — using dark background fallback")
        image_paths = []

    clips = []

    # ── Opening title card (4 seconds) ──
    opening = create_chapter_card(metadata.get("title", story["title"])[:50], duration=4)
    clips.append(opening)
    time_used = 4.0

    # ── Ken Burns image slideshow ──
    ken_burns_directions = ["zoom_in", "zoom_out", "pan_left", "pan_right", "diagonal"]

    remaining = total_duration - time_used - 3  # 3s for outro card
    if image_paths:
        secs_per_image = remaining / len(image_paths)
        secs_per_image = max(5.0, min(12.0, secs_per_image))  # Between 5-12s per image

        for i, img_path in enumerate(image_paths):
            if time_used >= total_duration - 3:
                break

            img_duration = min(secs_per_image, total_duration - time_used - 3)
            direction = ken_burns_directions[i % len(ken_burns_directions)]

            print(f"  🎞️  Image {i+1}/{len(image_paths)}: {img_duration:.1f}s ({direction})")

            # Ken Burns clip
            kb_clip = apply_ken_burns(img_path, img_duration, direction)

            # Add dark cinematic overlay
            dark_overlay = ColorClip(
                size=(1280, 720), color=(0, 0, 0), duration=img_duration
            ).set_opacity(0.35)

            img_clip = CompositeVideoClip([kb_clip, dark_overlay])

            # Add crossfade transition
            if clips and i > 0:
                img_clip = img_clip.crossfadein(0.8)

            clips.append(img_clip)
            time_used += img_duration

            # Insert chapter card every ~3 images
            if (i + 1) % 3 == 0 and time_used < total_duration - 6:
                chapter_num = (i // 3) + 1
                chapter_names = ["The Background", "The Crime", "The Investigation", "The Aftermath", "The Truth"]
                chapter_name = chapter_names[min(chapter_num - 1, len(chapter_names) - 1)]
                chapter_card = create_chapter_card(f"Chapter {chapter_num}: {chapter_name}", duration=2.5)
                clips.append(chapter_card)
                time_used += 2.5

    else:
        # Fallback: animated dark background with particles effect
        def make_dark_bg(t):
            img = Image.new("RGB", (1280, 720), (5, 0, 0))
            draw = ImageDraw.Draw(img)

            # Animated grain/particles
            rng = np.random.RandomState(int(t * 10))
            for _ in range(30):
                x = rng.randint(0, 1280)
                y = rng.randint(0, 720)
                r = rng.randint(1, 3)
                brightness = rng.randint(40, 80)
                draw.ellipse([x-r, y-r, x+r, y+r], fill=(brightness, 0, 0))

            return np.array(img)

        bg_clip = VideoClip(make_dark_bg, duration=remaining)
        clips.append(bg_clip)
        time_used += remaining

    # ── Outro card (3 seconds) ──
    outro = create_chapter_card("Subscribe for Daily Mysteries 🔴", duration=3)
    clips.append(outro)

    # ── Concatenate all clips ──
    print(f"  🔗 Concatenating {len(clips)} clips...")
    try:
        final_video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print(f"⚠️ Compose method failed: {e}, trying chain...")
        final_video = concatenate_videoclips(clips, method="chain")

    # Trim/extend to match audio exactly
    if final_video.duration > total_duration:
        final_video = final_video.subclip(0, total_duration)
    elif final_video.duration < total_duration:
        # Loop last frame to fill gap
        gap = total_duration - final_video.duration
        last_frame = ImageClip(final_video.get_frame(final_video.duration - 0.1), duration=gap)
        final_video = concatenate_videoclips([final_video, last_frame])

    # Add watermark
    def watermark_frame(t):
        img = Image.new("RGBA", (1280, 40), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((20, 10), f"🔴 {config.CHANNEL_NAME} • Subscribe for daily mysteries", font=font, fill=(200, 200, 200, 140))
        return np.array(img.convert("RGB"))

    watermark = VideoClip(watermark_frame, duration=total_duration)\
        .set_position(("left", "bottom"))\
        .set_opacity(0.45)

    final = CompositeVideoClip([final_video, watermark])
    final = final.set_audio(audio)

    output_path = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
    print("  🎞️  Writing final video...")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast",
        bitrate="3000k",
        logger=None
    )

    print(f"✅ Cinematic video assembled! ({total_duration/60:.1f} mins)")
    return output_path


# ============================================
# STEP 8 - CREATE THUMBNAIL
# ============================================

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 8: Creating viral thumbnail...")

    W, H = 1280, 720
    mood = metadata.get("thumbnail_mood", "dark")

    # Use first fetched image as base if available
    if image_paths:
        try:
            img = Image.open(image_paths[0]).convert("RGB")
            img = img.resize((W, H), Image.LANCZOS)

            # Darken significantly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.35)

            # Desaturate slightly
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.6)
        except:
            img = Image.new("RGB", (W, H), (10, 0, 0))
    else:
        img = Image.new("RGB", (W, H), (10, 0, 0))

    draw = ImageDraw.Draw(img)

    # Mood color tint overlay
    mood_tints = {
        "dark": (20, 0, 0, 60),
        "red": (60, 0, 0, 80),
        "blue": (0, 0, 40, 70),
        "dramatic": (30, 0, 40, 70)
    }
    tint_color = mood_tints.get(mood, mood_tints["dark"])
    tint = Image.new("RGBA", (W, H), tint_color)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, tint).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Vignette
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for i in range(350, 0, -1):
        alpha = int(180 * (1 - i/350) ** 2)
        v_draw.ellipse([W//2-i*2, H//2-i, W//2+i*2, H//2+i], outline=(0,0,0,alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, vignette).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_xl = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 88)
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 56)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 34)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 26)
    except:
        font_xl = font_lg = font_md = font_sm = ImageFont.load_default()

    # Top label
    draw.text((30, 22), "🔴 " + config.CHANNEL_NAME.upper(), font=font_sm, fill=(200, 200, 200))

    # Main thumbnail text
    thumb_text = metadata.get("thumbnail_text", "SHOCKING CASE").upper()
    words = thumb_text.split()
    if len(words) <= 2:
        lines = [thumb_text]
    elif len(words) <= 4:
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:])]

    y = H//2 - (len(lines) * 100)//2 - 20
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font_xl)
        w = bbox[2]-bbox[0]
        x = (W-w)//2

        # Deep shadow
        for s in range(8, 0, -1):
            draw.text((x+s, y+s), line, font=font_xl, fill=(0,0,0))
        # Red glow
        for dx,dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2)]:
            draw.text((x+dx, y+dy), line, font=font_xl, fill=(200,0,0))
        # White main
        draw.text((x, y), line, font=font_xl, fill=(255,255,255))
        y += 102

    # Case subtitle
    subtitle = story["title"][:45] + ("..." if len(story["title"]) > 45 else "")
    bbox = draw.textbbox((0,0), subtitle, font=font_md)
    w = bbox[2]-bbox[0]
    x = (W-w)//2
    draw.text((x+1, y+10+1), subtitle, font=font_md, fill=(0,0,0))
    draw.text((x, y+10), subtitle, font=font_md, fill=(230, 190, 0))

    # Bottom bar
    draw.rectangle([(0, H-58), (W, H)], fill=(12, 0, 0))
    draw.rectangle([(0, H-60), (W, H-58)], fill=(200, 0, 0))
    draw.text((30, H-44), "TRUE CRIME  •  UNSOLVED MYSTERIES  •  DARK CASES", font=font_sm, fill=(160,160,160))

    thumb_path = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")
    img.save(thumb_path, "JPEG", quality=95)
    print("✅ Thumbnail created!")
    return thumb_path


# ============================================
# STEP 9 - UPLOAD TO YOUTUBE
# ============================================

def upload_to_youtube(video_path, thumbnail_path, metadata):
    print("\n📤 Step 9: Uploading to YouTube...")

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

    request_body = {
        "snippet": {
            "title": metadata.get("title", "True Crime Story")[:100],
            "description": metadata.get("full_description", ""),
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

    # Upload thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("✅ Thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail failed: {e}")

    # Pinned comment
    pinned = metadata.get("pinned_comment", "What do you think happened? 👇")
    try:
        comment = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": f"🔴 {pinned}\n\n💬 Drop your theory below — every comment helps!\n🔔 Subscribe for daily mysteries → {config.CHANNEL_HANDLE}"
                        }
                    }
                }
            }
        ).execute()
        print("✅ Pinned comment posted!")
    except Exception as e:
        print(f"⚠️ Comment failed: {e}")

    print(f"\n🎉 LIVE: https://youtube.com/watch?v={video_id}")
    return video_id


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline():
    print("=" * 55)
    print("🚀 ARCHIVE OF ENIGMAS — Cinematic Pipeline")
    print("=" * 55)

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    try:
        # 1. Fetch story
        story = fetch_story()

        # 2. Generate script
        script, metadata = generate_script(story)

        # 3. Extract image keywords
        queries = extract_visual_keywords(story, metadata)

        # 4. Fetch images
        image_paths = fetch_images(queries, target_count=14)

        # 5. Voiceover
        audio_path = generate_voiceover(script)

        # 6. Thumbnail
        thumbnail_path = create_thumbnail(image_paths, metadata, story)

        # 7. Assemble cinematic video
        video_path = assemble_cinematic_video(audio_path, image_paths, metadata, story)

        # 8. Upload
        video_id = upload_to_youtube(video_path, thumbnail_path, metadata)

        print("\n" + "=" * 55)
        print(f"🎉 SUCCESS! https://youtube.com/watch?v={video_id}")
        print(f"📊 Title: {metadata.get('title')}")
        print(f"🖼️  Images used: {len(image_paths)}")
        print(f"🏷️  Tags: {len(metadata.get('tags_list', []))}")
        print("=" * 55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
