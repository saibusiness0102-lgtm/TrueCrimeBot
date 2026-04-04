# ============================================
# ARCHIVE OF ENIGMAS — DOCUMENTARY BOT v4
# Mixed images + videos | Full duration | Cinematic
# ============================================

import os
import re
import json
import math
import random
import shutil
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
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
                content = entry.get("summary","") or entry.get("description","")
                if len(content) > 300:
                    print(f"✅ RSS story: {entry.title}")
                    return {"title":entry.title,"content":content[:5000],"source":"RSS"}
        except:
            continue
    return None


def fetch_from_wikipedia():
    case = random.choice(config.WIKIPEDIA_CASES)
    try:
        print(f"📖 Wikipedia: {case}")
        page = wikipedia.page(case, auto_suggest=True)
        return {"title":page.title,"content":page.content[:6000],"source":"Wikipedia"}
    except Exception as e:
        print(f"⚠️ Wikipedia fallback: {e}")
        return {"title":"The Zodiac Killer",
                "content":"The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s.",
                "source":"Fallback"}


def fetch_story():
    print("\n🔍 Step 1: Fetching story...")
    story = fetch_from_rss() if not config.PREFER_WIKIPEDIA else None
    return story or fetch_from_wikipedia()


# ============================================
# STEP 2 - EXTRACT KEYWORDS FOR BOTH IMAGES + VIDEOS
# ============================================

def extract_keywords(story):
    title   = story["title"].lower()
    content = story["content"].lower()

    # Image search queries (still/atmospheric)
    image_queries = [
        "crime scene tape dark night",
        "detective noir shadow investigation",
        "old newspaper crime headline vintage",
        "dark foggy forest mystery",
        "fingerprint forensic evidence closeup",
        "abandoned house dark night",
        "silhouette dark figure mystery",
        "courtroom justice vintage dark",
        "wanted poster vintage crime",
        "dark alley rain night cinematic",
        "candlelight dark room mystery",
        "old photograph vintage sepia dark",
        "magnifying glass detective clue",
        "police badge dark dramatic",
        "prison bars dark shadow",
    ]

    # Video search queries (motion/atmospheric)
    video_queries = [
        "dark rainy city night",
        "police car lights night",
        "fog forest dark eerie",
        "rain window dark night",
        "storm lightning dramatic dark",
        "dark ocean waves night",
        "city traffic night rain",
        "smoke dark dramatic",
        "fire dark night dramatic",
        "dark road night driving",
    ]

    # Case-specific additions
    if any(w in title+content for w in ["murder","kill","dead","homicide"]):
        image_queries = ["crime scene investigation police","forensic dark dramatic","murder mystery detective noir"] + image_queries
        video_queries = ["police siren lights night","crime scene investigation dark","forensic lab dramatic"] + video_queries

    if any(w in title+content for w in ["missing","disappear","vanish"]):
        image_queries = ["missing person poster dark","search party flashlight","empty road dark night"] + image_queries
        video_queries = ["search rescue forest night","flashlight dark forest","empty road fog night"] + video_queries

    if any(w in title+content for w in ["serial","killer"]):
        image_queries = ["detective board suspects investigation","prison dark corridor","shadow figure dark"] + image_queries
        video_queries = ["dark corridor dramatic","prison cell dramatic","shadow walking dark"] + video_queries

    if any(w in title+content for w in ["forest","woods","rural","mountain"]):
        image_queries = ["dark forest fog eerie trees","mist forest mystery"] + image_queries
        video_queries = ["forest fog dramatic dark","dark woods eerie"] + video_queries

    if any(w in title+content for w in ["water","river","lake","ocean"]):
        image_queries = ["dark lake night eerie","river fog mystery"] + image_queries
        video_queries = ["dark water lake night","river fog dramatic"] + video_queries

    random.shuffle(image_queries)
    random.shuffle(video_queries)
    return image_queries[:18], video_queries[:12]


