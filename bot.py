# ============================================
# ARCHIVE OF ENIGMAS — DOCUMENTARY BOT v5
# ElevenLabs voice | Auto Shorts | 3 thumbnail styles
# Topic rotation | Title diversity guard | 6 sources
# ============================================

import os
import re
import json
import math
import random
import shutil
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
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
# TITLE & TOPIC DIVERSITY GUARD
# Prevents repeating same-type titles/topics
# ============================================

HISTORY_FILE = "upload_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"recent_titles": [], "recent_topics": [], "recent_keywords": []}

def save_history(h):
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)

def update_history(title, topic_type, keywords):
    h = load_history()
    h["recent_titles"] = ([title] + h["recent_titles"])[:20]
    h["recent_topics"] = ([topic_type] + h["recent_topics"])[:10]
    h["recent_keywords"] = (keywords + h["recent_keywords"])[:30]
    save_history(h)

def is_too_similar(title, topic_type):
    h = load_history()
    # Block same topic type appearing more than twice in last 5
    recent5 = h["recent_topics"][:5]
    if recent5.count(topic_type) >= 2:
        print(f"  ⚠️  Topic '{topic_type}' appeared {recent5.count(topic_type)}x in last 5. Skipping.")
        return True
    # Block near-duplicate titles (same first 4 words)
    new_words = title.lower().split()[:4]
    for old_title in h["recent_titles"][:10]:
        old_words = old_title.lower().split()[:4]
        if new_words == old_words:
            print(f"  ⚠️  Title too similar to recent: '{old_title}'. Skipping.")
            return True
    return False

def detect_topic_type(text):
    text = text.lower()
    if any(w in text for w in ["missing", "disappear", "vanish"]): return "missing"
    if any(w in text for w in ["serial", "killer", "spree"]): return "serial"
    if any(w in text for w in ["murder", "homicide", "kill", "stab"]): return "murder"
    if any(w in text for w in ["theft", "heist", "robbery", "stolen"]): return "heist"
    if any(w in text for w in ["cult", "sect", "ritual"]): return "cult"
    if any(w in text for w in ["unsolved", "mystery", "unknown", "unidentified"]): return "unsolved"
    if any(w in text for w in ["cold case", "decades", "years later"]): return "coldcase"
    if any(w in text for w in ["conspiracy", "cover", "government"]): return "conspiracy"
    return "other"


# ============================================
# STEP 1 — FETCH STORY (6 sources with rotation)
# ============================================

def fetch_from_rss():
    rss_feeds = [
        "https://www.crimeonline.com/feed/",
        "https://www.oxygen.com/rss.xml",
        "https://www.investigationdiscovery.com/feed",
        "https://www.truecrimeobsessed.com/feed",
        "https://abcnews.go.com/US/feed",
        "https://feeds.simplecast.com/xl36XBC2",  # Crime Junkie podcast RSS
    ]
    random.shuffle(rss_feeds)  # Rotate sources
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:10]
            random.shuffle(entries)  # Don't always pick the first entry
            for entry in entries:
                content = entry.get("summary", "") or entry.get("description", "")
                if len(content) > 300:
                    topic = detect_topic_type(entry.title + " " + content)
                    if not is_too_similar(entry.title, topic):
                        print(f"✅ RSS story: {entry.title}")
                        return {"title": entry.title, "content": content[:5000], "source": "RSS", "topic": topic}
        except Exception as e:
            print(f"  ⚠️ RSS {feed_url[:40]}: {e}")
            continue
    return None


def fetch_from_wikipedia():
    h = load_history()
    used_keywords = set(h.get("recent_keywords", []))

    # Expanded and diverse case list
    cases = [
        # Unsolved / mysterious
        "Zodiac Killer", "Jack the Ripper", "DB Cooper", "Black Dahlia murder",
        "Tamam Shud case", "Dyatlov Pass incident", "Isdal Woman",
        "Boy in the box Philadelphia", "Lyle Stevik", "Taman Shud case",
        "Beaumont children disappearance", "Springfield Three",
        "Villisca axe murders", "Max Headroom broadcast intrusion",
        "Hinterkaifeck murders", "Sodder children disappearance",
        "Axeman of New Orleans", "Cleveland torso murderer",
        "Circleville letters", "Taman Shud case",
        # Serial killers
        "Golden State Killer", "Ted Bundy", "Jeffrey Dahmer", "John Wayne Gacy",
        "Aileen Wuornos", "BTK killer", "Dennis Rader", "Gary Ridgway",
        "Samuel Little", "Ed Kemper", "Richard Ramirez", "Dean Corll",
        "Andrei Chikatilo", "Pedro Lopez", "Luis Garavito", "Harold Shipman",
        "John Christie murderer", "Peter Sutcliffe",
        # Famous murder cases
        "Lizzie Borden", "JonBenet Ramsey", "Tylenol murders", "OJ Simpson trial",
        "Sam Sheppard murder case", "Emmett Till", "Scott Peterson case",
        "Laci Peterson", "Amanda Knox", "Steven Avery", "Brendan Dassey",
        "West Memphis Three", "Casey Anthony case", "Phil Spector murder",
        # Heists / crimes
        "Isabella Stewart Gardner Museum theft",
        "Great Train Robbery 1963", "Antwerp diamond heist",
        "Paris Museum heist", "D.B. Cooper hijacking",
        # Cult / conspiracy
        "Jonestown massacre", "Heaven's Gate cult",
        "NXIVM cult", "People's Temple", "Aum Shinrikyo",
        # Modern cases
        "Gabby Petito case", "Delphi murders", "Chris Watts murders",
        "Watts family murders",
    ]

    # Filter out recently used
    available = [c for c in cases if c.lower() not in used_keywords]
    if not available:
        available = cases  # Reset if all used
    random.shuffle(available)

    for case in available[:5]:  # Try up to 5
        try:
            topic = detect_topic_type(case)
            if is_too_similar(case, topic):
                continue
            print(f"📖 Wikipedia: {case}")
            page = wikipedia.page(case, auto_suggest=True)
            return {
                "title": page.title,
                "content": page.content[:6000],
                "source": "Wikipedia",
                "topic": topic
            }
        except Exception as e:
            print(f"  ⚠️ Wikipedia '{case}': {e}")
            continue

    # Final fallback
    return {
        "title": "The Zodiac Killer",
        "content": "The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s.",
        "source": "Fallback",
        "topic": "unsolved"
    }


