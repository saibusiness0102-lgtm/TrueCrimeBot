# ============================================
# ARCHIVE OF ENIGMAS — DOCUMENTARY BOT v12 GROWTH
# 20-min videos | 1080p | English-First | Peak SEO
# Fixes v12 (this version):
#   - Script prompts now GROUNDED: only narrate what's in the source
#     content, no invented witness quotes / forensic detail / scene
#     specifics. Lower temperature for less embellishment.
#   - Burned-in captions using edge-tts word-boundary timestamps.
#   - Audio mastering pass (ffmpeg loudnorm) for consistent voice level.
#   - Varied cut pacing (no more fixed 8s/14s every slot) + a
#     procedural timeline-card graphic mixed into chapter breaks.
#   - REMOVED the synthetic "engagement" comment that simulated
#     viewer debate — kept only the genuinely useful chapters comment.
# Carried over from v11:
#   - Wikipedia-first (no more multilingual RSS stories)
#   - Bebas Neue font download for viral thumbnails
#   - Stronger title prompt with proven formats
#   - Better Wikipedia case list (more viral/trending cases)
#   - Upload history tracked across ALL languages
#
# REQUIRES: ffmpeg installed on the runner (for audio mastering).
#   GitHub Actions: add a step `sudo apt-get update && sudo apt-get
#   install -y ffmpeg` before the Python step.
# ============================================

import os
import re
import sys
import json
import math
import random
import shutil
import asyncio
import subprocess
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import edge_tts
from groq import Groq
import feedparser
import wikipedia
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import gc
import config

# ============================================
# PIL ANTIALIAS FIX (Pillow 10+ compatibility)
# ============================================
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# ============================================
# FONT DOWNLOAD — Bebas Neue for viral thumbnails
# ============================================

def ensure_bebas_font():
    """Download Bebas Neue once per run — tries multiple URLs."""
    import urllib.request
    path = config.FONT_CACHE_PATH
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    urls = getattr(config, "BEBAS_NEUE_URLS", []) or [getattr(config, "BEBAS_NEUE_URL", "")]
    for url in urls:
        if not url: continue
        try:
            print(f"  🔤 Downloading Bebas Neue font...")
            urllib.request.urlretrieve(url, path)
            if os.path.exists(path) and os.path.getsize(path) > 10000:
                print("  ✅ Bebas Neue downloaded!")
                return path
        except Exception as e:
            print(f"  ⚠️ Font URL failed ({e}), trying next...")
    print("  ⚠️ All font URLs failed — using LiberationSans fallback")
    return None

BEBAS_FONT_PATH = None   # set on first run in run_pipeline()

# ============================================
# TITLE & TOPIC DIVERSITY GUARD
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

def update_history(title, topic_type, keywords, lang="en"):
    h = load_history()
    entry = f"[{lang.upper()}] {title}"
    h["recent_titles"]   = ([entry] + h["recent_titles"])[:20]
    h["recent_topics"]   = ([topic_type] + h["recent_topics"])[:10]
    h["recent_keywords"] = (keywords + h["recent_keywords"])[:30]
    save_history(h)

_CRIME_NOUNS = {
    "vanish","vanishes","vanished","missing","disappear","disappeared",
    "murder","murdered","killer","killed","killing","kill","dead","death",
    "rape","raped","assault","assaulted","kidnap","kidnapped","abduct",
    "found","body","hunt","case","mom","mother","father","dad","daughter",
    "son","child","children","woman","man","girl","boy","teen","wife",
    "husband","family","couple","sister","brother","baby","infant",
}

_RSS_CRIME_REQUIRED = {
    "murder","killed","killing","homicide","manslaughter","stabbed","shooting","shot",
    "missing","disappeared","vanished","abducted","kidnapped","kidnapping",
    "arrested","convicted","sentenced","charged","indicted","suspect",
    "victim","crime","robbery","assault","rape","sexual assault","molested",
    "trafficking","serial killer","cold case","investigation","forensic",
    "fraud","scam","embezzle","ponzi","poisoned","poisoning",
}

def is_crime_story(title, content):
    text = (title + " " + content).lower()
    return any(kw in text for kw in _RSS_CRIME_REQUIRED)

def _title_key_nouns(title):
    return {w.strip("'\".,!?") for w in title.lower().split()} & _CRIME_NOUNS

def is_too_similar(title, topic_type):
    h = load_history()
    recent5 = h["recent_topics"][:5]
    max_same = getattr(config, "MAX_SAME_TOPIC_IN_5", 1)
    if recent5.count(topic_type) >= max_same:
        print(f"  ⚠️  Topic '{topic_type}' appeared {recent5.count(topic_type)}x. Skipping.")
        return True
    new_nouns = _title_key_nouns(title)
    for old_title in h["recent_titles"][:15]:
        old_nouns = _title_key_nouns(old_title)
        overlap   = new_nouns & old_nouns
        if len(overlap) >= 2:
            print(f"  ⚠️  Too similar to: '{old_title}' (shared: {overlap}). Skipping.")
            return True
        if title.lower().split()[:3] == old_title.lower().split()[:3]:
            print(f"  ⚠️  Title starts identically to: '{old_title}'. Skipping.")
            return True
    return False

def detect_topic_type(text):
    text = text.lower()
    if any(w in text for w in ["serial","spree","multiple victim"]):    return "serial"
    if any(w in text for w in ["rape","sexual assault","molest"]):       return "assault"
    if any(w in text for w in ["caste","dalit","honor killing","dowry"]): return "caste"
    if any(w in text for w in ["poison","poisoning","arsenic","cyanide"]): return "poison"
    if any(w in text for w in ["fraud","scam","ponzi","embezzle","con"]): return "fraud"
    if any(w in text for w in ["missing","disappear","vanish"]):         return "missing"
    if any(w in text for w in ["murder","homicide","kill","stabbed","shot","strangled"]): return "murder"
    if any(w in text for w in ["theft","heist","robbery","stolen","burglar"]): return "heist"
    if any(w in text for w in ["cult","sect","ritual","sacrifice"]):     return "cult"
    if any(w in text for w in ["unsolved","mystery","unknown","unidentified"]): return "unsolved"
    if any(w in text for w in ["cold case","decades","reopened"]):       return "coldcase"
    if any(w in text for w in ["conspiracy","cover","government","corrupt"]): return "conspiracy"
    if any(w in text for w in ["kidnap","abduct","ransom","hostage"]):   return "kidnap"
    return "other"


# ============================================
# STEP 1 — FETCH STORY
# ============================================

def fetch_from_rss():
    rss_feeds = [
        "https://www.crimeonline.com/feed/",
        "https://www.oxygen.com/rss.xml",
        "https://www.investigationdiscovery.com/feed",
        "https://abcnews.go.com/US/feed",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Crime.xml",
        "https://www.theguardian.com/uk/crime/rss",
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://feeds.feedburner.com/ndtvnews-india-news",
        "https://abcnews.go.com/Court/feed",
        "https://lawandcrime.com/feed/",
    ]
    random.shuffle(rss_feeds)
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:10]
            random.shuffle(entries)
            for entry in entries:
                content = entry.get("summary","") or entry.get("description","")
                if len(content) > 300:
                    if not is_crime_story(entry.title, content):
                        print(f"  ⏭️  Skipping non-crime story: {entry.title[:60]}")
                        continue
                    topic = detect_topic_type(entry.title + " " + content)
                    if not is_too_similar(entry.title, topic):
                        print(f"✅ RSS story: {entry.title}")
                        return {"title": entry.title, "content": content[:5000], "source": "RSS", "topic": topic}
        except Exception as e:
            print(f"  ⚠️ RSS {feed_url[:40]}: {e}")
    return None

def fetch_from_wikipedia():
    h = load_history()
    used_keywords = set(h.get("recent_keywords", []))
    cases = [
        "Zodiac Killer","Jack the Ripper","Golden State Killer","Ted Bundy",
        "Jeffrey Dahmer","John Wayne Gacy","BTK killer","Gary Ridgway",
        "Samuel Little","Ed Kemper","Richard Ramirez","Dean Corll",
        "Andrei Chikatilo","Aileen Wuornos","Harold Shipman","H. H. Holmes",
        "Charles Manson","Pedro Lopez","Luis Garavito","John Edward Robinson",
        "Israel Keyes","Randy Kraft","Gerard Schaefer","Dennis Nilsen",
        "Peter Sutcliffe","Robert Pickton","Paul Bernardo","Herb Baumeister",
        "Chris Watts murders","JonBenet Ramsey","Gabby Petito case",
        "Delphi murders","Amanda Knox","Steven Avery","Scott Peterson case",
        "Menendez brothers","Pamela Smart","Robert Durst",
        "Phil Spector murder","Oscar Pistorius trial","West Memphis Three",
        "Making a Murderer","OJ Simpson trial","Casey Anthony trial",
        "Drew Peterson","Murder of Meredith Kercher",
        "Watts family murders","Brian Laundrie","Rust film set shooting",
        "Alex Murdaugh murders","Chad Daybell murders",
        "Murder of Laci Peterson","Shayna Hubers case",
        "Kyle Unger wrongful conviction","Kevin Cooper case",
        "Adnan Syed case","Serial podcast murder",
        "Black Dahlia murder","Villisca axe murders","Hinterkaifeck murders",
        "Axeman of New Orleans","Cleveland torso murderer","Lizzie Borden",
        "Tylenol murders","Tamam Shud case","Dyatlov Pass incident",
        "Isdal Woman","Beaumont children disappearance","Sodder children disappearance",
        "Elisa Lam case","Max Headroom broadcast intrusion",
        "Boy in the box Philadelphia","Zodiac ciphers",
        "Marilyn Monroe death","Babushka Lady assassination",
        "Paige Rouse disappearance","Maura Murray disappearance",
        "Springfield Three disappearance","Doe Network case",
        "Asha Degree disappearance","Brandon Lawson case",
        "Jonestown massacre","Heaven's Gate cult","NXIVM cult",
        "Aum Shinrikyo","Branch Davidians Waco","The Family cult Australia",
        "Order of the Solar Temple","Rajneeshee bioterror attack",
        "Children of God cult","Peoples Temple","The Ant Hill Kids",
        "DB Cooper","Isabella Stewart Gardner Museum theft",
        "Great Train Robbery 1963","Antwerp diamond heist",
        "Hatton Garden heist","Banco Central Brazil robbery",
        "Dunbar Armored robbery","Lufthansa heist 1978",
        "French Connection drug smuggling","Pink Panthers jewel thieves",
        "Bernie Madoff Ponzi scheme","Enron scandal",
        "Elizabeth Holmes Theranos","Anna Sorokin fraud",
        "Harshad Mehta scam","Vijay Mallya fraud",
        "Nirav Modi diamond fraud","Frank Abagnale",
        "Sam Bankman-Fried FTX collapse","WeWork Adam Neumann fraud",
        "Billy McFarland Fyre Festival","Trevor Milton Nikola fraud",
        "Jaycee Dugard kidnapping","Elizabeth Smart kidnapping",
        "Ariel Castro kidnappings","Natascha Kampusch kidnapping",
        "Patty Hearst kidnapping","Lindbergh kidnapping",
        "Fritzl case","Colleen Stan captivity","Mary Vincent attack",
        "Alexander Litvinenko poisoning","Salisbury Novichok attack",
        "Georgi Markov assassination","Graham Young poisoner",
        "Marie Besnard poison murders","Nannie Doss poisoner",
    ]
    available = [c for c in cases if c.lower() not in used_keywords]
    if not available:
        available = cases
    random.shuffle(available)
    for case in available[:5]:
        try:
            topic = detect_topic_type(case)
            if is_too_similar(case, topic):
                continue
            print(f"📖 Wikipedia: {case}")
            page = wikipedia.page(case, auto_suggest=True)
            return {"title": page.title, "content": page.content[:6000], "source": "Wikipedia", "topic": topic}
        except Exception as e:
            print(f"  ⚠️ Wikipedia '{case}': {e}")
    return {"title": "The Zodiac Killer", "content": "The Zodiac Killer was an unidentified serial killer active in Northern California during the late 1960s and early 1970s.", "source": "Fallback", "topic": "unsolved"}