# ============================================
# STEP 3 - FETCH IMAGES FROM PEXELS
# ============================================

def fetch_images(queries, target=18):
    print(f"\n📸 Fetching {target} cinematic images...")
    img_dir = os.path.join(config.OUTPUT_FOLDER, "images")
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir)
    os.makedirs(img_dir, exist_ok=True)

    headers   = {"Authorization": config.PEXELS_API_KEY}
    images    = []
    used_ids  = set()

    for query in queries:
        if len(images) >= target:
            break
        try:
            resp   = requests.get(
                f"https://api.pexels.com/v1/search?query={query}&per_page=3&orientation=landscape",
                headers=headers, timeout=10)
            photos = resp.json().get("photos",[])
            for photo in photos:
                if len(images) >= target: break
                if photo["id"] in used_ids: continue
                used_ids.add(photo["id"])
                url = photo["src"]["large2x"]
                r   = requests.get(url, timeout=15)
                if r.status_code == 200:
                    path = os.path.join(img_dir, f"img_{len(images):03d}.jpg")
                    with open(path,"wb") as f: f.write(r.content)
                    images.append(path)
                    print(f"  📸 Image {len(images)}: {query[:38]}")
        except Exception as e:
            print(f"  ⚠️ Image error: {e}")

    print(f"✅ {len(images)} images fetched!")
    return images


# ============================================
# STEP 4 - FETCH VIDEOS FROM PEXELS
# ============================================

def fetch_videos(queries, target=10):
    print(f"\n🎥 Fetching {target} atmospheric video clips...")
    vid_dir  = os.path.join(config.OUTPUT_FOLDER, "videos")
    if os.path.exists(vid_dir):
        shutil.rmtree(vid_dir)
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
            items = resp.json().get("videos",[])
            for item in items:
                if len(videos) >= target: break
                if item["id"] in used_ids: continue
                used_ids.add(item["id"])

                # Pick best quality file under 1080p
                files = sorted(item["video_files"], key=lambda x: x.get("width",0), reverse=True)
                chosen = next((f for f in files if f.get("width",0) <= 1920), files[0] if files else None)
                if not chosen: continue

                path = os.path.join(vid_dir, f"vid_{len(videos):03d}.mp4")
                r    = requests.get(chosen["link"], stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path,"wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    videos.append({"path": path, "duration": item.get("duration", 10)})
                    print(f"  🎥 Video {len(videos)}: {query[:38]} ({item.get('duration',0)}s)")
        except Exception as e:
            print(f"  ⚠️ Video error: {e}")

    print(f"✅ {len(videos)} video clips fetched!")
    return videos


# ============================================
# STEP 5 - GENERATE SCRIPT
# ============================================

def generate_script(story):
    print("\n✍️  Step 2: Generating 15-min script...")
    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = f"""
You are the writer for "Archive of Enigmas" — a top true crime YouTube channel.
Write a COMPLETE 15-minute video script (2200+ words) about this case.

Story Title: {story['title']}
Story Content: {story['content']}

STRUCTURE:
[HOOK] Most shocking moment. 60 seconds.
[INTRO] Welcome to Archive of Enigmas intro.
[CHAPTER 1: BACKGROUND] Set scene, victims. 3 mins. End with cliffhanger.
[CHAPTER 2: THE CRIME] What happened. 4 mins. Add [PAUSE] markers.
[CHAPTER 3: INVESTIGATION] Police, clues, suspects. 4 mins.
[CHAPTER 4: AFTERMATH] What happened next. 2 mins.
[ENGAGEMENT] Ask viewers to comment and subscribe.
[CHAPTER 5: TWIST] Shocking revelation. 2 mins.
[OUTRO] Subscribe CTA.

RULES: 2200+ words. Use "you". Cliffhanger every chapter. Specific details. Human storyteller.

After script:
---METADATA---
TITLE: (Clickbait under 70 chars)
DESCRIPTION: (300 word SEO description)
TAGS: (20 tags comma separated)
THUMBNAIL_TEXT: (3-5 shocking words)
THUMBNAIL_MOOD: (dark/red/blue/dramatic)
PINNED_COMMENT: (Engaging question)
CHAPTERS: (YouTube timestamps one per line like "0:00 The Opening")
"""

    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role":"user","content":prompt}],
        max_tokens=4000, temperature=0.85)

    full = resp.choices[0].message.content

    if "---METADATA---" in full:
        script, meta_raw = full.split("---METADATA---",1)
    else:
        script, meta_raw = full, ""

    metadata = {}
    cur_key, cur_val = None, []
    for line in meta_raw.strip().split("\n"):
        matched = False
        for key in ["TITLE","DESCRIPTION","TAGS","THUMBNAIL_TEXT","THUMBNAIL_MOOD","PINNED_COMMENT","CHAPTERS"]:
            if line.startswith(f"{key}:"):
                if cur_key: metadata[cur_key.lower()] = "\n".join(cur_val).strip()
                cur_key, cur_val = key, [line.replace(f"{key}:","").strip()]
                matched = True; break
        if not matched and cur_key: cur_val.append(line)
    if cur_key: metadata[cur_key.lower()] = "\n".join(cur_val).strip()

    metadata.setdefault("title", story["title"])
    metadata.setdefault("description", f"True crime: {story['title']}")
    metadata.setdefault("tags","true crime,mystery,unsolved,dark cases")
    metadata.setdefault("thumbnail_text","SHOCKING CASE")
    metadata.setdefault("thumbnail_mood","dark")
    metadata.setdefault("pinned_comment","What do YOU think happened? Drop your theory! 👇")

    title_lower = story["title"].lower()
    niche = config.NICHE_HASHTAGS.get("default",[])
    for kw,tags in config.NICHE_HASHTAGS.items():
        if kw in title_lower: niche = tags; break
    hashtags = " ".join(config.BASE_HASHTAGS + niche)
    metadata["hashtags"] = hashtags

    chapters = metadata.get("chapters","0:00 Introduction\n2:00 The Crime\n6:00 Investigation\n11:00 Aftermath\n14:00 Conclusion")
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
    print(f"✅ Script: {wc} words (~{wc//150} mins)")
    return script.strip(), metadata