def fetch_story():
    print("\n🔍 Step 1: Fetching story...")
    story = fetch_from_rss() if not config.PREFER_WIKIPEDIA else None
    return story or fetch_from_wikipedia()


# ============================================
# STEP 2 — EXTRACT KEYWORDS
# ============================================

def extract_keywords(story):
    title   = story["title"].lower()
    content = story["content"].lower()

    image_queries = [
        "crime scene tape dark night", "detective noir shadow investigation",
        "old newspaper crime headline vintage", "dark foggy forest mystery",
        "fingerprint forensic evidence closeup", "abandoned house dark night",
        "silhouette dark figure mystery", "courtroom justice vintage dark",
        "wanted poster vintage crime", "dark alley rain night cinematic",
        "candlelight dark room mystery", "old photograph vintage sepia dark",
        "magnifying glass detective clue", "police badge dark dramatic",
        "prison bars dark shadow",
    ]

    video_queries = [
        "dark rainy city night", "police car lights night", "fog forest dark eerie",
        "rain window dark night", "storm lightning dramatic dark",
        "dark ocean waves night", "city traffic night rain",
        "smoke dark dramatic", "fire dark night dramatic", "dark road night driving",
    ]

    if any(w in title + content for w in ["murder", "kill", "dead", "homicide"]):
        image_queries = ["crime scene investigation police", "forensic dark dramatic", "murder mystery detective noir"] + image_queries
        video_queries = ["police siren lights night", "crime scene investigation dark", "forensic lab dramatic"] + video_queries

    if any(w in title + content for w in ["missing", "disappear", "vanish"]):
        image_queries = ["missing person poster dark", "search party flashlight", "empty road dark night"] + image_queries
        video_queries = ["search rescue forest night", "flashlight dark forest", "empty road fog night"] + video_queries

    if any(w in title + content for w in ["serial", "killer"]):
        image_queries = ["detective board suspects investigation", "prison dark corridor", "shadow figure dark"] + image_queries
        video_queries = ["dark corridor dramatic", "prison cell dramatic", "shadow walking dark"] + video_queries

    if any(w in title + content for w in ["forest", "woods", "rural", "mountain"]):
        image_queries = ["dark forest fog eerie trees", "mist forest mystery"] + image_queries
        video_queries = ["forest fog dramatic dark", "dark woods eerie"] + video_queries

    if any(w in title + content for w in ["water", "river", "lake", "ocean"]):
        image_queries = ["dark lake night eerie", "river fog mystery"] + image_queries
        video_queries = ["dark water lake night", "river fog dramatic"] + video_queries

    random.shuffle(image_queries)
    random.shuffle(video_queries)
    return image_queries[:18], video_queries[:12]


# ============================================
# STEP 3 — FETCH IMAGES
# ============================================

def fetch_images(queries, target=18):
    print(f"\n📸 Fetching {target} cinematic images...")
    img_dir = os.path.join(config.OUTPUT_FOLDER, "images")
    if os.path.exists(img_dir): shutil.rmtree(img_dir)
    os.makedirs(img_dir, exist_ok=True)

    headers  = {"Authorization": config.PEXELS_API_KEY}
    images   = []
    used_ids = set()

    for query in queries:
        if len(images) >= target: break
        try:
            resp = requests.get(
                f"https://api.pexels.com/v1/search?query={query}&per_page=3&orientation=landscape",
                headers=headers, timeout=10)
            photos = resp.json().get("photos", [])
            for photo in photos:
                if len(images) >= target: break
                if photo["id"] in used_ids: continue
                used_ids.add(photo["id"])
                r = requests.get(photo["src"]["large2x"], timeout=15)
                if r.status_code == 200:
                    path = os.path.join(img_dir, f"img_{len(images):03d}.jpg")
                    with open(path, "wb") as f: f.write(r.content)
                    images.append(path)
                    print(f"  📸 Image {len(images)}: {query[:38]}")
        except Exception as e:
            print(f"  ⚠️ Image error: {e}")

    print(f"✅ {len(images)} images fetched!")
    return images


# ============================================
# STEP 4 — FETCH VIDEOS
# ============================================