def fetch_story():
    print("\n🔍 Step 1: Fetching story...")
    story = fetch_from_rss() if not config.PREFER_WIKIPEDIA else None
    return story or fetch_from_wikipedia()


# ============================================
# STEP 2 — EXTRACT KEYWORDS
# ============================================

def extract_keywords(story):
    title   = story["title"].lower()
    content = (story.get("content","") or "").lower()
    text    = title + " " + content

    TOPIC_IMAGES = {
        "murder": [
            "bloody crime scene investigation","forensic scientist evidence gloves",
            "chalk outline floor crime","autopsy table dark dramatic",
            "detective holding evidence bag","police tape house crime scene",
            "court room judge gavel","victim memorial flowers candles",
            "crime scene photo evidence board","prosecutor evidence courtroom dark",
        ],
        "missing": [
            "missing person flyer post","search party flashlights forest night",
            "empty swing set abandoned playground","milk carton missing child vintage",
            "search rescue team dogs forest","abandoned child bedroom dark",
            "candle vigil memorial night","family crying grief dark",
            "detective studying map missing route","empty chair at table dark",
        ],
        "serial": [
            "serial killer mugshot newspaper","detective crime board red string",
            "prison corridor cell dramatic","victims memorial wall photographs",
            "criminal profile document desk","FBI investigation files dark",
            "courtroom packed dramatic verdict","dark silhouette figure stalking",
            "phone call night dark window","evidence map pins locations crime",
        ],
        "heist": [
            "vault door steel bank dramatic","gold bars stacks dramatic",
            "masked robber dark dramatic","security camera footage grainy",
            "money counting table dramatic","getaway car dramatic night",
            "briefcase handcuff arrest","police chase night urban",
            "stolen jewelry dramatic close","auction house valuable art dramatic",
        ],
        "cult": [
            "candles ritual dark ceremony","abandoned cult compound building",
            "robed figures ceremony dark forest","cult leader crowd podium dramatic",
            "bible torn pages dark dramatic","isolated rural compound aerial",
            "brainwashing propaganda poster vintage","survivor testimony courtroom dramatic",
            "mass grave dark documentary","FBI raid compound dramatic",
        ],
        "unsolved": [
            "cold case file folder dusty","unanswered questions chalkboard dark",
            "detective staring wall evidence","old crime scene photo sepia",
            "question mark shadow dark","file cabinet overflowing cases",
            "mystery door locked dark","vintage newspaper headline unsolved",
            "detective old evidence box","shadow figure foggy night vintage",
        ],
        "conspiracy": [
            "classified document redacted black","surveillance camera network dark",
            "government building night dramatic","conspiracy board newspaper clippings",
            "shadowy figure silhouette dramatic","newspaper headline cover up dark",
            "briefcase exchange dark alley","hacker computer screen dark",
            "secret meeting dark room","wiretap phone surveillance dramatic",
        ],
        "coldcase": [
            "dusty evidence box files cold case","old polaroid photo faded dark",
            "detective reopening old case files","vintage crime scene photograph",
            "decades old newspaper archive","retired detective case notes dark",
            "forensic DNA lab modern dramatic","family seeking justice courtroom",
            "cold storage evidence room dark","witness testimony years later dramatic",
        ],
    }

    TOPIC_VIDEOS = {
        "murder": [
            "ambulance emergency lights night","police investigation crime scene",
            "courtroom gavel dramatic close","prison sentence judge dramatic",
            "forensic team working crime scene","detective interviewing witness",
        ],
        "missing": [
            "search helicopter forest aerial","search party walking field night",
            "missing poster blowing wind","empty road driving night dramatic",
            "vigil candles crowd night","family reunion emotional dramatic",
        ],
        "serial": [
            "police car convoy dramatic","prison transfer van dramatic",
            "courtroom packed trial dramatic","detective profiling board dramatic",
            "news reporter crime scene live","handcuffed perp walk dramatic",
        ],
        "heist": [
            "bank vault door dramatic","police chase urban night",
            "money counting dramatic","getaway car speeding night",
            "police roadblock dramatic","news helicopter aerial dramatic",
        ],
        "cult": [
            "forest dark night dramatic","crowd chanting dramatic",
            "abandoned building interior dark","smoke fire ritual dramatic",
            "documentary interview dramatic","police raid building dramatic",
        ],
        "default": [
            "dark rainy city night","fog forest dark eerie",
            "storm lightning dramatic dark","dark ocean waves night",
            "fire dark night dramatic","dark road night driving",
            "smoke dark atmospheric","rain window dark dramatic",
            "dark alley night cinematic","thunder clouds dark dramatic",
        ],
    }

    UNIVERSAL_IMAGES = [
        "dark dramatic cinematic shadows","vintage sepia photograph dark room",
        "candlelight dark atmospheric room","old typewriter dark dramatic",
        "magnifying glass clue mystery","shadow window rain night",
        "dark cemetery fog night","old clock dramatic dark",
        "newspaper archive reading dark","leather journal pen dark desk",
        "radio vintage dark room dramatic","telephone vintage dramatic dark",
    ]

    topic = story.get("topic", "other")
    if topic == "other":
        if any(w in text for w in ["serial","spree"]): topic = "serial"
        elif any(w in text for w in ["murder","kill","homicide"]): topic = "murder"
        elif any(w in text for w in ["missing","disappear","vanish"]): topic = "missing"
        elif any(w in text for w in ["heist","robbery","theft"]): topic = "heist"
        elif any(w in text for w in ["cult","sect","ritual"]): topic = "cult"
        elif any(w in text for w in ["conspiracy","cover","government"]): topic = "conspiracy"
        elif any(w in text for w in ["cold case","decade","unsolved"]): topic = "coldcase"

    topic_imgs = TOPIC_IMAGES.get(topic, TOPIC_IMAGES.get("unsolved", []))
    topic_vids = TOPIC_VIDEOS.get(topic, TOPIC_VIDEOS["default"])

    image_queries = []
    for i, q in enumerate(topic_imgs):
        image_queries.append(q)
        if i < len(UNIVERSAL_IMAGES):
            image_queries.append(UNIVERSAL_IMAGES[i])

    video_queries = topic_vids + TOPIC_VIDEOS["default"]

    random.shuffle(image_queries)
    random.shuffle(video_queries)

    seen = set()
    image_queries = [q for q in image_queries if not (q in seen or seen.add(q))]
    video_queries = [q for q in video_queries if not (q in seen or seen.add(q))]

    print(f"  🎨 Visual theme: '{topic}' ({len(image_queries)} img queries, {len(video_queries)} vid queries)")
    return image_queries[:30], video_queries[:16]


# ============================================
# STEP 3 — FETCH IMAGES (1080p target)
# ============================================

def fetch_images(queries, target=24):
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
                url = photo["src"].get("original", photo["src"]["large2x"])
                r   = requests.get(url, timeout=20)
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