# ============================================
# STEP 6 - VOICEOVER
# ============================================

def generate_voiceover(script):
    print("\n🎙️  Step 6: Generating voiceover...")
    clean = re.sub(r'\[.*?\]','',script).replace("[PAUSE]","...").strip()
    clean = re.sub(r'\n{3,}','\n\n',clean)

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER,"voiceover.mp3")

    max_chars = 4800
    chunks = []
    while len(clean) > max_chars:
        cut = clean.rfind('. ',0,max_chars)
        if cut == -1: cut = max_chars
        chunks.append(clean[:cut+1])
        clean = clean[cut+1:].strip()
    if clean: chunks.append(clean)

    chunk_paths = []
    for i,chunk in enumerate(chunks):
        p = os.path.join(config.OUTPUT_FOLDER,f"chunk_{i}.mp3")
        gTTS(text=chunk,lang="en",slow=False).save(p)
        chunk_paths.append(p)
        print(f"  🎙️ Chunk {i+1}/{len(chunks)}")

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], audio_path)
    else:
        clips = [AudioFileClip(p) for p in chunk_paths]
        merged = concatenate_audioclips(clips)
        merged.write_audiofile(audio_path, logger=None)
        for c in clips: c.close()

    for p in chunk_paths:
        try: os.remove(p)
        except: pass

    print("✅ Voiceover done!")
    return audio_path


# ============================================
# STEP 7 - KEN BURNS FOR IMAGES
# ============================================