def fetch_videos(queries, target=10):
    print(f"\n🎥 Fetching {target} atmospheric video clips...")
    vid_dir  = os.path.join(config.OUTPUT_FOLDER, "videos")
    if os.path.exists(vid_dir): shutil.rmtree(vid_dir)
    os.makedirs(vid_dir, exist_ok=True)

    headers  = {"Authorization": config.PEXELS_API_KEY}
    videos   = []
    used_ids = set()

    for query in queries:
        if len(videos) >= target: break
        try:
            resp = requests.get(
                f"https://api.pexels.com/videos/search?query={query}&per_page=3&min_duration=5&max_duration=25",
                headers=headers, timeout=10)
            items = resp.json().get("videos", [])
            for item in items:
                if len(videos) >= target: break
                if item["id"] in used_ids: continue
                used_ids.add(item["id"])
                files = sorted(item["video_files"], key=lambda x: x.get("width", 0), reverse=True)
                chosen = next((f for f in files if f.get("width", 0) <= 1920), files[0] if files else None)
                if not chosen: continue
                path = os.path.join(vid_dir, f"vid_{len(videos):03d}.mp4")
                r = requests.get(chosen["link"], stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    videos.append({"path": path, "duration": item.get("duration", 10)})
                    print(f"  🎥 Video {len(videos)}: {query[:38]} ({item.get('duration', 0)}s)")
        except Exception as e:
            print(f"  ⚠️ Video error: {e}")

    print(f"✅ {len(videos)} video clips fetched!")
    return videos


# ============================================
# STEP 5 — GENERATE SCRIPT + SHORTS HOOK
# ============================================

def generate_script(story):
    print("\n✍️  Step 5: Generating scripts...")
    h = load_history()
    recent_titles_str = ", ".join(h["recent_titles"][:5]) if h["recent_titles"] else "none yet"

    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""You are the writer for "Archive of Enigmas" — a top true crime YouTube channel.
Write a COMPLETE 15-minute video script (2200+ words) about this case.

Story Title: {story['title']}
Story Content: {story['content']}

RECENT TITLES USED (DO NOT repeat these patterns): {recent_titles_str}

STRUCTURE:
[HOOK] Most shocking/unexpected moment. 60 seconds.
[INTRO] Welcome to Archive of Enigmas intro.
[CHAPTER 1: BACKGROUND] Set scene, victims. 3 mins. End with cliffhanger.
[CHAPTER 2: THE CRIME] What happened. 4 mins. Add [PAUSE] markers.
[CHAPTER 3: INVESTIGATION] Police, clues, suspects. 4 mins.
[CHAPTER 4: AFTERMATH] What happened next. 2 mins.
[ENGAGEMENT] Ask viewers to comment and subscribe.
[CHAPTER 5: TWIST] Shocking revelation. 2 mins.
[OUTRO] Subscribe CTA.

RULES: 2200+ words. Use "you". Cliffhanger every chapter. Specific details. Human storyteller.
DO NOT use passive robotic language. Write like a gripping podcast host.

Then write a SHORTS_SCRIPT (60 seconds max, ~150 words):
---SHORTS_SCRIPT---
(Gripping 60-second version of the most shocking part. Hook in first 3 words.
Fast-paced. End with "follow for more". No intro music cue.)
---END_SHORTS---

Then:
---METADATA---
TITLE: (Unique clickbait title under 70 chars — NOT similar to: {recent_titles_str})
DESCRIPTION: (300 word SEO description)
TAGS: (20 tags comma separated)
THUMBNAIL_TEXT: (3-5 shocking words)
THUMBNAIL_MOOD: (dark/red/split/face)
THUMBNAIL_STYLE: (1, 2, or 3 — pick the most compelling for this case)
PINNED_COMMENT: (Engaging question)
CHAPTERS: (YouTube timestamps one per line like "0:00 The Opening")
"""

    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4500, temperature=0.85)

    full = resp.choices[0].message.content

    # Extract shorts script
    shorts_script = ""
    if "---SHORTS_SCRIPT---" in full and "---END_SHORTS---" in full:
        s_start = full.index("---SHORTS_SCRIPT---") + len("---SHORTS_SCRIPT---")
        s_end   = full.index("---END_SHORTS---")
        shorts_script = full[s_start:s_end].strip()
        full = full[:full.index("---SHORTS_SCRIPT---")] + full[full.index("---END_SHORTS---") + len("---END_SHORTS---"):]

    # Extract metadata
    if "---METADATA---" in full:
        script, meta_raw = full.split("---METADATA---", 1)
    else:
        script, meta_raw = full, ""

    metadata = {}
    cur_key, cur_val = None, []
    for line in meta_raw.strip().split("\n"):
        matched = False
        for key in ["TITLE", "DESCRIPTION", "TAGS", "THUMBNAIL_TEXT", "THUMBNAIL_MOOD",
                    "THUMBNAIL_STYLE", "PINNED_COMMENT", "CHAPTERS"]:
            if line.startswith(f"{key}:"):
                if cur_key: metadata[cur_key.lower()] = "\n".join(cur_val).strip()
                cur_key, cur_val = key, [line.replace(f"{key}:", "").strip()]
                matched = True; break
        if not matched and cur_key: cur_val.append(line)
    if cur_key: metadata[cur_key.lower()] = "\n".join(cur_val).strip()

    metadata.setdefault("title", story["title"])
    metadata.setdefault("description", f"True crime: {story['title']}")
    metadata.setdefault("tags", "true crime,mystery,unsolved,dark cases")
    metadata.setdefault("thumbnail_text", "SHOCKING CASE")
    metadata.setdefault("thumbnail_mood", "dark")
    metadata.setdefault("thumbnail_style", "1")
    metadata.setdefault("pinned_comment", "What do YOU think happened? Drop your theory! 👇")

    title_lower = story["title"].lower()
    niche = config.NICHE_HASHTAGS.get("default", [])
    for kw, tags in config.NICHE_HASHTAGS.items():
        if kw in title_lower: niche = tags; break
    hashtags = " ".join(config.BASE_HASHTAGS + niche)
    metadata["hashtags"] = hashtags

    chapters = metadata.get("chapters", "0:00 Introduction\n2:00 The Crime\n6:00 Investigation\n11:00 Aftermath\n14:00 Conclusion")
    metadata["full_description"] = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters}

🔔 Subscribe for daily true crime → {config.CHANNEL_HANDLE}
👍 Like if this gave you chills
💬 Drop your theory below!

{hashtags}

© {config.CHANNEL_NAME} — Educational purposes only."""

    metadata["tags_list"] = [t.strip() for t in metadata["tags"].split(",")][:20]
    wc = len(script.split())
    print(f"✅ Main script: {wc} words (~{wc//150} mins)")
    print(f"✅ Shorts script: {len(shorts_script.split())} words")
    return script.strip(), shorts_script, metadata


# ============================================
# STEP 6 — VOICEOVER (ElevenLabs primary, gTTS fallback)
# ============================================

def generate_voiceover_elevenlabs(text, output_path):
    """Use ElevenLabs for human-quality voice"""
    api_key = config.ELEVENLABS_API_KEY
    if not api_key:
        return False

    voice_id = config.ELEVENLABS_VOICE_ID  # e.g. "pNInz6obpgDQGcFmaJgB" (Adam)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    # ElevenLabs has ~2500 char limit per request — chunk it
    max_chars = 2400
    chunks = []
    remaining = text
    while len(remaining) > max_chars:
        cut = remaining.rfind(". ", 0, max_chars)
        if cut == -1: cut = max_chars
        chunks.append(remaining[:cut + 1])
        remaining = remaining[cut + 1:].strip()
    if remaining: chunks.append(remaining)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        p = os.path.join(config.OUTPUT_FOLDER, f"el_chunk_{i}.mp3")
        try:
            resp = requests.post(url, json={**payload, "text": chunk}, headers=headers, stream=True, timeout=60)
            if resp.status_code == 200:
                with open(p, "wb") as f:
                    for part in resp.iter_content(chunk_size=8192): f.write(part)
                chunk_paths.append(p)
                print(f"  🎙️ ElevenLabs chunk {i+1}/{len(chunks)}")
            else:
                print(f"  ⚠️ ElevenLabs error {resp.status_code}: {resp.text[:100]}")
                return False
        except Exception as e:
            print(f"  ⚠️ ElevenLabs exception: {e}")
            return False

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], output_path)
    else:
        clips = [AudioFileClip(p) for p in chunk_paths]
        merged = concatenate_audioclips(clips)
        merged.write_audiofile(output_path, logger=None)
        for c in clips: c.close()

    for p in chunk_paths:
        try: os.remove(p)
        except: pass

    return True