def fetch_videos_pexels(queries, target, vid_dir):
    headers  = {"Authorization": config.PEXELS_API_KEY}
    videos   = []
    used_ids = set()
    for query in queries:
        if len(videos) >= target: break
        try:
            resp = requests.get(
                f"https://api.pexels.com/videos/search?query={query}&per_page=3&min_duration=5&max_duration=30",
                headers=headers, timeout=10)
            items = resp.json().get("videos", [])
            for item in items:
                if len(videos) >= target: break
                if item["id"] in used_ids: continue
                used_ids.add(item["id"])
                files = sorted(item["video_files"], key=lambda x: x.get("width",0), reverse=True)
                chosen = next((f for f in files if 1080 <= f.get("height",0) <= 1080), None) or \
                         next((f for f in files if f.get("width",0) <= 1920), files[0] if files else None)
                if not chosen: continue
                path = os.path.join(vid_dir, f"vid_{len(videos):03d}.mp4")
                r = requests.get(chosen["link"], stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    videos.append({"path": path, "duration": item.get("duration",10)})
                    print(f"  🎥 [Pexels] {len(videos)}: {query[:35]}")
        except Exception as e:
            print(f"  ⚠️ Pexels video error: {e}")
    return videos

def fetch_videos_pixabay(queries, target, vid_dir, start_idx=0):
    if not config.PIXABAY_API_KEY:
        return []
    videos   = []
    used_ids = set()
    for query in queries:
        if len(videos) >= target: break
        try:
            resp = requests.get(
                f"https://pixabay.com/api/videos/?key={config.PIXABAY_API_KEY}"
                f"&q={requests.utils.quote(query)}&per_page=3&min_duration=5&max_duration=30&video_type=film",
                timeout=10)
            items = resp.json().get("hits", [])
            for item in items:
                if len(videos) >= target: break
                if item["id"] in used_ids: continue
                used_ids.add(item["id"])
                vids = item.get("videos", {})
                chosen_url = vids.get("large",{}).get("url") or vids.get("medium",{}).get("url") or vids.get("small",{}).get("url")
                if not chosen_url: continue
                dur = item.get("duration", 10)
                idx = start_idx + len(videos)
                path = os.path.join(vid_dir, f"vid_{idx:03d}.mp4")
                r = requests.get(chosen_url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    videos.append({"path": path, "duration": dur})
                    print(f"  🎥 [Pixabay] {len(videos)}: {query[:35]}")
        except Exception as e:
            print(f"  ⚠️ Pixabay video error: {e}")
    return videos

def fetch_videos(queries, target=14):
    print(f"\n🎥 Fetching {target} atmospheric video clips...")
    vid_dir  = os.path.join(config.OUTPUT_FOLDER, "videos")
    if os.path.exists(vid_dir): shutil.rmtree(vid_dir)
    os.makedirs(vid_dir, exist_ok=True)

    videos = fetch_videos_pexels(queries, target, vid_dir)

    if len(videos) < target and config.PIXABAY_API_KEY:
        needed = target - len(videos)
        print(f"  🔄 Getting {needed} more from Pixabay...")
        extra = fetch_videos_pixabay(queries, needed, vid_dir, start_idx=len(videos))
        videos.extend(extra)

    print(f"✅ {len(videos)} video clips fetched!")
    return videos


# ============================================
# GROQ RATE-LIMIT RETRY WRAPPER
# ============================================
import time as _time

def groq_create_with_retry(client, max_retries=6, **kwargs):
    from groq import RateLimitError
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            err_str = str(e)
            if "tokens per day" in err_str or "TPD" in err_str:
                print("🚫 Groq daily token quota (100k TPD) exhausted.")
                print("   ➡  Upgrade at https://console.groq.com/settings/billing")
                print("   ⏭  Skipping today's run — will retry tomorrow.")
                sys.exit(0)
            if attempt == max_retries - 1:
                raise
            match = re.search(r'try again in ([\d.]+)s', err_str)
            if match:
                wait = float(match.group(1)) + 2
            else:
                wait = min(5 * 2 ** attempt, 120)
            print(f"  ⏳ Rate limit hit — waiting {wait:.1f}s then retrying "
                  f"(attempt {attempt + 1}/{max_retries})...")
            _time.sleep(wait)


# ============================================
# STEP 5 — GENERATE SCRIPT (GROUNDED, 20-min TARGET)
# ============================================
# CHANGED: every chapter instruction now forces the model to base
# claims only on the provided context and to flag anything not in the
# source as unknown/speculated rather than inventing it. Temperature
# lowered from 0.88 -> 0.75 to reduce embellishment. Structure
# (5 chapters, ~4 paragraphs of 5 sentences, [PAUSE] joins, retry-if-
# too-short logic) is unchanged so duration math and downstream
# chunking still work exactly as before.
# ============================================

GROUNDING_RULE = (
    "CRITICAL ACCURACY RULE: Base every factual claim ONLY on the context "
    "provided below. Do not invent names, quotes, dialogue, exact times, "
    "or forensic details that are not in the context. You MAY use general "
    "atmospheric/scene-setting language (weather, mood, tension) that is "
    "not fact-checkable, but you must NOT present invented specifics as "
    "fact. If the context does not cover something, say it is unknown or "
    "undocumented rather than stating it outright."
)

def generate_script(story, language="en"):
    import time as _time
    print(f"\n✍️  Step 5: Generating grounded 20-min script ({language.upper()})...")
    h = load_history()
    recent_titles_str = ", ".join(h["recent_titles"][:5]) if h["recent_titles"] else "none yet"
    client     = Groq(api_key=config.GROQ_API_KEY)
    fast_model = getattr(config, "GROQ_MODEL_FAST", config.GROQ_MODEL)

    lang_instruction = ""
    if language != "en":
        lang_info = config.SUPPORTED_LANGUAGES.get(language, {})
        lang_instruction = f"Write ENTIRELY in {lang_info.get('name', 'English')} language."

    case    = story["title"]
    context = story.get("content", "")[:3000]

    CHAPTERS = [
        {
            "name": "HOOK",
            "instruction": f"""You are the narrator for a true crime YouTube channel.
{GROUNDING_RULE}
Case: {case}
Context: {context[:900]}
{lang_instruction}

Write EXACTLY 4 paragraphs. Each paragraph must have EXACTLY 5 sentences.
That is 20 sentences total. Do not stop before 20 sentences.

Paragraph 1: Open with the most consequential moment IN THE CONTEXT. Use only dates/locations that appear in the context — describe generally rather than inventing a specific if the context doesn't give one.
Paragraph 2: Describe the scene using only atmosphere/mood language, not invented facts.
Paragraph 3: Describe the victim or perpetrator using only traits stated in the context.
Paragraph 4: Summarize what is actually documented about how the case became known — no invented witness quotes.
Paragraph 5: Say these words: "Before we go further — hit subscribe and the bell. We post new cases every single day."
Paragraph 6: "Let me take you back to the beginning of what's documented about this case..."
Paragraph 7: Introduce the backstory, grounded in the context only.
Paragraph 8: Transition line setting up the background chapter.

IMPORTANT: Write ONLY the spoken words. No labels. No markdown. No chapter headings."""
        },
        {
            "name": "BACKGROUND",
            "instruction": f"""You are the narrator for a true crime YouTube channel.
{GROUNDING_RULE}
Case: {case}
Context: {context[:1800]}
{lang_instruction}

Write EXACTLY 4 paragraphs. Each paragraph must have EXACTLY 5 sentences.
That is 20 sentences total. Do not stop before 20 sentences.

Paragraph 1: Who was the central person in this case, per the context — name, age, location if given.
Paragraph 2: Documented facts about their daily life — job, family — omit anything not in the context.
Paragraph 3: General, non-invented framing of how they were perceived by others.
Paragraph 4: Relationships mentioned in the context — who they were close to.
Paragraph 5: Documented events in the weeks or months leading up to the incident.
Paragraph 6: Any documented warning signs — if none are in the context, say the record is unclear rather than inventing one.
Paragraph 7: Who is documented as having noticed or responded, or state if this isn't documented.
Paragraph 8: End with a genuine question inviting the viewer to keep watching.

IMPORTANT: Write ONLY the spoken words. No labels. No markdown."""
        },
        {
            "name": "THE CASE",
            "instruction": f"""You are the narrator for a true crime YouTube channel.
{GROUNDING_RULE}
Case: {case}
Context: {context}
{lang_instruction}

Write EXACTLY 4 paragraphs. Each paragraph must have EXACTLY 5 sentences.
That is 20 sentences total. Do not stop before 20 sentences.

Paragraph 1: Set the scene using only documented date, time, location, circumstances.
Paragraph 2: The documented sequence of events leading up to the incident.
Paragraph 3: What is documented to have happened, step by step, without invented detail.
Paragraph 4: The single most notable documented fact — not an invented "shocking" detail.
Paragraph 5: Documented immediate reactions and who discovered what happened.
Paragraph 6: Ask viewers: "Comment below — what do you think really happened here?"
Paragraph 7: The documented scale or scope of the case as it became clear.
Paragraph 8: End with a transition into the investigation, grounded only in the context.

IMPORTANT: Write ONLY the spoken words. No labels. No markdown."""
        },
        {
            "name": "INVESTIGATION",
            "instruction": f"""You are the narrator for a true crime YouTube channel.
{GROUNDING_RULE}
Case: {case}
Context: {context}
{lang_instruction}

Write EXACTLY 4 paragraphs. Each paragraph must have EXACTLY 5 sentences.
That is 20 sentences total. Do not stop before 20 sentences.

Paragraph 1: How police or investigators are documented to have first responded.
Paragraph 2: The key documented piece of evidence, if the context describes one.
Paragraph 3: Documented suspects — only if named in the context; otherwise describe the investigative approach generally.
Paragraph 4: Any documented false leads or dead ends in the investigation.
Paragraph 5: Documented setbacks or mistakes, if described in the context.
Paragraph 6: How the community is documented to have reacted.
Paragraph 7: Ask viewers: "Drop your theory in the comments — who do YOU think was responsible?"
Paragraph 8: The documented turning point — or state plainly that the case remained unresolved if that's accurate.

IMPORTANT: Write ONLY the spoken words. No labels. No markdown."""
        },
        {
            "name": "OUTCOME AND OUTRO",
            "instruction": f"""You are the narrator for a true crime YouTube channel.
{GROUNDING_RULE}
Case: {case}
Context: {context}
{lang_instruction}

Write EXACTLY 4 paragraphs. Each paragraph must have EXACTLY 5 sentences.
That is 20 sentences total. Do not stop before 20 sentences.

Paragraph 1: The documented resolution, verdict, or current status — including "unsolved" or "cold case" if that is accurate. Do not invent a resolution that isn't in the context.
Paragraph 2: Further documented detail on that outcome.
Paragraph 3: What is documented about what happened to the key people afterward.
Paragraph 4: Documented broader impact, only if the context describes one.
Paragraph 5: The lasting significance of the case, framed honestly — say if the impact is unclear or undocumented.
Paragraph 6: A genuine discussion question about a documented ambiguity in the case.
Paragraph 7: A second discussion question about a different documented angle.
Paragraph 8: "If this case interested you, hit subscribe — we post a new case every single day. Our next video is on screen right now. See you there."

IMPORTANT: Write ONLY the spoken words. No labels. No markdown."""
        },
    ]

    chapter_texts = []
    total_wc      = 0

    for i, ch in enumerate(CHAPTERS):
        print(f"  📝 Chapter {i+1}/5 [{ch['name']}]...")
        chapter_text = ""
        for attempt in range(4):
            try:
                resp = groq_create_with_retry(
                    client,
                    model=fast_model,
                    messages=[{"role": "user", "content": ch["instruction"]}],
                    max_tokens=1400,
                    temperature=0.75   # lowered from 0.88 to reduce embellishment
                )
                text = resp.choices[0].message.content.strip()
                wc   = len(text.split())
                if wc < 350 and attempt < 3:
                    print(f"     ⚠️ Too short ({wc} words), retrying {attempt+2}/4...")
                    _time.sleep(3)
                    continue
                chapter_text = text
                total_wc    += wc
                print(f"     ✅ {wc} words")
                break
            except Exception as e:
                print(f"     ⚠️ Attempt {attempt+1} failed: {e}")
                _time.sleep(5)

        if not chapter_text:
            print(f"     ❌ Chapter {i+1} failed — using placeholder")
            chapter_text = f"This chapter covers the {ch['name'].lower()} of the {case} case, based on publicly documented information."

        chapter_texts.append(chapter_text)
        if i < len(CHAPTERS) - 1:
            _time.sleep(2)

    script   = "\n\n[PAUSE]\n\n".join(chapter_texts)
    est_mins = total_wc // 150
    print(f"  📊 Total: {total_wc} words → ~{est_mins} min")

    if est_mins < 11:
        shortest_idx  = min(range(len(chapter_texts)), key=lambda x: len(chapter_texts[x].split()))
        shortest_name = CHAPTERS[shortest_idx]["name"]
        print(f"  ⚠️ Under 11 min — extending [{shortest_name}]...")
        try:
            ext = groq_create_with_retry(
                client,
                model=fast_model,
                messages=[{"role": "user", "content":
                    f"{GROUNDING_RULE}\n"
                    f"Write 8 more paragraphs of 5 sentences each continuing this section "
                    f"about {case}, based only on this context: {context}\n"
                    f"Add more documented detail and context — do not invent facts. "
                    f"Write ONLY spoken narration. {lang_instruction}"}],
                max_tokens=1400, temperature=0.75)
            ext_text = ext.choices[0].message.content.strip()
            chapter_texts[shortest_idx] += "\n\n" + ext_text
            script   = "\n\n[PAUSE]\n\n".join(chapter_texts)
            total_wc = len(script.split())
            print(f"  📊 Extended: {total_wc} words → ~{total_wc//150} min")
        except Exception as e:
            print(f"  ⚠️ Extension failed: {e}")

    # ── METADATA (grounded in the script itself, not free invention) ────────
    print("  🏷️  Generating metadata...")
    title_formats = "\n".join(f"  • {f}" for f in
                               getattr(config, "HIGH_PERFORMING_TITLE_FORMATS", []))
    meta_prompt = f"""Write YouTube metadata for a true crime video about: {case}
Base every claim ONLY on what a viewer would learn from this script — do not invent extra facts:
{script[:1500]}

{lang_instruction}
Avoid titles similar to: {recent_titles_str}

TITLE: (Under 70 chars. Must use one of:
{title_formats}
Must include real name or location. Factual — no invented superlatives beyond what's documented.)
DESCRIPTION: (200 words SEO-rich. What happened, why notable, key search terms)
TAGS: (25 comma-separated true crime search terms)
THUMBNAIL_TEXT: (2-4 ALL-CAPS specific words, grounded in documented facts)
THUMBNAIL_MOOD: dark
THUMBNAIL_STYLE: (1, 2, 3, or 4)
PINNED_COMMENT: (One genuine discussion question about a documented ambiguity)
COMMUNITY_POST: (40-word community post with poll)
CHAPTERS: (timestamps one per line format "0:00 Hook")"""

    metadata = {}
    try:
        meta_resp = groq_create_with_retry(
            client,
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": meta_prompt}],
            max_tokens=900, temperature=0.6)
        meta_raw = meta_resp.choices[0].message.content
        cur_key, cur_val = None, []
        for line in meta_raw.strip().split("\n"):
            matched = False
            for key in ["TITLE","DESCRIPTION","TAGS","THUMBNAIL_TEXT","THUMBNAIL_MOOD",
                        "THUMBNAIL_STYLE","PINNED_COMMENT","COMMUNITY_POST","CHAPTERS"]:
                if line.startswith(f"{key}:"):
                    if cur_key:
                        metadata[cur_key.lower()] = "\n".join(cur_val).strip()
                    cur_key = key
                    cur_val = [line.replace(f"{key}:", "").strip()]
                    matched = True
                    break
            if not matched and cur_key:
                cur_val.append(line)
        if cur_key:
            metadata[cur_key.lower()] = "\n".join(cur_val).strip()
    except Exception as e:
        print(f"  ⚠️ Metadata failed: {e}")

    metadata.setdefault("title", story["title"])
    metadata.setdefault("description", f"True crime: {story['title']}")
    metadata.setdefault("tags", "true crime,documentary,case files")
    metadata.setdefault("thumbnail_text", story["title"].upper()[:30])
    metadata.setdefault("thumbnail_mood", "dark")
    metadata.setdefault("thumbnail_style", random.choice(config.THUMBNAIL_STYLES))
    metadata.setdefault("pinned_comment", "What do you think happened here?")
    metadata.setdefault("community_post", f"New case: {story['title']}.")
    metadata["topic"] = story.get("topic", "default")

    # ── SHORTS (also grounded) ───────────────────────────────────────────────
    shorts_script = ""
    try:
        sh = groq_create_with_retry(
            client,
            model=fast_model,
            messages=[{"role": "user", "content":
                f"{GROUNDING_RULE}\n"
                f"Write a YouTube Shorts script about: {case}, based only on this context: {context[:1000]}\n"
                f"Exactly 3 paragraphs of 3 sentences each (9 sentences total, ~140 words). "
                f"Para 1: a factual, attention-grabbing opening line. "
                f"Para 2: the key documented facts. "
                f"Para 3: the documented outcome/status + 'Follow for more real cases.' "
                f"ONLY spoken words. {lang_instruction}"}],
            max_tokens=300, temperature=0.7)
        shorts_script = sh.choices[0].message.content.strip()
        print(f"  📱 Shorts: {len(shorts_script.split())} words")
    except Exception as e:
        print(f"  ⚠️ Shorts failed: {e}")

    # ── DESCRIPTION ──────────────────────────────────────────────────────────
    topic_key   = story.get("topic", "other")
    niche       = (config.NICHE_HASHTAGS.get(topic_key) or
                   config.NICHE_HASHTAGS.get("default", []))
    lang_suffix = config.SUPPORTED_LANGUAGES.get(language, {}).get("hashtag_suffix", "")
    trending    = getattr(config, "TRENDING_HASHTAGS", [])
    hashtags    = " ".join(config.BASE_HASHTAGS[:15] + niche[:5] + trending[:3]) + lang_suffix
    metadata["hashtags"] = hashtags

    topic_seo  = getattr(config, "TOPIC_SEO_KEYWORDS",    {}).get(topic_key, [])
    global_seo = getattr(config, "GLOBAL_SEO_TERMS",      [])
    lang_seo   = getattr(config, "LANGUAGE_SEO_KEYWORDS", {}).get(language, [])
    end_screen = getattr(config, "END_SCREEN_CTA",         {}).get(language, "")
    seo_block  = " | ".join(list(dict.fromkeys(
        topic_seo[:4] + global_seo[:4] + lang_seo[:4]))[:10])

    chapters_text = metadata.get("chapters",
        "0:00 Hook\n3:00 Background\n8:00 The Case\n14:00 Investigation\n19:00 Outcome")

    metadata["full_description"] = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters_text}

{end_screen}

🔔 Subscribe → {config.CHANNEL_HANDLE}
👍 Like if this case interested you
💬 Share your thoughts — we read every comment
🔕 Notifications on — new case every day

{hashtags}

─────────────────────────────────
{seo_block}
─────────────────────────────────

Sources: publicly available records and reporting.
© {config.CHANNEL_NAME} — Educational purposes only."""

    import re as _re
    year_m  = _re.findall(r'\b(19|20)\d{2}\b',
                           story.get("content","") + story.get("title",""))
    place_m = _re.findall(r'\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)\b',
                           story.get("title",""))
    place_m = [p for p in place_m if p not in
               ("The","She","He","They","What","Who","How","Why","This","That")][:3]
    raw_tags = [t.strip().lstrip("#") for t in metadata["tags"].split(",") if t.strip()]
    bonus    = ([f"true crime {y}" for y in list(dict.fromkeys(year_m))[:2]] +
                [f"{p} crime" for p in place_m])
    metadata["tags_list"] = (raw_tags + bonus)[:35]

    print(f"✅ Script: {total_wc} words (~{total_wc//150} min) | {metadata.get('title','?')[:55]}")
    return script.strip(), shorts_script, metadata


def translate_script(script, shorts_script, metadata, target_lang):
    """Unchanged from original — translates chapter-by-chapter to avoid truncation."""
    if target_lang == "en":
        return script, shorts_script, metadata

    lang_info = config.SUPPORTED_LANGUAGES.get(target_lang, {})
    lang_name = lang_info.get("name", target_lang)
    print(f"\n🌍 Translating to {lang_name} (chapter by chapter)...")

    client    = Groq(api_key=config.GROQ_API_KEY)
    fast_model = getattr(config, "GROQ_MODEL_FAST", config.GROQ_MODEL)

    chapters = [c.strip() for c in script.split("[PAUSE]") if c.strip()]
    print(f"  📚 Translating {len(chapters)} chapters...")

    translated_chapters = []
    for i, chapter in enumerate(chapters):
        print(f"  🌐 Chapter {i+1}/{len(chapters)} ({len(chapter.split())} words)...")
        for attempt in range(3):
            try:
                resp = groq_create_with_retry(
                    client,
                    model=fast_model,
                    messages=[{"role": "user", "content":
                        f"Translate this true crime narration to {lang_name}. "
                        f"Keep the exact tone and pacing, and do not add or invent content. "
                        f"Translate EVERY sentence — do not summarise or shorten. "
                        f"Return ONLY the translated text, nothing else:\n\n{chapter}"}],
                    max_tokens=1600, temperature=0.3)
                translated = resp.choices[0].message.content.strip()
                wc_orig = len(chapter.split())
                wc_trans = len(translated.split())
                if wc_trans < wc_orig * 0.5 and attempt < 2:
                    print(f"     ⚠️ Translation too short ({wc_trans}/{wc_orig} words), retry...")
                    continue
                translated_chapters.append(translated)
                print(f"     ✅ {wc_trans} words")
                break
            except Exception as e:
                print(f"     ⚠️ Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    translated_chapters.append(chapter)
        import time as _t2; _t2.sleep(1)

    translated_script = "\n\n[PAUSE]\n\n".join(translated_chapters)
    total_wc = len(translated_script.split())
    print(f"  ✅ Translation complete: {total_wc} words (~{total_wc//150} min)")

    meta_prompt = f"""Translate ALL of the following to {lang_name}.
Return ONLY a valid JSON object with these exact keys. No markdown, no extra text.

{{
  "title": "{metadata.get('title','').replace('"', '')}",
  "description": "{metadata.get('description','')[:400].replace('"', '')}",
  "shorts_script": "{(shorts_script or '').replace(chr(10), ' ').replace('"', '')[:500]}",
  "pinned_comment": "{metadata.get('pinned_comment','').replace('"', '')}",
  "community_post": "{metadata.get('community_post','').replace('"', '')}"
}}

Translate the values to {lang_name}. Return valid JSON only."""

    try:
        resp2 = groq_create_with_retry(
            client,
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": meta_prompt}],
            max_tokens=1500, temperature=0.3)
        raw = resp2.choices[0].message.content.strip()
        raw = re.sub(r'^```[a-z]*\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
        translated_meta = json.loads(raw)

        metadata = dict(metadata)
        metadata["title"]          = translated_meta.get("title", metadata["title"])
        metadata["description"]    = translated_meta.get("description", metadata["description"])
        metadata["pinned_comment"] = translated_meta.get("pinned_comment", metadata["pinned_comment"])
        metadata["community_post"] = translated_meta.get("community_post", metadata["community_post"])
        translated_shorts          = translated_meta.get("shorts_script", shorts_script)

        chapters_txt = metadata.get("chapters", "0:00 Hook")
        lang_suffix = lang_info.get("hashtag_suffix", "")
        trending = getattr(config, "TRENDING_HASHTAGS", [])
        hashtags = " ".join(config.BASE_HASHTAGS[:10] + trending[:3]) + lang_suffix
        metadata["hashtags"] = hashtags
        metadata["full_description"] = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters_txt}

🔔 Subscribe for daily true crime → {config.CHANNEL_HANDLE}
👍 Like if this case interested you
💬 Share your thoughts below
🔕 Turn on notifications so you never miss a case

{hashtags}

Sources: publicly available records and reporting.
© {config.CHANNEL_NAME} — Educational purposes only."""

    except Exception as e:
        print(f"  ⚠️ Metadata translation parse failed: {e} — using English metadata")
        translated_shorts = shorts_script

    print(f"✅ Translation to {lang_name} done!")
    return translated_script, translated_shorts, metadata


# ============================================
# STEP 6 — VOICEOVER WITH CAPTIONS + MASTERING
# ============================================
# CHANGED: now captures edge-tts word-boundary timestamps as it
# synthesizes each chunk, so we get burned-in captions "for free"
# from the same TTS call rather than a second transcription pass.
# Also runs the final audio through an ffmpeg loudnorm + light
# compression pass for consistent, professional voice level.
# Returns (audio_path, captions_path) — captions_path may be None if
# something failed, callers should treat that as "no captions".
# ============================================

async def _tts_chunk_with_words(text, voice, output_path, rate=None, volume=None):
    rate   = rate   or config.TTS_RATE
    volume = volume or config.TTS_VOLUME
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    word_marks = []
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_marks.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
    return word_marks

def master_audio(in_path, target_lufs=-16.0):
    """Two-pass-ish loudnorm + light compression via ffmpeg. Falls back
    to the original file if ffmpeg isn't available or fails."""
    out_path = in_path.replace(".mp3", "_mastered.mp3")
    try:
        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11,"
                   f"acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
            "-ar", "44100", out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        if result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  🎚️  Audio mastered to {target_lufs} LUFS")
            return out_path
        print(f"  ⚠️ ffmpeg mastering failed, using original: {str(result.stderr)[-200:]}")
    except Exception as e:
        print(f"  ⚠️ Audio mastering skipped ({e})")
    return in_path

def generate_voiceover(script, label="voiceover", voice=None, rate=None):
    """
    Same chunking/retry robustness as before, but now also captures
    word-level timing (for captions) and masters the final audio.
    Returns (audio_path, captions_path).
    """
    import time as _t
    voice  = voice  or config.TTS_VOICE
    rate   = rate   or config.TTS_RATE
    print(f"\n🎙️  Generating {label} with edge-tts ({voice})...")
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path    = os.path.join(config.OUTPUT_FOLDER, f"{label}.mp3")
    captions_path = os.path.join(config.OUTPUT_FOLDER, f"{label}_captions.json")

    clean = re.sub(r'\[.*?\]', '', script)
    clean = clean.replace("[PAUSE]", " ... ").strip()
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'\*+', '', clean)
    clean = re.sub(r'#+\s*', '', clean)

    wc = len(clean.split())
    print(f"  📝 Script: {wc} words → expected ~{wc//150} min audio")

    max_chars = 2800
    chunks    = []
    remaining = clean
    while len(remaining) > max_chars:
        cut = remaining.rfind('. ', 0, max_chars)
        if cut == -1: cut = remaining.rfind('? ', 0, max_chars)
        if cut == -1: cut = remaining.rfind('! ', 0, max_chars)
        if cut == -1: cut = max_chars
        chunks.append(remaining[:cut + 1].strip())
        remaining = remaining[cut + 1:].strip()
    if remaining.strip():
        chunks.append(remaining.strip())

    print(f"  📦 {len(chunks)} chunks to process")

    chunk_paths   = []
    all_words     = []
    time_offset   = 0.0
    failed_chunks = 0

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        p = os.path.join(config.OUTPUT_FOLDER, f"edge_chunk_{i}.mp3")
        success = False

        for attempt in range(3):
            try:
                marks = asyncio.run(_tts_chunk_with_words(chunk, voice, p, rate))
                if os.path.exists(p) and os.path.getsize(p) > 1000:
                    for m in marks:
                        m["start"] += time_offset
                        m["end"]   += time_offset
                    all_words.extend(marks)
                    chunk_dur = AudioFileClip(p).duration
                    time_offset += chunk_dur
                    chunk_paths.append(p)
                    print(f"  🎙️ Chunk {i+1}/{len(chunks)} ✅ ({len(chunk.split())} words, {len(marks)} cues)")
                    success = True
                    break
                else:
                    print(f"  ⚠️ Chunk {i+1} empty output, retry {attempt+1}/3")
                    _t.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Chunk {i+1} attempt {attempt+1}/3 failed: {str(e)[:80]}")
                _t.sleep(3)

        if not success:
            print(f"  ❌ Chunk {i+1} failed all 3 attempts — generating silence")
            silence_dur = max(5.0, len(chunk.split()) / 150 * 60)
            silent = AudioClip(lambda t: 0, duration=silence_dur)
            silent.write_audiofile(p, fps=44100, logger=None)
            chunk_paths.append(p)
            time_offset += silence_dur
            failed_chunks += 1

    if not chunk_paths:
        print("❌ ALL TTS chunks failed — creating placeholder audio")
        placeholder = AudioClip(lambda t: 0, duration=60)
        placeholder.write_audiofile(audio_path, fps=44100, logger=None)
        return audio_path, None

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], audio_path)
    else:
        clips = []
        for p in chunk_paths:
            try:
                clips.append(AudioFileClip(p))
            except Exception as e:
                print(f"  ⚠️ Could not load {p}: {e}")
        if clips:
            merged = concatenate_audioclips(clips)
            merged.write_audiofile(audio_path, fps=44100, logger=None)
            for c in clips: c.close()
        else:
            shutil.copy(chunk_paths[0], audio_path)

    for p in chunk_paths:
        try: os.remove(p)
        except: pass

    if all_words:
        with open(captions_path, "w") as f:
            json.dump(all_words, f)
    else:
        captions_path = None

    mastered_path = master_audio(audio_path)

    try:
        final_audio = AudioFileClip(mastered_path)
        dur_min = final_audio.duration / 60
        final_audio.close()
        print(f"✅ Voiceover done: {dur_min:.1f} min ({label})")
        if dur_min < 15 and failed_chunks > 0:
            print(f"  ⚠️ Audio shorter than expected ({dur_min:.1f} min) — {failed_chunks} chunks failed")
    except Exception:
        print(f"✅ Voiceover done ({label})")

    return mastered_path, captions_path