def make_ken_burns_clip(img_path, duration, direction, W=1280, H=720):
    try:
        pil = Image.open(img_path).convert("RGB")
        pil = ImageEnhance.Brightness(pil).enhance(0.72)
        pil = ImageEnhance.Color(pil).enhance(0.65)
        pil = ImageEnhance.Contrast(pil).enhance(1.15)
        scale = max(W*1.35/pil.width, H*1.35/pil.height)
        nw,nh = int(pil.width*scale), int(pil.height*scale)
        pil = pil.resize((nw,nh), Image.LANCZOS)
        arr = np.array(pil)
    except:
        arr = np.zeros((H,W,3),dtype=np.uint8)
        nw,nh = W,H

    dirs = {
        "zoom_in":   ((nw*.10,nh*.10,nw*.90,nh*.90),(nw*.20,nh*.20,nw*.80,nh*.80)),
        "zoom_out":  ((nw*.20,nh*.20,nw*.80,nh*.80),(nw*.05,nh*.05,nw*.95,nh*.95)),
        "pan_left":  ((nw*.05,nh*.10,nw*.70,nh*.90),(nw*.30,nh*.10,nw*.95,nh*.90)),
        "pan_right": ((nw*.30,nh*.10,nw*.95,nh*.90),(nw*.05,nh*.10,nw*.70,nh*.90)),
        "pan_up":    ((nw*.10,nh*.20,nw*.90,nh*.95),(nw*.10,nh*.05,nw*.90,nh*.80)),
        "diagonal":  ((nw*.05,nh*.05,nw*.72,nh*.72),(nw*.28,nh*.28,nw*.95,nh*.95)),
    }
    (sx1,sy1,sx2,sy2),(ex1,ey1,ex2,ey2) = dirs.get(direction, dirs["zoom_in"])

    def make_frame(t):
        p = t/max(duration,0.001)
        p = p*p*(3-2*p)  # ease in-out
        x1=max(0,min(int(sx1+(ex1-sx1)*p),nw-2))
        y1=max(0,min(int(sy1+(ey1-sy1)*p),nh-2))
        x2=max(x1+1,min(int(sx2+(ex2-sx2)*p),nw))
        y2=max(y1+1,min(int(sy2+(ey2-sy2)*p),nh))
        crop = arr[y1:y2,x1:x2]
        if crop.size==0: return np.zeros((H,W,3),dtype=np.uint8)
        return np.array(Image.fromarray(crop).resize((W,H),Image.LANCZOS))

    return VideoClip(make_frame, duration=duration)


# ============================================
# STEP 8 - PROCESS VIDEO CLIP
# ============================================