def generate_voiceover_gtts(text, output_path):
    """gTTS fallback"""
    max_chars = 4800
    clean = re.sub(r'\[.*?\]', '', text).replace("[PAUSE]", "...").strip()
    clean = re.sub(r'\n{3,}', '\n\n', clean)

    chunks = []
    while len(clean) > max_chars:
        cut = clean.rfind('. ', 0, max_chars)
        if cut == -1: cut = max_chars
        chunks.append(clean[:cut + 1])
        clean = clean[cut + 1:].strip()
    if clean: chunks.append(clean)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        p = os.path.join(config.OUTPUT_FOLDER, f"gtts_chunk_{i}.mp3")
        gTTS(text=chunk, lang="en", slow=False).save(p)
        chunk_paths.append(p)
        print(f"  🎙️ gTTS chunk {i+1}/{len(chunks)}")

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], output_path)
    else:
        clips = [AudioFileClip(p) for p in chunk_paths]
        merged = concatenate_audioclips(clips)
        merged.write_audiofile(output_path, logger=None)
        for c in clips: c.close()

    for p in chunk_paths:
        try: os.remove(p)
        except: pass


def generate_voiceover(script, label="voiceover"):
    print(f"\n🎙️  Generating {label}...")
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, f"{label}.mp3")

    clean = re.sub(r'\[.*?\]', '', script).replace("[PAUSE]", "...").strip()

    # Try ElevenLabs first
    if config.ELEVENLABS_API_KEY:
        print("  🎤 Trying ElevenLabs (human voice)...")
        if generate_voiceover_elevenlabs(clean, audio_path):
            print(f"✅ ElevenLabs {label} done!")
            return audio_path
        else:
            print("  ⚠️ ElevenLabs failed, falling back to gTTS")

    generate_voiceover_gtts(clean, audio_path)
    print(f"✅ gTTS {label} done!")
    return audio_path


# ============================================
# STEP 7 — KEN BURNS FOR IMAGES
# ============================================

def make_ken_burns_clip(img_path, duration, direction, W=1280, H=720):
    try:
        pil = Image.open(img_path).convert("RGB")
        pil = ImageEnhance.Brightness(pil).enhance(0.72)
        pil = ImageEnhance.Color(pil).enhance(0.65)
        pil = ImageEnhance.Contrast(pil).enhance(1.15)
        scale = max(W * 1.35 / pil.width, H * 1.35 / pil.height)
        nw, nh = int(pil.width * scale), int(pil.height * scale)
        pil = pil.resize((nw, nh), Image.LANCZOS)
        arr = np.array(pil)
    except:
        arr = np.zeros((H, W, 3), dtype=np.uint8)
        nw, nh = W, H

    dirs = {
        "zoom_in":   ((nw * .10, nh * .10, nw * .90, nh * .90), (nw * .20, nh * .20, nw * .80, nh * .80)),
        "zoom_out":  ((nw * .20, nh * .20, nw * .80, nh * .80), (nw * .05, nh * .05, nw * .95, nh * .95)),
        "pan_left":  ((nw * .05, nh * .10, nw * .70, nh * .90), (nw * .30, nh * .10, nw * .95, nh * .90)),
        "pan_right": ((nw * .30, nh * .10, nw * .95, nh * .90), (nw * .05, nh * .10, nw * .70, nh * .90)),
        "pan_up":    ((nw * .10, nh * .20, nw * .90, nh * .95), (nw * .10, nh * .05, nw * .90, nh * .80)),
        "diagonal":  ((nw * .05, nh * .05, nw * .72, nh * .72), (nw * .28, nh * .28, nw * .95, nh * .95)),
    }
    (sx1, sy1, sx2, sy2), (ex1, ey1, ex2, ey2) = dirs.get(direction, dirs["zoom_in"])

    def make_frame(t):
        p = t / max(duration, 0.001)
        p = p * p * (3 - 2 * p)
        x1 = max(0, min(int(sx1 + (ex1 - sx1) * p), nw - 2))
        y1 = max(0, min(int(sy1 + (ey1 - sy1) * p), nh - 2))
        x2 = max(x1 + 1, min(int(sx2 + (ex2 - sx2) * p), nw))
        y2 = max(y1 + 1, min(int(sy2 + (ey2 - sy2) * p), nh))
        crop = arr[y1:y2, x1:x2]
        if crop.size == 0: return np.zeros((H, W, 3), dtype=np.uint8)
        return np.array(Image.fromarray(crop).resize((W, H), Image.LANCZOS))

    return VideoClip(make_frame, duration=duration)