def words_to_caption_lines(word_marks, max_words_per_line=5):
    lines = []
    cur, cur_start = [], None
    for w in word_marks:
        if cur_start is None:
            cur_start = w["start"]
        cur.append(w["text"])
        if len(cur) >= max_words_per_line:
            lines.append({"text": " ".join(cur), "start": cur_start, "end": w["end"]})
            cur, cur_start = [], None
    if cur:
        lines.append({"text": " ".join(cur), "start": cur_start, "end": word_marks[-1]["end"]})
    return lines


def build_caption_clips(captions_path, W=1920, H=1080):
    """Returns MoviePy TextClips timed to the audio, or [] if unavailable."""
    if not captions_path or not os.path.exists(captions_path):
        return []
    try:
        with open(captions_path) as f:
            word_marks = json.load(f)
    except Exception:
        return []
    if not word_marks:
        return []
    lines = words_to_caption_lines(word_marks)
    clips = []
    for line in lines:
        dur = max(0.3, line["end"] - line["start"])
        try:
            txt = TextClip(
                line["text"].upper(), fontsize=64, color="white",
                font="Liberation-Sans-Bold", stroke_color="black", stroke_width=3,
                method="caption", size=(int(W*0.85), None),
            ).set_start(line["start"]).set_duration(dur).set_position(("center", H-260))
        except Exception:
            continue
        clips.append(txt)
    return clips