def process_video_clip(vid_info, duration, W=1280, H=720):
    """Load, trim, resize and color-grade a video clip"""
    try:
        clip = VideoFileClip(vid_info["path"]).without_audio()

        # Loop if shorter than needed
        if clip.duration < duration:
            loops = int(math.ceil(duration / clip.duration)) + 1
            clip = concatenate_videoclips([clip]*loops)

        # Trim to needed duration
        clip = clip.subclip(0, duration)

        # Resize maintaining aspect ratio then crop center
        clip = clip.resize(height=H)
        if clip.size[0] < W:
            clip = clip.resize(width=W)

        # Center crop to exact size
        if clip.size[0] > W:
            x_center = clip.size[0]//2
            clip = clip.crop(x1=x_center-W//2, x2=x_center+W//2)
        if clip.size[1] > H:
            y_center = clip.size[1]//2
            clip = clip.crop(y1=y_center-H//2, y2=y_center+H//2)

        # Darken for cinematic feel
        clip = clip.fl_image(lambda frame:
            np.clip(frame.astype(np.float32)*0.55, 0, 255).astype(np.uint8))

        return clip
    except Exception as e:
        print(f"  ⚠️ Video process error: {e}")
        return ColorClip(size=(W,H), color=(5,0,0), duration=duration)


# ============================================
# STEP 9 - CHAPTER CARD
# ============================================

def create_chapter_card(text, duration=2.5, W=1280, H=720):
    def make_frame(t):
        fade_in  = min(t/0.4, 1.0)
        fade_out = min((duration-t)/0.4, 1.0) if t > duration-0.4 else 1.0
        alpha    = min(fade_in, fade_out)

        img  = Image.new("RGB",(W,H),(0,0,0))
        draw = ImageDraw.Draw(img)

        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",54)
            f_sub   = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",24)
        except:
            f_title = f_sub = ImageFont.load_default()

        lw = int(260*alpha)
        draw.rectangle([(W//2-lw//2,H//2-52),(W//2+lw//2,H//2-49)], fill=(int(200*alpha),0,0))

        sub = config.CHANNEL_NAME.upper()
        b   = draw.textbbox((0,0),sub,font=f_sub)
        draw.text(((W-(b[2]-b[0]))//2, H//2-88), sub, font=f_sub, fill=(int(130*alpha),0,0))

        b = draw.textbbox((0,0),text,font=f_title)
        draw.text(((W-(b[2]-b[0]))//2, H//2-15), text, font=f_title,
                  fill=(int(255*alpha),int(255*alpha),int(255*alpha)))

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# ============================================
# STEP 10 - ASSEMBLE MIXED DOCUMENTARY VIDEO
# ============================================

def assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story):
    print("\n🎬 Step 10: Assembling mixed documentary video...")

    audio     = AudioFileClip(audio_path)
    total_dur = audio.duration
    W, H      = 1280, 720

    print(f"  ⏱️  Duration : {total_dur/60:.1f} minutes")
    print(f"  📸 Images   : {len(image_paths)}")
    print(f"  🎥 Videos   : {len(video_clips)}")

    KB_DIRS    = ["zoom_in","zoom_out","pan_left","pan_right","pan_up","diagonal"]
    IMG_DUR    = 7.0   # seconds per image
    VID_DUR    = 12.0  # seconds per video clip
    CARD_DUR   = 2.5
    CARD_EVERY = 4     # chapter card every N media items

    # Build interleaved media list: image, image, video, image, image, video ...
    # Ratio: 2 images per 1 video
    media_sequence = []
    img_idx = 0
    vid_idx = 0

    while True:
        # 2 images
        for _ in range(2):
            if image_paths:
                media_sequence.append(("image", image_paths[img_idx % len(image_paths)], IMG_DUR, KB_DIRS[img_idx % len(KB_DIRS)]))
                img_idx += 1
        # 1 video
        if video_clips:
            media_sequence.append(("video", video_clips[vid_idx % len(video_clips)], VID_DUR, None))
            vid_idx += 1

        # Estimate total time so far
        total_estimated = sum(m[2] for m in media_sequence) + (len(media_sequence)//CARD_EVERY)*CARD_DUR
        if total_estimated >= total_dur + 30:  # add 30s buffer
            break

        # Safety: don't loop infinitely
        if len(media_sequence) > 500:
            break

    print(f"  🎞️  Media slots planned: {len(media_sequence)}")

    # Build clips list
    clips     = []
    time_used = 0.0

    # Opening title card
    clips.append(create_chapter_card(metadata.get("title","True Crime")[:50], duration=4.0))
    time_used += 4.0

    chapter_names = ["The Beginning","The Crime","The Investigation","The Aftermath","The Truth"]
    chapter_count = 0
    media_count   = 0

    for m_type, m_data, m_dur, m_extra in media_sequence:
        if time_used >= total_dur - 1.0:
            break

        remaining = total_dur - time_used

        # Chapter card every N items
        if media_count > 0 and media_count % CARD_EVERY == 0:
            cd = min(CARD_DUR, remaining - 0.5)
            if cd > 0.5:
                name = chapter_names[min(chapter_count, len(chapter_names)-1)]
                clips.append(create_chapter_card(f"Chapter {chapter_count+1}: {name}", duration=cd))
                time_used += cd
                chapter_count += 1
                remaining = total_dur - time_used
                if remaining < 1.0: break

        clip_dur = min(m_dur, remaining - 0.5)
        if clip_dur < 1.0: break

        if m_type == "image":
            # Ken Burns image
            kb = make_ken_burns_clip(m_data, clip_dur, m_extra, W, H)
            dark_ov = ColorClip(size=(W,H),color=(0,0,0),duration=clip_dur).set_opacity(0.28)
            clip = CompositeVideoClip([kb, dark_ov])

        else:
            # Atmospheric video clip
            clip = process_video_clip(m_data, clip_dur, W, H)
            dark_ov = ColorClip(size=(W,H),color=(0,0,0),duration=clip_dur).set_opacity(0.25)
            clip = CompositeVideoClip([clip, dark_ov])

        clips.append(clip)
        time_used += clip_dur
        media_count += 1

    # Outro
    outro_dur = min(3.0, max(0.5, total_dur-time_used))
    clips.append(create_chapter_card("Subscribe for Daily Mysteries 🔴", duration=outro_dur))

    print(f"  🔗 Joining {len(clips)} clips...")

    try:
        video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print(f"  ⚠️ compose failed: {e}, trying chain...")
        video = concatenate_videoclips(clips, method="chain")

    # Trim/pad to exact audio length
    if video.duration > total_dur + 0.5:
        video = video.subclip(0, total_dur)
    elif video.duration < total_dur - 1.0:
        gap  = total_dur - video.duration
        pad  = ImageClip(video.get_frame(video.duration-0.1), duration=gap)
        video = concatenate_videoclips([video, pad])

    # Watermark
    def wm_frame(t):
        img  = Image.new("RGBA",(W,36),(0,0,0,0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",20)
        except:
            font = ImageFont.load_default()
        draw.text((18,8), f"🔴 {config.CHANNEL_NAME}  •  New case every day",
                  font=font, fill=(210,210,210,135))
        return np.array(img.convert("RGB"))

    wm = VideoClip(wm_frame, duration=total_dur)\
           .set_position(("left","bottom")).set_opacity(0.42)

    final = CompositeVideoClip([video, wm]).set_audio(audio)

    out = os.path.join(config.OUTPUT_FOLDER,"final_video.mp4")
    print("  💾 Writing final video...")
    final.write_videofile(
        out, fps=24, codec="libx264", audio_codec="aac",
        threads=4, preset="ultrafast", bitrate="4000k", logger=None)

    print(f"✅ Documentary assembled! ({total_dur/60:.1f} mins)")
    return out


# ============================================
# STEP 11 - THUMBNAIL
# ============================================

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 11: Creating thumbnail...")
    W, H = 1280, 720
    mood = metadata.get("thumbnail_mood","dark")
    thumb = os.path.join(config.OUTPUT_FOLDER,"thumbnail.jpg")

    if image_paths:
        try:
            img = Image.open(image_paths[0]).convert("RGB").resize((W,H),Image.LANCZOS)
            img = ImageEnhance.Brightness(img).enhance(0.28)
            img = ImageEnhance.Color(img).enhance(0.5)
        except:
            img = Image.new("RGB",(W,H),(10,0,0))
    else:
        img = Image.new("RGB",(W,H),(10,0,0))

    tints = {"dark":(20,0,0,75),"red":(65,0,0,90),"blue":(0,0,55,80),"dramatic":(35,0,45,80)}
    tint  = Image.new("RGBA",(W,H), tints.get(mood,(20,0,0,75)))
    img   = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    draw  = ImageDraw.Draw(img)

    try:
        f_xl = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",90)
        f_lg = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",52)
        f_sm = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",26)
    except:
        f_xl = f_lg = f_sm = ImageFont.load_default()

    draw.text((28,18), "🔴 "+config.CHANNEL_NAME.upper(), font=f_sm, fill=(210,210,210))

    txt   = metadata.get("thumbnail_text","SHOCKING CASE").upper()
    words = txt.split()
    lines = ([txt] if len(words)<=2
             else [" ".join(words[:len(words)//2]), " ".join(words[len(words)//2:])])

    y = H//2 - len(lines)*102//2 - 10
    for line in lines:
        b = draw.textbbox((0,0),line,font=f_xl)
        x = (W-(b[2]-b[0]))//2
        for s in range(8,0,-1):
            draw.text((x+s,y+s),line,font=f_xl,fill=(0,0,0))
        for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            draw.text((x+dx,y+dy),line,font=f_xl,fill=(215,0,0))
        draw.text((x,y),line,font=f_xl,fill=(255,255,255))
        y += 104

    sub = story["title"][:45]+("..." if len(story["title"])>45 else "")
    b   = draw.textbbox((0,0),sub,font=f_lg)
    draw.text(((W-(b[2]-b[0]))//2, y+10), sub, font=f_lg, fill=(230,185,0))

    draw.rectangle([(0,H-58),(W,H)],fill=(12,0,0))
    draw.rectangle([(0,H-60),(W,H-58)],fill=(200,0,0))
    draw.text((28,H-44),"TRUE CRIME  •  UNSOLVED MYSTERIES  •  DARK CASES",font=f_sm,fill=(155,155,155))

    img.save(thumb,"JPEG",quality=95)
    print("✅ Thumbnail created!")
    return thumb


# ============================================
# STEP 12 - UPLOAD
# ============================================

def upload_to_youtube(video_path, thumbnail_path, metadata):
    print("\n📤 Step 12: Uploading to YouTube...")

    td  = json.loads(config.YOUTUBE_TOKEN)
    creds = Credentials(
        token=td.get("token"), refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri"), client_id=td.get("client_id"),
        client_secret=td.get("client_secret"), scopes=td.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request()); print("🔄 Token refreshed!")

    yt = build("youtube","v3",credentials=creds)

    body = {
        "snippet": {
            "title":                metadata.get("title","True Crime")[:100],
            "description":          metadata.get("full_description",""),
            "tags":                 metadata.get("tags_list",[])[:500],
            "categoryId":           "25",
            "defaultLanguage":      "en",
            "defaultAudioLanguage": "en"
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False}
    }

    media = MediaFileUpload(video_path,chunksize=-1,resumable=True,mimetype="video/mp4")
    resp  = yt.videos().insert(part="snippet,status",body=body,media_body=media).execute()
    vid   = resp.get("id")
    print(f"✅ Video uploaded! ID: {vid}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(videoId=vid,
                media_body=MediaFileUpload(thumbnail_path,mimetype="image/jpeg")).execute()
            print("✅ Thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail: {e}")

    pinned = metadata.get("pinned_comment","What do YOU think happened? 👇")
    try:
        yt.commentThreads().insert(
            part="snippet",
            body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{
                "textOriginal":f"🔴 {pinned}\n\n💬 Every theory welcome!\n🔔 Subscribe → {config.CHANNEL_HANDLE}"
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
    print("="*55)
    print("🚀 ARCHIVE OF ENIGMAS — Documentary Pipeline v4")
    print("="*55)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    try:
        story                = fetch_story()
        script, metadata     = generate_script(story)
        img_queries, vid_queries = extract_keywords(story)
        image_paths          = fetch_images(img_queries, target=18)
        video_clips          = fetch_videos(vid_queries, target=10)
        audio_path           = generate_voiceover(script)
        thumbnail_path       = create_thumbnail(image_paths, metadata, story)
        video_path           = assemble_documentary_video(
                                   audio_path, image_paths, video_clips, metadata, story)
        video_id             = upload_to_youtube(video_path, thumbnail_path, metadata)

        print("\n"+"="*55)
        print(f"🎉 SUCCESS! https://youtube.com/watch?v={video_id}")
        print(f"📸 Images  : {len(image_paths)}")
        print(f"🎥 Videos  : {len(video_clips)}")
        print(f"📊 Title   : {metadata.get('title')}")
        print("="*55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback; traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