# ============================================
# STEP 8 — PROCESS VIDEO CLIP
# ============================================

def process_video_clip(vid_info, duration, W=1280, H=720):
    try:
        clip = VideoFileClip(vid_info["path"]).without_audio()
        if clip.duration < duration:
            loops = int(math.ceil(duration / clip.duration)) + 1
            clip = concatenate_videoclips([clip] * loops)
        clip = clip.subclip(0, duration)
        clip = clip.resize(height=H)
        if clip.size[0] < W: clip = clip.resize(width=W)
        if clip.size[0] > W:
            xc = clip.size[0] // 2
            clip = clip.crop(x1=xc - W // 2, x2=xc + W // 2)
        if clip.size[1] > H:
            yc = clip.size[1] // 2
            clip = clip.crop(y1=yc - H // 2, y2=yc + H // 2)
        clip = clip.fl_image(lambda frame:
            np.clip(frame.astype(np.float32) * 0.55, 0, 255).astype(np.uint8))
        return clip
    except Exception as e:
        print(f"  ⚠️ Video process error: {e}")
        return ColorClip(size=(W, H), color=(5, 0, 0), duration=duration)


# ============================================
# STEP 9 — CHAPTER CARD
# ============================================

def create_chapter_card(text, duration=2.5, W=1280, H=720):
    def make_frame(t):
        fade_in  = min(t / 0.4, 1.0)
        fade_out = min((duration - t) / 0.4, 1.0) if t > duration - 0.4 else 1.0
        alpha    = min(fade_in, fade_out)
        img  = Image.new("RGB", (W, H), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 54)
            f_sub   = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
        except:
            f_title = f_sub = ImageFont.load_default()
        lw = int(260 * alpha)
        draw.rectangle([(W // 2 - lw // 2, H // 2 - 52), (W // 2 + lw // 2, H // 2 - 49)], fill=(int(200 * alpha), 0, 0))
        sub = config.CHANNEL_NAME.upper()
        b = draw.textbbox((0, 0), sub, font=f_sub)
        draw.text(((W - (b[2] - b[0])) // 2, H // 2 - 88), sub, font=f_sub, fill=(int(130 * alpha), 0, 0))
        b = draw.textbbox((0, 0), text, font=f_title)
        draw.text(((W - (b[2] - b[0])) // 2, H // 2 - 15), text, font=f_title, fill=(int(255 * alpha), int(255 * alpha), int(255 * alpha)))
        return np.array(img)
    return VideoClip(make_frame, duration=duration)


# ============================================
# STEP 10 — ASSEMBLE MAIN VIDEO
# ============================================

def assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story):
    print("\n🎬 Step 10: Assembling mixed documentary video...")
    audio     = AudioFileClip(audio_path)
    total_dur = audio.duration
    W, H      = 1280, 720

    print(f"  ⏱️  Duration : {total_dur/60:.1f} minutes")
    print(f"  📸 Images   : {len(image_paths)}")
    print(f"  🎥 Videos   : {len(video_clips)}")

    KB_DIRS    = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "diagonal"]
    IMG_DUR    = 7.0
    VID_DUR    = 12.0
    CARD_DUR   = 2.5
    CARD_EVERY = 4

    media_sequence = []
    img_idx = 0
    vid_idx = 0
    while True:
        for _ in range(2):
            if image_paths:
                media_sequence.append(("image", image_paths[img_idx % len(image_paths)], IMG_DUR, KB_DIRS[img_idx % len(KB_DIRS)]))
                img_idx += 1
        if video_clips:
            media_sequence.append(("video", video_clips[vid_idx % len(video_clips)], VID_DUR, None))
            vid_idx += 1
        total_estimated = sum(m[2] for m in media_sequence) + (len(media_sequence) // CARD_EVERY) * CARD_DUR
        if total_estimated >= total_dur + 30: break
        if len(media_sequence) > 500: break

    print(f"  🎞️  Media slots planned: {len(media_sequence)}")

    clips     = []
    time_used = 0.0
    clips.append(create_chapter_card(metadata.get("title", "True Crime")[:50], duration=4.0))
    time_used += 4.0

    chapter_names = ["The Beginning", "The Crime", "The Investigation", "The Aftermath", "The Truth"]
    chapter_count = 0
    media_count   = 0

    for m_type, m_data, m_dur, m_extra in media_sequence:
        if time_used >= total_dur - 1.0: break
        remaining = total_dur - time_used
        if media_count > 0 and media_count % CARD_EVERY == 0:
            cd = min(CARD_DUR, remaining - 0.5)
            if cd > 0.5:
                name = chapter_names[min(chapter_count, len(chapter_names) - 1)]
                clips.append(create_chapter_card(f"Chapter {chapter_count + 1}: {name}", duration=cd))
                time_used += cd
                chapter_count += 1
                remaining = total_dur - time_used
                if remaining < 1.0: break
        clip_dur = min(m_dur, remaining - 0.5)
        if clip_dur < 1.0: break
        if m_type == "image":
            kb = make_ken_burns_clip(m_data, clip_dur, m_extra, W, H)
            dark_ov = ColorClip(size=(W, H), color=(0, 0, 0), duration=clip_dur).set_opacity(0.28)
            clip = CompositeVideoClip([kb, dark_ov])
        else:
            clip = process_video_clip(m_data, clip_dur, W, H)
            dark_ov = ColorClip(size=(W, H), color=(0, 0, 0), duration=clip_dur).set_opacity(0.25)
            clip = CompositeVideoClip([clip, dark_ov])
        clips.append(clip)
        time_used += clip_dur
        media_count += 1

    outro_dur = min(3.0, max(0.5, total_dur - time_used))
    clips.append(create_chapter_card("Subscribe for Daily Mysteries 🔴", duration=outro_dur))

    print(f"  🔗 Joining {len(clips)} clips...")
    try:
        video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print(f"  ⚠️ compose failed: {e}, trying chain...")
        video = concatenate_videoclips(clips, method="chain")

    if video.duration > total_dur + 0.5:
        video = video.subclip(0, total_dur)
    elif video.duration < total_dur - 1.0:
        gap = total_dur - video.duration
        pad = ImageClip(video.get_frame(video.duration - 0.1), duration=gap)
        video = concatenate_videoclips([video, pad])

    def wm_frame(t):
        img  = Image.new("RGBA", (W, 36), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((18, 8), f"🔴 {config.CHANNEL_NAME}  •  New case every day", font=font, fill=(210, 210, 210, 135))
        return np.array(img.convert("RGB"))

    wm    = VideoClip(wm_frame, duration=total_dur).set_position(("left", "bottom")).set_opacity(0.42)
    final = CompositeVideoClip([video, wm]).set_audio(audio)
    out   = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
    print("  💾 Writing final video...")
    final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac",
                          threads=4, preset="ultrafast", bitrate="4000k", logger=None)
    print(f"✅ Documentary assembled! ({total_dur/60:.1f} mins)")
    return out


# ============================================
# STEP 10b — ASSEMBLE SHORTS VIDEO (9:16 vertical)
# ============================================

def assemble_shorts_video(shorts_audio_path, image_paths, metadata):
    print("\n📱 Step 10b: Assembling YouTube Short (9:16)...")
    W, H = 1080, 1920  # Vertical format

    audio     = AudioFileClip(shorts_audio_path)
    total_dur = min(audio.duration, 59.0)  # YouTube Shorts max 60s

    # Use 4-6 images for a short
    used_images = image_paths[:6] if len(image_paths) >= 6 else image_paths
    clip_dur    = total_dur / max(len(used_images), 1)
    KB_DIRS     = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

    def make_vertical_kb(img_path, duration, direction):
        """Ken Burns for 9:16 vertical format"""
        try:
            pil = Image.open(img_path).convert("RGB")
            pil = ImageEnhance.Brightness(pil).enhance(0.68)
            pil = ImageEnhance.Color(pil).enhance(0.6)
            pil = ImageEnhance.Contrast(pil).enhance(1.2)
            # For vertical: crop landscape to portrait
            scale = max(W * 1.3 / pil.width, H * 1.3 / pil.height)
            nw, nh = int(pil.width * scale), int(pil.height * scale)
            pil = pil.resize((nw, nh), Image.LANCZOS)
            arr = np.array(pil)
        except:
            arr = np.zeros((H, W, 3), dtype=np.uint8)
            nw, nh = W, H

        dirs = {
            "zoom_in":   ((nw * .15, nh * .15, nw * .85, nh * .85), (nw * .22, nh * .22, nw * .78, nh * .78)),
            "zoom_out":  ((nw * .22, nh * .22, nw * .78, nh * .78), (nw * .10, nh * .10, nw * .90, nh * .90)),
            "pan_left":  ((nw * .05, nh * .05, nw * .65, nh * .95), (nw * .35, nh * .05, nw * .95, nh * .95)),
            "pan_right": ((nw * .35, nh * .05, nw * .95, nh * .95), (nw * .05, nh * .05, nw * .65, nh * .95)),
        }
        (sx1, sy1, sx2, sy2), (ex1, ey1, ex2, ey2) = dirs.get(direction, dirs["zoom_in"])

        def make_frame(t):
            p = t / max(duration, 0.001)
            p = p * p * (3 - 2 * p)
            x1 = max(0, min(int(sx1 + (ex1 - sx1) * p), nw - 2))
            y1 = max(0, min(int(sy1 + (ey1 - sy1) * p), nh - 2))
            x2 = max(x1 + 1, min(int(sx2 + (ex2 - sx2) * p), nw))
            y2 = max(y1 + 1, min(int(sy2 + (ey2 - sy2) * p), nh))
            crop = arr[y1:y2, x1:x2]
            if crop.size == 0: return np.zeros((H, W, 3), dtype=np.uint8)
            return np.array(Image.fromarray(crop).resize((W, H), Image.LANCZOS))

        return VideoClip(make_frame, duration=duration)

    clips = []
    for i, img_path in enumerate(used_images):
        d   = clip_dur
        clip = make_vertical_kb(img_path, d, KB_DIRS[i % len(KB_DIRS)])
        dark_ov = ColorClip(size=(W, H), color=(0, 0, 0), duration=d).set_opacity(0.3)

        # Add captions overlay at bottom for Shorts
        def make_caption(t, title=metadata.get("title", "")[:50]):
            img  = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            try:
                f_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 52)
                f_sub   = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 30)
            except:
                f_title = f_sub = ImageFont.load_default()
            # Semi-transparent background bar
            overlay = Image.new("RGBA", (W, 200), (0, 0, 0, 160))
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)
            # Channel name
            draw.text((40, 16), f"🔴 {config.CHANNEL_NAME}", font=f_sub, fill=(200, 200, 200, 220))
            # Title
            words = title.split()
            line1 = " ".join(words[:len(words) // 2])
            line2 = " ".join(words[len(words) // 2:])
            draw.text((40, 58), line1, font=f_title, fill=(255, 255, 255, 255))
            draw.text((40, 118), line2, font=f_title, fill=(255, 255, 0, 255))
            return np.array(img.convert("RGB"))

        caption_clip = VideoClip(make_caption, duration=d).set_position(("center", H - 200))
        composed = CompositeVideoClip([clip, dark_ov, caption_clip])
        clips.append(composed)

    video = concatenate_videoclips(clips, method="compose")
    if video.duration > total_dur:
        video = video.subclip(0, total_dur)

    final = video.set_audio(audio.subclip(0, min(audio.duration, total_dur)))
    out   = os.path.join(config.OUTPUT_FOLDER, "shorts_video.mp4")
    print("  💾 Writing Shorts video...")
    final.write_videofile(out, fps=30, codec="libx264", audio_codec="aac",
                          threads=4, preset="ultrafast", bitrate="6000k", logger=None)
    print(f"✅ Short assembled! ({total_dur:.0f}s)")
    return out


# ============================================
# STEP 11 — THUMBNAIL (3 STYLES)
# ============================================

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 11: Creating thumbnail...")
    W, H = 1280, 720
    thumb = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")

    style = metadata.get("thumbnail_style", "1").strip()
    thumb_text = metadata.get("thumbnail_text", "SHOCKING CASE").upper()
    title_text = story["title"][:42] + ("..." if len(story["title"]) > 42 else "")

    try:
        f_xl  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 86)
        f_lg  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 52)
        f_md  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 36)
        f_sm  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 26)
    except:
        f_xl = f_lg = f_md = f_sm = ImageFont.load_default()

    if image_paths:
        try:
            base_img = Image.open(image_paths[0]).convert("RGB").resize((W, H), Image.LANCZOS)
        except:
            base_img = Image.new("RGB", (W, H), (8, 0, 0))
    else:
        base_img = Image.new("RGB", (W, H), (8, 0, 0))

    if style == "2":
        # STYLE 2: Red split — left half red tinted, right half dark
        # Great for: murder cases, killers
        left  = base_img.crop((0, 0, W // 2, H))
        right = base_img.crop((W // 2, 0, W, H))
        left  = ImageEnhance.Brightness(left).enhance(0.35)
        left  = ImageEnhance.Color(left).enhance(0.4)
        right = ImageEnhance.Brightness(right).enhance(0.22)
        right = ImageEnhance.Color(right).enhance(0.3)
        red_tint = Image.new("RGBA", (W // 2, H), (140, 0, 0, 100))
        left_rgba = left.convert("RGBA")
        left_rgba = Image.alpha_composite(left_rgba, red_tint)
        img = Image.new("RGB", (W, H))
        img.paste(left_rgba.convert("RGB"), (0, 0))
        img.paste(right, (W // 2, 0))
        draw = ImageDraw.Draw(img)
        # Red divider line
        draw.rectangle([(W // 2 - 4, 0), (W // 2 + 4, H)], fill=(220, 0, 0))
        # Channel tag
        draw.text((20, 18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(220, 220, 220))
        # Big hook text on left side
        words = thumb_text.split()
        lines = [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])] if len(words) > 2 else [thumb_text]
        y = H // 2 - len(lines) * 92 // 2
        for line in lines:
            b = draw.textbbox((0, 0), line, font=f_xl)
            x = (W // 2 - (b[2] - b[0])) // 2
            for s in range(6, 0, -1): draw.text((x + s, y + s), line, font=f_xl, fill=(0, 0, 0))
            draw.text((x, y), line, font=f_xl, fill=(255, 255, 255))
            y += 96
        # Title on right
        b = draw.textbbox((0, 0), title_text, font=f_md)
        tx = W // 2 + (W // 2 - (b[2] - b[0])) // 2
        draw.text((tx, H // 2 - 20), title_text, font=f_md, fill=(255, 220, 0))

    elif style == "3":
        # STYLE 3: Dark vignette + large centered text + glowing red bottom bar
        # Great for: unsolved mysteries, conspiracy
        img = ImageEnhance.Brightness(base_img).enhance(0.20)
        img = ImageEnhance.Color(img).enhance(0.3)
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        # Vignette
        vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vignette)
        for i in range(250):
            alpha = int(i * 0.8)
            vd.rectangle([(i, i), (W - i, H - i)], outline=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
        draw = ImageDraw.Draw(img)
        # Channel name
        draw.text((20, 18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(180, 180, 180))
        # Center hook text
        words = thumb_text.split()
        lines = ([thumb_text] if len(words) <= 2 else
                 [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])])
        y = H // 2 - 130
        for line in lines:
            b = draw.textbbox((0, 0), line, font=f_xl)
            x = (W - (b[2] - b[0])) // 2
            # Glowing effect layers
            for r in range(12, 0, -3):
                draw.text((x, y), line, font=f_xl, fill=(180, 0, 0, 30))
            for s in range(5, 0, -1): draw.text((x + s, y + s), line, font=f_xl, fill=(0, 0, 0))
            draw.text((x, y), line, font=f_xl, fill=(255, 60, 60))
            y += 100
        # Bottom red bar
        draw.rectangle([(0, H - 80), (W, H)], fill=(180, 0, 0))
        b = draw.textbbox((0, 0), title_text, font=f_md)
        draw.text(((W - (b[2] - b[0])) // 2, H - 60), title_text, font=f_md, fill=(255, 255, 255))

    else:
        # STYLE 1: Classic dark — (original improved)
        img = ImageEnhance.Brightness(base_img).enhance(0.28)
        img = ImageEnhance.Color(img).enhance(0.5)
        draw = ImageDraw.Draw(img)
        draw.text((28, 18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(210, 210, 210))
        words = thumb_text.split()
        lines = ([thumb_text] if len(words) <= 2 else
                 [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])])
        y = H // 2 - len(lines) * 102 // 2 - 10
        for line in lines:
            b = draw.textbbox((0, 0), line, font=f_xl)
            x = (W - (b[2] - b[0])) // 2
            for s in range(8, 0, -1): draw.text((x + s, y + s), line, font=f_xl, fill=(0, 0, 0))
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]: draw.text((x + dx, y + dy), line, font=f_xl, fill=(215, 0, 0))
            draw.text((x, y), line, font=f_xl, fill=(255, 255, 255))
            y += 104
        b = draw.textbbox((0, 0), title_text, font=f_lg)
        draw.text(((W - (b[2] - b[0])) // 2, y + 10), title_text, font=f_lg, fill=(230, 185, 0))
        draw.rectangle([(0, H - 58), (W, H)], fill=(12, 0, 0))
        draw.rectangle([(0, H - 60), (W, H - 58)], fill=(200, 0, 0))
        draw.text((28, H - 44), "TRUE CRIME  •  UNSOLVED MYSTERIES  •  DARK CASES", font=f_sm, fill=(155, 155, 155))

    img.save(thumb, "JPEG", quality=95)
    print(f"✅ Thumbnail created! (Style {style})")
    return thumb


# ============================================
# STEP 12 — UPLOAD TO YOUTUBE
# ============================================

def upload_to_youtube(video_path, thumbnail_path, metadata, is_short=False):
    kind = "Short" if is_short else "Video"
    print(f"\n📤 Step 12: Uploading {kind} to YouTube...")

    td    = json.loads(config.YOUTUBE_TOKEN)
    creds = Credentials(
        token=td.get("token"), refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri"), client_id=td.get("client_id"),
        client_secret=td.get("client_secret"), scopes=td.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("🔄 Token refreshed!")

    yt = build("youtube", "v3", credentials=creds)

    title = metadata.get("title", "True Crime")[:100]
    if is_short:
        title = f"#Shorts {title}"[:100]
        description = f"🔴 {title}\n\n{metadata.get('hashtags', '')}\n\n#Shorts\n\n🔔 Subscribe → {config.CHANNEL_HANDLE}"
        tags = metadata.get("tags_list", []) + ["Shorts", "TrueCrimeShorts"]
    else:
        description = metadata.get("full_description", "")
        tags = metadata.get("tags_list", [])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:500],
            "categoryId": "25",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    resp  = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    vid   = resp.get("id")
    print(f"✅ {kind} uploaded! ID: {vid}")

    if not is_short and thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("✅ Thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail: {e}")

    if not is_short:
        pinned = metadata.get("pinned_comment", "What do YOU think happened? 👇")
        try:
            yt.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {
                    "textOriginal": f"🔴 {pinned}\n\n💬 Every theory welcome!\n🔔 Subscribe → {config.CHANNEL_HANDLE}"
                }}}}
            ).execute()
            print("✅ Pinned comment posted!")
        except Exception as e:
            print(f"⚠️ Comment: {e}")

    print(f"\n🎉 LIVE: https://youtube.com/watch?v={vid}")
    return vid


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline():
    print("=" * 55)
    print("🚀 ARCHIVE OF ENIGMAS — Documentary Pipeline v5")
    print("=" * 55)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    try:
        # 1. Get story (with diversity guard)
        story = fetch_story()
        topic = story.get("topic", "other")
        print(f"  📌 Topic type: {topic}")

        # 2. Generate scripts (main + shorts)
        script, shorts_script, metadata = generate_script(story)

        # 3. Fetch media
        img_queries, vid_queries = extract_keywords(story)
        image_paths  = fetch_images(img_queries, target=18)
        video_clips  = fetch_videos(vid_queries, target=10)

        # 4. Voiceovers
        audio_path        = generate_voiceover(script, label="voiceover")
        shorts_audio_path = None
        if shorts_script:
            shorts_audio_path = generate_voiceover(shorts_script, label="shorts_voiceover")

        # 5. Thumbnail
        thumbnail_path = create_thumbnail(image_paths, metadata, story)

        # 6. Assemble main video
        video_path = assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story)

        # 7. Assemble Short
        shorts_path = None
        if shorts_audio_path and image_paths:
            try:
                shorts_path = assemble_shorts_video(shorts_audio_path, image_paths, metadata)
            except Exception as e:
                print(f"⚠️ Shorts assembly failed: {e}")

        # 8. Upload
        video_id  = upload_to_youtube(video_path, thumbnail_path, metadata, is_short=False)
        shorts_id = None
        if shorts_path:
            try:
                shorts_id = upload_to_youtube(shorts_path, None, metadata, is_short=True)
            except Exception as e:
                print(f"⚠️ Shorts upload failed: {e}")

        # 9. Update history (prevent future repeats)
        keywords = [story["title"].lower().split()[0]] if story["title"] else []
        update_history(metadata["title"], topic, keywords)

        print("\n" + "=" * 55)
        print(f"🎉 SUCCESS!")
        print(f"📺 Main: https://youtube.com/watch?v={video_id}")
        if shorts_id:
            print(f"📱 Short: https://youtube.com/watch?v={shorts_id}")
        print(f"📊 Title  : {metadata.get('title')}")
        print(f"🎭 Style  : Thumbnail style {metadata.get('thumbnail_style', '1')}")
        print(f"🎤 Voice  : {'ElevenLabs' if config.ELEVENLABS_API_KEY else 'gTTS'}")
        print("=" * 55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback; traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