# ============================================
# STEP 6b — BACKGROUND MUSIC (still disabled — copyright safety)
# ============================================

def fetch_background_music():
    print("\n🎵 Background music: DISABLED (copyright protection)")
    return None

def mix_audio_with_music(voice_path, music_path, output_path):
    print("  🎙️ Voice-only audio (copyright safe)")
    return voice_path


# ============================================
# STEP 7 — KEN BURNS (1080p)
# ============================================

def make_ken_burns_clip(img_path, duration, direction, W=1920, H=1080):
    try:
        pil = Image.open(img_path).convert("RGB")
        pil = ImageEnhance.Brightness(pil).enhance(0.78)
        pil = ImageEnhance.Color(pil).enhance(0.80)
        pil = ImageEnhance.Contrast(pil).enhance(1.15)
        scale = max(W * 1.35 / pil.width, H * 1.35 / pil.height)
        nw, nh = int(pil.width * scale), int(pil.height * scale)
        pil = pil.resize((nw, nh), Image.LANCZOS)
        arr = np.array(pil)
    except Exception as _img_err:
        print(f"  ⚠️ Image load failed ({_img_err}), using fallback frame")
        fallback = np.zeros((H, W, 3), dtype=np.uint8)
        fallback[:, :, 0] = 18
        arr = fallback
        nw, nh = W, H

    dirs = {
        "zoom_in":   ((nw*.10, nh*.10, nw*.90, nh*.90), (nw*.20, nh*.20, nw*.80, nh*.80)),
        "zoom_out":  ((nw*.20, nh*.20, nw*.80, nh*.80), (nw*.05, nh*.05, nw*.95, nh*.95)),
        "pan_left":  ((nw*.05, nh*.10, nw*.70, nh*.90), (nw*.30, nh*.10, nw*.95, nh*.90)),
        "pan_right": ((nw*.30, nh*.10, nw*.95, nh*.90), (nw*.05, nh*.10, nw*.70, nh*.90)),
        "pan_up":    ((nw*.10, nh*.20, nw*.90, nh*.95), (nw*.10, nh*.05, nw*.90, nh*.80)),
        "diagonal":  ((nw*.05, nh*.05, nw*.72, nh*.72), (nw*.28, nh*.28, nw*.95, nh*.95)),
        "slow_zoom": ((nw*.12, nh*.12, nw*.88, nh*.88), (nw*.22, nh*.22, nw*.78, nh*.78)),
    }
    (sx1,sy1,sx2,sy2),(ex1,ey1,ex2,ey2) = dirs.get(direction, dirs["zoom_in"])

    def make_frame(t):
        p = t / max(duration, 0.001)
        p = p * p * (3 - 2 * p)
        x1 = max(0, min(int(sx1+(ex1-sx1)*p), nw-2))
        y1 = max(0, min(int(sy1+(ey1-sy1)*p), nh-2))
        x2 = max(x1+1, min(int(sx2+(ex2-sx2)*p), nw))
        y2 = max(y1+1, min(int(sy2+(ey2-sy2)*p), nh))
        crop = arr[y1:y2, x1:x2]
        if crop.size == 0:
            x1, y1 = max(0, x1-1), max(0, y1-1)
            x2, y2 = min(nw, x1+2), min(nh, y1+2)
            crop = arr[y1:y2, x1:x2]
            if crop.size == 0: crop = arr[:2, :2]
        return np.array(Image.fromarray(crop).resize((W,H),Image.LANCZOS))

    clip = VideoClip(make_frame, duration=duration)
    clip.size = (W, H)
    return clip


def faster_ken_burns_schedule(n_slots, min_dur=3.5, max_dur=6.5, seed=0):
    """
    Varied per-slot durations so cuts feel edited rather than a fixed
    8s/14s metronome on every single video.
    """
    rng = random.Random(seed)
    return [round(rng.uniform(min_dur, max_dur), 2) for _ in range(n_slots)]


# ============================================
# STEP 8 — PROCESS VIDEO CLIP (1080p)
# ============================================

def process_video_clip(vid_info, duration, W=1920, H=1080):
    try:
        clip = VideoFileClip(vid_info["path"]).without_audio()
        if clip.duration < duration:
            loops = int(math.ceil(duration / clip.duration)) + 1
            clip  = concatenate_videoclips([clip] * loops)
        clip = clip.subclip(0, duration)
        clip = clip.resize(height=H)
        if clip.size[0] < W: clip = clip.resize(width=W)
        if clip.size[0] > W:
            xc = clip.size[0] // 2
            clip = clip.crop(x1=xc - W//2, x2=xc + W//2)
        if clip.size[1] > H:
            yc = clip.size[1] // 2
            clip = clip.crop(y1=yc - H//2, y2=yc + H//2)
        clip = clip.fl_image(lambda frame:
            np.clip(frame.astype(np.float32) * 0.72, 0, 255).astype(np.uint8))
        return clip
    except Exception as e:
        print(f"  ⚠️ Video process error: {e}")
        return ColorClip(size=(W,H), color=(5,0,0), duration=duration)


# ============================================
# STEP 9 — CHAPTER CARDS + TIMELINE GRAPHIC
# ============================================

def create_chapter_card(text, duration=3.0, W=1920, H=1080, style="cinematic"):
    def make_frame(t):
        fade_in  = min(t / 0.5, 1.0)
        fade_out = min((duration - t) / 0.5, 1.0) if t > duration - 0.5 else 1.0
        alpha    = min(fade_in, fade_out)

        img  = Image.new("RGB", (W, H), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 80)
            f_sub = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 32)
        except:
            f_big = f_sub = ImageFont.load_default()

        lw = int(400 * alpha)
        draw.rectangle([(W//2 - lw//2, H//2 - 72), (W//2 + lw//2, H//2 - 68)], fill=(int(200*alpha),0,0))

        sub = config.CHANNEL_NAME.upper()
        b   = draw.textbbox((0,0), sub, font=f_sub)
        draw.text(((W-(b[2]-b[0]))//2, H//2-112), sub, font=f_sub, fill=(int(100*alpha),0,0))

        b = draw.textbbox((0,0), text, font=f_big)
        tw = b[2]-b[0]
        draw.text(((W-tw)//2+4, H//2-14), text, font=f_big, fill=(int(30*alpha),0,0))
        draw.text(((W-tw)//2, H//2-18), text, font=f_big, fill=(int(255*alpha),int(255*alpha),int(255*alpha)))

        return np.array(img)

    clip = VideoClip(make_frame, duration=duration)
    clip.size = (W, H)
    return clip


def create_timeline_card(events, duration=5.0, W=1920, H=1080):
    """
    events: list of {"date": "...", "label": "..."} (3-6 items, keep
    labels short). Gives some chapter breaks a genuinely different
    look — a documented timeline — instead of every break being the
    same red-text-on-black card.
    """
    font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    font_small = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    def make_frame(t):
        alpha = min(t / 0.6, 1.0)
        img = Image.new("RGB", (W, H), (8, 8, 10))
        draw = ImageDraw.Draw(img)
        try:
            f_date = ImageFont.truetype(font_path, 34)
            f_label = ImageFont.truetype(font_small, 30)
            f_title = ImageFont.truetype(font_path, 44)
        except Exception:
            f_date = f_label = f_title = ImageFont.load_default()

        draw.text((80, 60), "TIMELINE", font=f_title, fill=(int(220*alpha), 0, 0))
        line_x = 140
        top, bottom = 160, H - 100
        draw.line([(line_x, top), (line_x, bottom)], fill=(90, 0, 0), width=4)

        n = max(len(events), 1)
        for i, ev in enumerate(events[:6]):
            y = top + (bottom - top) * (i / max(n - 1, 1))
            draw.ellipse([(line_x-10, y-10), (line_x+10, y+10)], fill=(int(220*alpha), 0, 0))
            draw.text((line_x + 40, y - 24), ev.get("date", ""), font=f_date,
                       fill=(int(255*alpha), int(255*alpha), int(255*alpha)))
            draw.text((line_x + 40, y + 12), ev.get("label", "")[:70], font=f_label,
                       fill=(int(200*alpha), int(200*alpha), int(200*alpha)))
        return np.array(img)

    clip = VideoClip(make_frame, duration=duration)
    clip.size = (W, H)
    return clip


# ============================================
# STEP 10 — ASSEMBLE MAIN VIDEO (1080p, captions, varied pacing)
# ============================================

def assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story, captions_path=None):
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    print(f"\n🎬 Step 10: Assembling {W}x{H} documentary video...")
    audio     = AudioFileClip(audio_path)
    total_dur = audio.duration

    MAX_DURATION = 14.5 * 60  # YouTube unverified-account limit
    if total_dur > MAX_DURATION:
        print(f"  ✂️  Trimming audio from {total_dur/60:.1f} min to {MAX_DURATION/60:.1f} min (YouTube unverified limit)")
        audio = audio.subclip(0, MAX_DURATION)
        total_dur = MAX_DURATION

    print(f"  ⏱️  Duration : {total_dur/60:.1f} minutes")
    print(f"  📸 Images   : {len(image_paths)}")
    print(f"  🎥 Videos   : {len(video_clips)}")

    KB_DIRS    = ["zoom_in","zoom_out","pan_left","pan_right","pan_up","diagonal","slow_zoom"]
    CARD_DUR   = 3.0
    CARD_EVERY = 4

    # Build a media plan first (type + source), THEN assign varied
    # durations from faster_ken_burns_schedule instead of a fixed
    # IMG_DUR=8.0 / VID_DUR=14.0 for every single slot.
    media_plan = []
    img_idx = vid_idx = 0
    while True:
        for _ in range(2):
            if image_paths:
                media_plan.append(("image", image_paths[img_idx % len(image_paths)], KB_DIRS[img_idx % len(KB_DIRS)]))
                img_idx += 1
        if video_clips:
            media_plan.append(("video", video_clips[vid_idx % len(video_clips)], None))
            vid_idx += 1
        # rough estimate assuming ~5s/image, ~10s/video average for the break check
        est = sum(5.0 if m[0]=="image" else 10.0 for m in media_plan) + (len(media_plan)//CARD_EVERY) * CARD_DUR
        if est >= total_dur + 30: break
        if len(media_plan) > 700: break

    img_durs = faster_ken_burns_schedule(sum(1 for m in media_plan if m[0]=="image"), 3.5, 6.5, seed=hash(story["title"]) % 1000)
    vid_durs = faster_ken_burns_schedule(sum(1 for m in media_plan if m[0]=="video"), 8.0, 14.0, seed=hash(story["title"]) % 1000 + 1)
    img_iter, vid_iter = iter(img_durs), iter(vid_durs)

    media_sequence = []
    for m_type, m_data, m_extra in media_plan:
        dur = next(img_iter, 5.0) if m_type == "image" else next(vid_iter, 10.0)
        media_sequence.append((m_type, m_data, dur, m_extra))

    print(f"  🎞️  Media slots: {len(media_sequence)} (varied duration)")

    clips     = []
    time_used = 0.0
    clips.append(create_chapter_card(metadata.get("title","True Crime")[:55], duration=5.0))
    time_used += 5.0

    chapter_names = ["The Background","The Case","The Investigation","The Outcome","The Aftermath"]
    chapter_count = media_count = 0

    for m_type, m_data, m_dur, m_extra in media_sequence:
        if time_used >= total_dur - 1.0: break
        remaining = total_dur - time_used

        if media_count > 0 and media_count % CARD_EVERY == 0:
            cd = min(CARD_DUR, remaining - 0.5)
            if cd > 0.5:
                name = chapter_names[min(chapter_count, len(chapter_names)-1)]
                # every 3rd break uses a timeline card instead of a plain
                # chapter card, for visual variety
                if chapter_count % 3 == 2:
                    events = [{"date": "", "label": f"Chapter {chapter_count+1}"},
                              {"date": "", "label": name}]
                    clips.append(create_timeline_card(events, duration=cd))
                else:
                    clips.append(create_chapter_card(f"Chapter {chapter_count+1}: {name}", duration=cd))
                time_used += cd
                chapter_count += 1
                remaining = total_dur - time_used
                if remaining < 1.0: break

        clip_dur = min(m_dur, remaining - 0.5)
        if clip_dur < 1.0: break

        if m_type == "image":
            kb = make_ken_burns_clip(m_data, clip_dur, m_extra, W, H)
            dark_ov = ColorClip(size=(W,H), color=(0,0,0), duration=clip_dur).set_opacity(0.25)
            clip = CompositeVideoClip([kb, dark_ov], size=(W, H))
        else:
            clip = process_video_clip(m_data, clip_dur, W, H)
            dark_ov = ColorClip(size=(W,H), color=(0,0,0), duration=clip_dur).set_opacity(0.22)
            clip = CompositeVideoClip([clip, dark_ov], size=(W, H))

        clips.append(clip)
        time_used += clip_dur
        media_count += 1

    outro_dur = min(4.0, max(0.5, total_dur - time_used))
    clips.append(create_chapter_card("🔴 Subscribe for Daily Cases", duration=outro_dur))

    print(f"  🔗 Joining {len(clips)} clips...")
    try:
        video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print(f"  ⚠️ compose failed: {e}, trying chain...")
        video = concatenate_videoclips(clips, method="chain")

    if video.duration > total_dur + 0.5:
        video = video.subclip(0, total_dur)

    def wm_frame(t):
        img  = Image.new("RGBA", (W, 44), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 26)
        except:
            font = ImageFont.load_default()
        draw.text((24, 10), config.WATERMARK_TEXT, font=font, fill=(210,210,210,140))
        return np.array(img.convert("RGB"))

    _wm_clip = VideoClip(wm_frame, duration=total_dur)
    _wm_clip.size = (W, 44)
    wm    = _wm_clip.set_position(("left","bottom")).set_opacity(config.WATERMARK_OPACITY)
    final = CompositeVideoClip([video, wm], size=(W, H)).set_audio(audio)

    # Burned-in captions from the TTS word-boundary timestamps
    caption_clips = build_caption_clips(captions_path, W, H)
    if caption_clips:
        print(f"  💬 Adding {len(caption_clips)} caption cues")
        final = CompositeVideoClip([final] + caption_clips, size=(W, H)).set_audio(audio)

    out = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
    print("  💾 Writing final video (1080p)...")
    final.write_videofile(out, fps=config.VIDEO_FPS, codec="libx264", audio_codec="aac",
                          threads=2, preset="ultrafast", bitrate=config.VIDEO_BITRATE, logger=None)
    for _c in clips:
        try: _c.close()
        except: pass
    clips.clear()
    try: video.close(); wm.close(); final.close(); audio.close()
    except: pass
    gc.collect()
    print(f"✅ Documentary assembled! ({total_dur/60:.1f} mins)")
    return out


# ============================================
# STEP 10b — SHORTS VIDEO (9:16, 1080x1920)
# ============================================

def assemble_shorts_video(shorts_audio_path, image_paths, metadata):
    print("\n📱 Step 10b: Assembling YouTube Short (9:16)...")
    W, H = 1080, 1920

    audio     = AudioFileClip(shorts_audio_path)
    total_dur = min(audio.duration, config.SHORTS_TARGET_DURATION)

    used_images = image_paths[:8] if len(image_paths) >= 8 else image_paths
    clip_dur    = total_dur / max(len(used_images), 1)
    KB_DIRS     = ["zoom_in","zoom_out","pan_left","pan_right","slow_zoom","diagonal"]

    def make_vertical_kb(img_path, duration, direction):
        try:
            pil = Image.open(img_path).convert("RGB")
            pil = ImageEnhance.Brightness(pil).enhance(0.65)
            pil = ImageEnhance.Color(pil).enhance(0.58)
            pil = ImageEnhance.Contrast(pil).enhance(1.25)
            scale = max(W * 1.3 / pil.width, H * 1.3 / pil.height)
            nw, nh = int(pil.width * scale), int(pil.height * scale)
            pil = pil.resize((nw, nh), Image.LANCZOS)
            arr = np.array(pil)
        except:
            arr = np.zeros((H,W,3),dtype=np.uint8)
            nw, nh = W, H

        dirs = {
            "zoom_in":   ((nw*.15,nh*.15,nw*.85,nh*.85),(nw*.22,nh*.22,nw*.78,nh*.78)),
            "zoom_out":  ((nw*.22,nh*.22,nw*.78,nh*.78),(nw*.10,nh*.10,nw*.90,nh*.90)),
            "pan_left":  ((nw*.05,nh*.05,nw*.65,nh*.95),(nw*.35,nh*.05,nw*.95,nh*.95)),
            "pan_right": ((nw*.35,nh*.05,nw*.95,nh*.95),(nw*.05,nh*.05,nw*.65,nh*.95)),
            "slow_zoom": ((nw*.18,nh*.18,nw*.82,nh*.82),(nw*.24,nh*.24,nw*.76,nh*.76)),
            "diagonal":  ((nw*.05,nh*.05,nw*.70,nh*.70),(nw*.30,nh*.30,nw*.95,nh*.95)),
        }
        (sx1,sy1,sx2,sy2),(ex1,ey1,ex2,ey2) = dirs.get(direction, dirs["zoom_in"])

        def make_frame(t):
            p = t / max(duration, 0.001)
            p = p*p*(3-2*p)
            x1 = max(0,min(int(sx1+(ex1-sx1)*p),nw-2))
            y1 = max(0,min(int(sy1+(ey1-sy1)*p),nh-2))
            x2 = max(x1+1,min(int(sx2+(ex2-sx2)*p),nw))
            y2 = max(y1+1,min(int(sy2+(ey2-sy2)*p),nh))
            crop = arr[y1:y2,x1:x2]
            if crop.size == 0: return np.zeros((H,W,3),dtype=np.uint8)
            return np.array(Image.fromarray(crop).resize((W,H),Image.LANCZOS))

        _vc = VideoClip(make_frame, duration=duration)
        _vc.size = (W, H)
        return _vc

    clips = []
    for i, img_path in enumerate(used_images):
        clip = make_vertical_kb(img_path, clip_dur, KB_DIRS[i % len(KB_DIRS)])
        dark_ov = ColorClip(size=(W,H), color=(0,0,0), duration=clip_dur).set_opacity(0.30)

        def make_caption(t, title=metadata.get("title","")[:55]):
            img  = Image.new("RGBA", (W, 220), (0,0,0,0))
            overlay = Image.new("RGBA", (W, 220), (0,0,0,170))
            img  = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)
            try:
                f_ch    = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 34)
                f_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 60)
            except:
                f_ch = f_title = ImageFont.load_default()
            draw.ellipse([(36,20),(62,46)], fill=(220,0,0,255))
            draw.text((72, 22), config.CHANNEL_NAME, font=f_ch, fill=(220,220,220,230))
            words = title.split()
            mid   = len(words)//2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            draw.text((36, 70), line1, font=f_title, fill=(255,255,255,255))
            draw.text((36,140), line2, font=f_title, fill=(255,255,0,255))
            return np.array(img.convert("RGB"))

        _cc = VideoClip(make_caption, duration=clip_dur)
        _cc.size = (W, 220)
        caption_clip = _cc.set_position(("center", H-220))
        composed     = CompositeVideoClip([clip, dark_ov, caption_clip], size=(W, H))
        clips.append(composed)

    video = concatenate_videoclips(clips, method="compose")
    if video.duration > total_dur: video = video.subclip(0, total_dur)

    final = video.set_audio(audio.subclip(0, min(audio.duration, total_dur)))
    out   = os.path.join(config.OUTPUT_FOLDER, "shorts_video.mp4")
    print("  💾 Writing Shorts (1080x1920)...")
    final.write_videofile(out, fps=30, codec="libx264", audio_codec="aac",
                          threads=2, preset="ultrafast", bitrate="6000k", logger=None)
    try: video.close(); final.close()
    except: pass
    gc.collect()
    print(f"✅ Short assembled! ({total_dur:.0f}s)")
    return out


# ============================================
# STEP 11 — THUMBNAIL (4 Styles, A/B Testing)
# ============================================

def _wrap_text(draw, text, font, max_width):
    words  = text.split()
    lines  = []
    line   = ""
    for word in words:
        test = (line + " " + word).strip()
        w    = draw.textbbox((0, 0), test, font=font)[2]
        if w <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [text]

def _draw_text_shadow(draw, x, y, text, font, fill, shadow=(0,0,0), depth=4):
    for dx in range(-depth, depth+1, depth):
        for dy in range(-depth, depth+1, depth):
            if dx or dy:
                draw.text((x+dx, y+dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def _best_bg_image(image_paths, story_title=""):
    import random as _r
    rng = _r.Random(hash(story_title) % 2**31)
    candidates = image_paths[:min(12, len(image_paths))] if len(image_paths) >= 3 else image_paths
    scored = []
    for p in candidates:
        try:
            arr = np.array(Image.open(p).convert("RGB").resize((160, 90)))
            brightness = arr.mean()
            std        = arr.std()
            score      = std * 0.6 + min(brightness, 120) * 0.4
            scored.append((score, p))
        except:
            scored.append((0, p))
    scored.sort(reverse=True)
    top3 = [p for _, p in scored[:3]]
    return rng.choice(top3)

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 11: Creating thumbnail...")
    W, H  = config.THUMBNAIL_WIDTH, config.THUMBNAIL_HEIGHT
    thumb = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")

    thumb_text = metadata.get("thumbnail_text", "TRUE CRIME CASE").upper().strip()
    words = thumb_text.split()[:4]
    thumb_text = " ".join(words)

    raw_title = metadata.get("title", story["title"])
    title_display = raw_title[:60] + ("..." if len(raw_title) > 60 else "")

    FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    BEBAS     = BEBAS_FONT_PATH or config.FONT_CACHE_PATH
    HEADLINE  = BEBAS if (BEBAS and os.path.exists(BEBAS)) else FONT_BOLD

    nwords = len(thumb_text.split())
    hl_sz  = 140 if nwords <= 2 else (110 if nwords == 3 else 90)
    try:
        f_hl   = ImageFont.truetype(HEADLINE, hl_sz)
        f_sub  = ImageFont.truetype(FONT_BOLD, 38)
        f_tag  = ImageFont.truetype(FONT_BOLD, 24)
        f_tiny = ImageFont.truetype(FONT_REG,  22)
    except:
        f_hl = f_sub = f_tag = f_tiny = ImageFont.load_default()

    bg_path  = _best_bg_image(image_paths, story_title=raw_title) if image_paths else None
    base_img = Image.new("RGB", (W, H), (15, 0, 0))
    if bg_path:
        try:
            base_img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)
        except:
            pass

    img = ImageEnhance.Brightness(base_img).enhance(0.40)
    img = ImageEnhance.Color(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.20)

    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    for row in range(H):
        frac  = row / H
        alpha = int(80 + 140 * max(0, frac - 0.25))
        alpha = min(alpha, 210)
        gd.line([(0, row), (W, row)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), grad).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 8)], fill=(220, 0, 0))

    badge_text = "▶  " + config.CHANNEL_NAME.upper()
    bw = draw.textbbox((0, 0), badge_text, font=f_tag)[2]
    draw.rounded_rectangle([(16, 16), (bw + 44, 48)], radius=5, fill=(200, 0, 0))
    draw.text((28, 20), badge_text, font=f_tag, fill=(255, 255, 255))

    lines = _wrap_text(draw, thumb_text, f_hl, W - 80)
    line_h = draw.textbbox((0, 0), "Ag", font=f_hl)[3] + 12
    total_h = line_h * len(lines)
    text_y = (H // 2) - (total_h // 2) - 30

    for i, line in enumerate(lines):
        lw = draw.textbbox((0, 0), line, font=f_hl)[2]
        x  = (W - lw) // 2
        y  = text_y + i * line_h
        for sx, sy in [(-4,-4),(4,-4),(-4,4),(4,4),(0,5),(5,0),(-5,0),(0,-5)]:
            draw.text((x+sx, y+sy), line, font=f_hl, fill=(0, 0, 0))
        color = (255, 230, 0) if i == 0 else (255, 255, 255)
        draw.text((x, y), line, font=f_hl, fill=color)

    band_top = H - 90
    draw.rectangle([(0, band_top), (W, H)], fill=(10, 0, 0))
    draw.rectangle([(0, band_top), (W, band_top + 4)], fill=(200, 0, 0))

    t_lines = _wrap_text(draw, title_display, f_sub, W - 60)
    t_y = band_top + 10
    for tline in t_lines[:2]:
        tw = draw.textbbox((0, 0), tline, font=f_sub)[2]
        draw.text(((W - tw) // 2, t_y), tline, font=f_sub, fill=(240, 240, 240))
        t_y += 42

    img.save(thumb, "JPEG", quality=95, optimize=True)
    size_kb = os.path.getsize(thumb) // 1024
    print(f"✅ Thumbnail: '{thumb_text}' | {W}x{H} | {size_kb}KB")
    return thumb


# ============================================
# STEP 12 — UPLOAD TO YOUTUBE
# ============================================

PLAYLIST_CACHE_FILE = "playlist_cache.json"

def load_playlist_cache():
    if os.path.exists(PLAYLIST_CACHE_FILE):
        try:
            with open(PLAYLIST_CACHE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_playlist_cache(cache):
    with open(PLAYLIST_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

PLAYLIST_DESCRIPTIONS = {
    "en": {
        "template": "A collection of true crime documentaries about {topic}. New cases added daily. Subscribe: {handle}",
        "master_title": "All True Crime Cases — Archive of Enigmas",
        "master_desc":  "Every true crime documentary from Archive of Enigmas. New case every day. Subscribe for more.",
    },
    "hi": {
        "template": "{topic} के बारे में सच्ची अपराध कहानियों का संग्रह। हर रोज़ नए मामले। Subscribe करें: {handle}",
        "master_title": "सभी अपराध मामले — Archive of Enigmas",
        "master_desc":  "Archive of Enigmas की सभी सच्ची अपराध कहानियां। हर दिन नया मामला। Subscribe करें।",
    },
    "es": {
        "template": "Una colección de documentales de crimen real sobre {topic}. Nuevos casos cada día. Suscríbete: {handle}",
        "master_title": "Todos los Casos de Crimen Real — Archive of Enigmas",
        "master_desc":  "Todos los documentales de crimen real de Archive of Enigmas. Un nuevo caso cada día.",
    },
    "pt": {
        "template": "Uma coleção de documentários de crime real sobre {topic}. Novos casos diariamente. Inscreva-se: {handle}",
        "master_title": "Todos os Casos de Crime Real — Archive of Enigmas",
        "master_desc":  "Todos os documentários de crime real do Archive of Enigmas. Um novo caso por dia.",
    },
    "fr": {
        "template": "Une collection de documentaires de crime vrai sur {topic}. Nouveaux cas chaque jour. Abonnez-vous: {handle}",
        "master_title": "Tous les Cas de Crime Vrai — Archive of Enigmas",
        "master_desc":  "Tous les documentaires de crime vrai d'Archive of Enigmas. Un nouveau cas chaque jour.",
    },
}

PLAYLIST_DEFINITIONS = {
    "serial":     {"en": "Serial Killers — True Crime Documentaries",
                   "hi": "सीरियल किलर — सच्ची अपराध कहानियां",
                   "es": "Asesinos en Serie — Crimen Real",
                   "pt": "Serial Killers — Documentários de Crime Real",
                   "fr": "Tueurs en Série — Documentaires Crime Vrai"},
    "murder":     {"en": "Murder Mysteries — True Crime Cases",
                   "hi": "हत्या के रहस्य — सच्ची घटनाएं",
                   "es": "Misterios de Asesinato — Casos Criminales",
                   "pt": "Mistérios de Assassinato — Casos Reais",
                   "fr": "Mystères de Meurtre — Affaires Criminelles"},
    "missing":    {"en": "Missing Persons — Unsolved Disappearances",
                   "hi": "गुमशुदा लोग — अनसुलझे मामले",
                   "es": "Personas Desaparecidas — Casos Sin Resolver",
                   "pt": "Pessoas Desaparecidas — Casos Não Resolvidos",
                   "fr": "Personnes Disparues — Affaires Non Résolues"},
    "heist":      {"en": "Greatest Heists in History — True Crime",
                   "hi": "इतिहास की सबसे बड़ी डकैतियां",
                   "es": "Los Mayores Robos de la Historia",
                   "pt": "Os Maiores Roubos da História",
                   "fr": "Les Plus Grands Braquages de l'Histoire"},
    "cult":       {"en": "Cults & Dark Secrets — True Crime Documentaries",
                   "hi": "पंथ और काले रहस्य — सच्ची घटनाएं",
                   "es": "Sectas y Secretos Oscuros — Crimen Real",
                   "pt": "Seitas e Segredos Sombrios — Crime Real",
                   "fr": "Sectes et Secrets Sombres — Crime Vrai"},
    "unsolved":   {"en": "Unsolved Mysteries — Cold Cases Documentary",
                   "hi": "अनसुलझे रहस्य — कोल्ड केस",
                   "es": "Misterios Sin Resolver — Casos Fríos",
                   "pt": "Mistérios Não Resolvidos — Casos Frios",
                   "fr": "Mystères Non Résolus — Affaires Non Classées"},
    "fraud":      {"en": "Biggest Frauds & Scams — True Crime",
                   "hi": "सबसे बड़े घोटाले — सच्ची घटनाएं",
                   "es": "Los Mayores Fraudes y Estafas — Crimen Real",
                   "pt": "As Maiores Fraudes e Golpes — Crime Real",
                   "fr": "Les Plus Grandes Fraudes — Crime Vrai"},
    "coldcase":   {"en": "Cold Cases Solved — True Crime Documentary",
                   "hi": "सुलझे कोल्ड केस — अपराध की कहानियां",
                   "es": "Casos Fríos Resueltos — Crimen Real",
                   "pt": "Casos Frios Resolvidos — Crime Real",
                   "fr": "Affaires Froides Résolues — Crime Vrai"},
    "default":    {"en": "True Crime Documentary — Archive of Enigmas",
                   "hi": "सच्ची अपराध कहानियां — Archive of Enigmas",
                   "es": "Documentales de Crimen Real — Archive of Enigmas",
                   "pt": "Documentários de Crime Real — Archive of Enigmas",
                   "fr": "Documentaires Crime Vrai — Archive of Enigmas"},
}

def get_or_create_playlist(yt, topic, language):
    cache     = load_playlist_cache()
    cache_key = f"{topic}_{language}"
    if cache_key in cache:
        print(f"  📋 Using cached playlist: {cache[cache_key]}")
        return cache[cache_key]

    topic_key   = topic if topic in PLAYLIST_DEFINITIONS else "default"
    lang_titles = PLAYLIST_DEFINITIONS[topic_key]
    pl_title    = lang_titles.get(language, lang_titles["en"])

    lang_desc_cfg = PLAYLIST_DESCRIPTIONS.get(language, PLAYLIST_DESCRIPTIONS["en"])

    if topic == "default":
        pl_title = lang_desc_cfg["master_title"]
        pl_desc  = lang_desc_cfg["master_desc"] + f" {config.CHANNEL_HANDLE}"
    else:
        pl_desc = lang_desc_cfg["template"].format(
            topic=topic_key,
            handle=config.CHANNEL_HANDLE
        )

    try:
        resp = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title":           pl_title[:100],
                    "description":     pl_desc[:500],
                    "defaultLanguage": language,
                    "tags":            [topic_key, "true crime", "documentary",
                                        language, config.CHANNEL_NAME],
                },
                "status": {"privacyStatus": "public"}
            }
        ).execute()
        pl_id = resp["id"]
        cache[cache_key] = pl_id
        save_playlist_cache(cache)
        print(f"  ✅ Created [{language.upper()}] playlist: '{pl_title}'")
        return pl_id
    except Exception as e:
        print(f"  ⚠️ Playlist create failed: {e}")
        return None

def add_video_to_playlist(yt, video_id, playlist_id):
    try:
        yt.playlistItems().insert(
            part="snippet",
            body={"snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}
            }}
        ).execute()
        print(f"  ✅ Added to playlist: {playlist_id}")
    except Exception as e:
        print(f"  ⚠️ Playlist add failed: {e}")


def upload_to_youtube(video_path, thumbnail_path, metadata, is_short=False, language="en"):
    """
    CHANGED: removed the second, synthetic "engagement" comment that
    simulated viewer debate. Only the genuinely useful chapters/CTA
    comment from the channel account is posted now.
    """
    kind = "Short" if is_short else "Video"
    print(f"\n📤 Step 12: Uploading {kind} to YouTube ({language.upper()})...")

    td    = json.loads(config.YOUTUBE_TOKEN)
    creds = Credentials(
        token=td.get("token"), refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri"), client_id=td.get("client_id"),
        client_secret=td.get("client_secret"), scopes=td.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("🔄 Token refreshed!")

    yt = build("youtube","v3",credentials=creds)

    title = metadata.get("title","True Crime")[:100]
    if is_short:
        title       = f"#Shorts {title}"[:100]
        description = f"🔴 {title}\n\n{metadata.get('hashtags','')}\n\n#Shorts\n\n🔔 Subscribe → {config.CHANNEL_HANDLE}"
        tags        = metadata.get("tags_list",[]) + ["Shorts","TrueCrimeShorts","true crime shorts"]
    else:
        description = metadata.get("full_description","")
        tags        = metadata.get("tags_list",[])

    body = {
        "snippet": {
            "title":                title,
            "description":          description,
            "tags":                 [
                    t.lstrip("#").strip()[:100]
                    for t in tags
                    if t and t.strip() and len(t.strip().lstrip("#")) > 0
                ][:500],
            "categoryId":           "25",
            "defaultLanguage":      language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus":             "public",
            "selfDeclaredMadeForKids":   False,
            "license":                   "youtube",
            "embeddable":                True,
            "publicStatsViewable":       True,
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    try:
        resp = yt.videos().insert(part="snippet,status,localizations", body=body, media_body=media).execute()
    except Exception as e:
        if "uploadLimitExceeded" in str(e):
            print("\u26a0\ufe0f  YouTube daily upload limit reached for this channel.")
            print("   \u27a1  Verify your channel at https://youtube.com/verify to lift the cap.")
            print("   \u23ed  Skipping upload — video saved locally at:", video_path)
            return None
        raise
    vid   = resp.get("id")
    print(f"✅ {kind} uploaded! ID: {vid}")

    if not is_short and vid:
        try:
            base_title = metadata.get("title", "")[:100]
            base_desc  = metadata.get("description", "")[:400]
            localizations = {}
            for loc_lang, loc_cfg in config.SUPPORTED_LANGUAGES.items():
                if loc_lang == language:
                    continue
                localizations[loc_lang] = {
                    "title":       base_title,
                    "description": base_desc,
                }
            if localizations:
                yt.videos().update(
                    part="localizations",
                    body={"id": vid, "localizations": localizations}
                ).execute()
                print(f"  🌍 Localizations pushed: {list(localizations.keys())}")
        except Exception as e:
            print(f"  ⚠️ Localizations failed (non-critical): {e}")

    if not is_short:
        topic = metadata.get("topic", "default")
        pl_id = get_or_create_playlist(yt, topic, language)
        if pl_id:
            add_video_to_playlist(yt, vid, pl_id)
        master_pl = get_or_create_playlist(yt, "default", language)
        if master_pl and master_pl != pl_id:
            add_video_to_playlist(yt, vid, master_pl)

    if not is_short and thumbnail_path and os.path.exists(thumbnail_path):
        size_kb = os.path.getsize(thumbnail_path) // 1024
        print(f"  📸 Uploading thumbnail ({size_kb}KB) for video {vid}...")
        thumb_ok = False
        for attempt in range(1, 4):
            try:
                import time as _time
                yt.thumbnails().set(
                    videoId=vid,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                ).execute()
                print(f"✅ Thumbnail uploaded! (attempt {attempt})")
                thumb_ok = True
                break
            except Exception as e:
                err_str = str(e)
                print(f"  ❌ Thumbnail attempt {attempt}/3 failed: {err_str[:120]}")
                if "forbidden" in err_str.lower() or "403" in err_str or "insufficientPermissions" in err_str:
                    print("  ⚠️  CHANNEL NOT VERIFIED — go to https://www.youtube.com/verify")
                    break
                if attempt < 3:
                    _time.sleep(5 * attempt)
        if not thumb_ok:
            manual_path = os.path.join(config.OUTPUT_FOLDER, f"thumbnail_manual_{vid}.jpg")
            import shutil as _sh
            _sh.copy(thumbnail_path, manual_path)
            print(f"  💾 Thumbnail saved for manual upload: {manual_path}")

    if not is_short:
        # ── Single, genuinely useful pinned comment: chapters + CTA ──────────
        # The previous second "engagement" comment that simulated a viewer
        # debate question has been removed — it was synthetic engagement,
        # posted from the channel's own account pretending to be organic
        # discussion, and it worked against the channel more than for it.
        try:
            chapters_text = metadata.get("chapters", "")
            first_comment_tmpl = getattr(config, "FIRST_COMMENT_TEMPLATE", "")
            if first_comment_tmpl and chapters_text:
                first_msg = first_comment_tmpl.format(
                    chapters=chapters_text[:400],
                    handle=config.CHANNEL_HANDLE
                )
            else:
                first_msg = metadata.get("pinned_comment", "What do you think happened here?")

            thread = yt.commentThreads().insert(
                part="snippet",
                body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{"textOriginal":first_msg}}}}).execute()
            comment_id = thread["snippet"]["topLevelComment"]["id"]
            try:
                yt.comments().setModerationStatus(
                    id=comment_id, moderationStatus="published", banAuthor=False
                ).execute()
            except Exception:
                pass
            print("✅ Pinned comment (chapters + CTA) posted!")
        except Exception as e:
            print(f"⚠️ Comment: {e}")

    print(f"\n🎉 LIVE: https://youtube.com/watch?v={vid}")
    return vid


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline():
    global BEBAS_FONT_PATH

    lang = os.environ.get("BOT_LANGUAGE", "en").strip().lower()
    lang_cfg  = config.SUPPORTED_LANGUAGES.get(lang, config.SUPPORTED_LANGUAGES["en"])
    lang_name = lang_cfg.get("name", "English")
    voice     = lang_cfg.get("voice", config.TTS_VOICE)
    rate      = lang_cfg.get("rate",  config.TTS_RATE)

    print("="*55)
    print(f"🚀 ARCHIVE OF ENIGMAS — Pipeline v12 | Lang: {lang_name}")
    print("="*55)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    BEBAS_FONT_PATH = ensure_bebas_font()

    try:
        story = fetch_story()
        topic = story.get("topic", "other")
        print(f"  📌 Topic: {topic} | Language: {lang_name}")

        if lang == "en":
            script, shorts_script, metadata = generate_script(story, language="en")
        else:
            print(f"  🌐 Generating English base, then translating to {lang_name}...")
            script, shorts_script, metadata = generate_script(story, language="en")
            script, shorts_script, metadata = translate_script(script, shorts_script, metadata, lang)

        img_queries, vid_queries = extract_keywords(story)
        image_paths = fetch_images(img_queries, target=24)
        video_clips = fetch_videos(vid_queries, target=14)

        audio_path, captions_path = generate_voiceover(script, label=f"voiceover_{lang}", voice=voice, rate=rate)
        shorts_audio_path = None
        if shorts_script:
            shorts_audio_path, _shorts_captions = generate_voiceover(
                shorts_script, label=f"shorts_voiceover_{lang}", voice=voice, rate=rate)

        music_path       = fetch_background_music()
        mixed_audio_path = os.path.join(config.OUTPUT_FOLDER, f"voiceover_{lang}_mixed.mp3")
        audio_path        = mix_audio_with_music(audio_path, music_path, mixed_audio_path)

        thumbnail_path = create_thumbnail(image_paths, metadata, story)

        video_path = assemble_documentary_video(
            audio_path, image_paths, video_clips, metadata, story, captions_path=captions_path)

        shorts_path = None
        if shorts_audio_path and image_paths:
            try:
                shorts_path = assemble_shorts_video(shorts_audio_path, image_paths, metadata)
            except Exception as e:
                print(f"⚠️ Shorts assembly failed: {e}")

        video_id = upload_to_youtube(video_path, thumbnail_path, metadata,
                                     is_short=False, language=lang)
        if video_id is None:
            print("⏹  Pipeline stopping cleanly — upload limit reached.")
            return
        shorts_id = None
        if shorts_path:
            try:
                shorts_id = upload_to_youtube(shorts_path, None, metadata,
                                              is_short=True, language=lang)
            except Exception as e:
                print(f"⚠️ Shorts upload failed: {e}")

        keywords = [story["title"].lower().split()[0]] if story["title"] else []
        update_history(metadata["title"], topic, keywords, lang=lang)

        print("\n" + "="*55)
        print("🎉 SUCCESS!")
        print(f"🌐 Language  : {lang_name}")
        print(f"📺 Main    : https://youtube.com/watch?v={video_id}")
        print(f"🎬 Studio  : https://studio.youtube.com/video/{video_id}/edit")
        if shorts_id:
            print(f"📱 Short   : https://youtube.com/watch?v={shorts_id}")
        print(f"📊 Title   : {metadata.get('title')}")
        print(f"🎭 Style   : Thumbnail style {metadata.get('thumbnail_style','1')}")
        print(f"🔤 Font    : {'Bebas Neue' if BEBAS_FONT_PATH else 'LiberationSans (fallback)'}")
        print(f"🎤 Voice   : edge-tts ({voice}), mastered + captioned")
        print("="*55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback; traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
