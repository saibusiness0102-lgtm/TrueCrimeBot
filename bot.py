# ============================================
# ARCHIVE OF ENIGMAS — DOCUMENTARY BOT v11 GROWTH
# 20-min videos | 1080p | English-First | Peak SEO
# Fixes v11:
#   - Wikipedia-first (no more multilingual RSS stories)
#   - Bebas Neue font download for viral thumbnails
#   - Stronger title prompt with proven formats
#   - Working background music URLs
#   - Better Wikipedia case list (more viral/trending cases)
#   - Upload history tracked across ALL languages
# ============================================

import os
import re
import json
import math
import random
import shutil
import asyncio
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
# v11 FIX: FONT DOWNLOAD — Bebas Neue for viral thumbnails
# LiberationSans looks generic; Bebas Neue looks like Netflix/crime docs
# ============================================

def ensure_bebas_font():
    """Download Bebas Neue once per run and cache it at FONT_CACHE_PATH."""
    import urllib.request
    path = config.FONT_CACHE_PATH
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    try:
        print("  🔤 Downloading Bebas Neue font...")
        urllib.request.urlretrieve(config.BEBAS_NEUE_URL, path)
        if os.path.getsize(path) > 10000:
            print("  ✅ Bebas Neue downloaded!")
            return path
    except Exception as e:
        print(f"  ⚠️ Font download failed ({e}), using fallback")
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
    # v11 FIX: Track history for ALL languages to prevent cross-language duplicates
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

# ── Keywords that MUST appear for an RSS story to qualify ────────────────
_RSS_CRIME_REQUIRED = {
    "murder","killed","killing","homicide","manslaughter","stabbed","shooting","shot",
    "missing","disappeared","vanished","abducted","kidnapped","kidnapping",
    "arrested","convicted","sentenced","charged","indicted","suspect",
    "victim","crime","robbery","assault","rape","sexual assault","molested",
    "trafficking","serial killer","cold case","investigation","forensic",
    "fraud","scam","embezzle","ponzi","poisoned","poisoning",
}

def is_crime_story(title, content):
    """Return True only if the story contains at least one crime keyword."""
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
                    # FIX: Only accept genuine crime stories
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
        # ── Classic Serial Killers ────────────────────────────────────
        "Zodiac Killer","Jack the Ripper","Golden State Killer","Ted Bundy",
        "Jeffrey Dahmer","John Wayne Gacy","BTK killer","Gary Ridgway",
        "Samuel Little","Ed Kemper","Richard Ramirez","Dean Corll",
        "Andrei Chikatilo","Aileen Wuornos","Harold Shipman","H. H. Holmes",
        "Charles Manson","Pedro Lopez","Luis Garavito","John Edward Robinson",
        "Israel Keyes","Randy Kraft","Gerard Schaefer","Dennis Nilsen",
        "Peter Sutcliffe","Robert Pickton","Paul Bernardo","Herb Baumeister",
        # ── Viral True Crime (high YouTube search volume) ────────────
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
        # ── Cold Cases & Mysteries ────────────────────────────────────
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
        # ── Cults & Conspiracies ──────────────────────────────────────
        "Jonestown massacre","Heaven's Gate cult","NXIVM cult",
        "Aum Shinrikyo","Branch Davidians Waco","The Family cult Australia",
        "Order of the Solar Temple","Rajneeshee bioterror attack",
        "Children of God cult","Peoples Temple","The Ant Hill Kids",
        # ── Famous Heists ─────────────────────────────────────────────
        "DB Cooper","Isabella Stewart Gardner Museum theft",
        "Great Train Robbery 1963","Antwerp diamond heist",
        "Hatton Garden heist","Banco Central Brazil robbery",
        "Dunbar Armored robbery","Lufthansa heist 1978",
        "French Connection drug smuggling","Pink Panthers jewel thieves",
        # ── Fraud & White Collar ──────────────────────────────────────
        "Bernie Madoff Ponzi scheme","Enron scandal",
        "Elizabeth Holmes Theranos","Anna Sorokin fraud",
        "Harshad Mehta scam","Vijay Mallya fraud",
        "Nirav Modi diamond fraud","Frank Abagnale",
        "Sam Bankman-Fried FTX collapse","WeWork Adam Neumann fraud",
        "Billy McFarland Fyre Festival","Trevor Milton Nikola fraud",
        # ── Kidnapping & Captivity ────────────────────────────────────
        "Jaycee Dugard kidnapping","Elizabeth Smart kidnapping",
        "Ariel Castro kidnappings","Natascha Kampusch kidnapping",
        "Patty Hearst kidnapping","Lindbergh kidnapping",
        "Fritzl case","Colleen Stan captivity","Mary Vincent attack",
        # ── Poisonings & Assassinations ───────────────────────────────
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
            "bloody crime scene investigation",
            "forensic scientist evidence gloves",
            "chalk outline floor crime",
            "autopsy table dark dramatic",
            "detective holding evidence bag",
            "police tape house crime scene",
            "court room judge gavel",
            "victim memorial flowers candles",
            "crime scene photo evidence board",
            "prosecutor evidence courtroom dark",
        ],
        "missing": [
            "missing person flyer post",
            "search party flashlights forest night",
            "empty swing set abandoned playground",
            "milk carton missing child vintage",
            "search rescue team dogs forest",
            "abandoned child bedroom dark",
            "candle vigil memorial night",
            "family crying grief dark",
            "detective studying map missing route",
            "empty chair at table dark",
        ],
        "serial": [
            "serial killer mugshot newspaper",
            "detective crime board red string",
            "prison corridor cell dramatic",
            "victims memorial wall photographs",
            "criminal profile document desk",
            "FBI investigation files dark",
            "courtroom packed dramatic verdict",
            "dark silhouette figure stalking",
            "phone call night dark window",
            "evidence map pins locations crime",
        ],
        "heist": [
            "vault door steel bank dramatic",
            "gold bars stacks dramatic",
            "masked robber dark dramatic",
            "security camera footage grainy",
            "money counting table dramatic",
            "getaway car dramatic night",
            "briefcase handcuff arrest",
            "police chase night urban",
            "stolen jewelry dramatic close",
            "auction house valuable art dramatic",
        ],
        "cult": [
            "candles ritual dark ceremony",
            "abandoned cult compound building",
            "robed figures ceremony dark forest",
            "cult leader crowd podium dramatic",
            "bible torn pages dark dramatic",
            "isolated rural compound aerial",
            "brainwashing propaganda poster vintage",
            "survivor testimony courtroom dramatic",
            "mass grave dark documentary",
            "FBI raid compound dramatic",
        ],
        "unsolved": [
            "cold case file folder dusty",
            "unanswered questions chalkboard dark",
            "detective staring wall evidence",
            "old crime scene photo sepia",
            "question mark shadow dark",
            "file cabinet overflowing cases",
            "mystery door locked dark",
            "vintage newspaper headline unsolved",
            "detective old evidence box",
            "shadow figure foggy night vintage",
        ],
        "conspiracy": [
            "classified document redacted black",
            "surveillance camera network dark",
            "government building night dramatic",
            "conspiracy board newspaper clippings",
            "shadowy figure silhouette dramatic",
            "newspaper headline cover up dark",
            "briefcase exchange dark alley",
            "hacker computer screen dark",
            "secret meeting dark room",
            "wiretap phone surveillance dramatic",
        ],
        "coldcase": [
            "dusty evidence box files cold case",
            "old polaroid photo faded dark",
            "detective reopening old case files",
            "vintage crime scene photograph",
            "decades old newspaper archive",
            "retired detective case notes dark",
            "forensic DNA lab modern dramatic",
            "family seeking justice courtroom",
            "cold storage evidence room dark",
            "witness testimony years later dramatic",
        ],
    }

    TOPIC_VIDEOS = {
        "murder": [
            "ambulance emergency lights night",
            "police investigation crime scene",
            "courtroom gavel dramatic close",
            "prison sentence judge dramatic",
            "forensic team working crime scene",
            "detective interviewing witness",
        ],
        "missing": [
            "search helicopter forest aerial",
            "search party walking field night",
            "missing poster blowing wind",
            "empty road driving night dramatic",
            "vigil candles crowd night",
            "family reunion emotional dramatic",
        ],
        "serial": [
            "police car convoy dramatic",
            "prison transfer van dramatic",
            "courtroom packed trial dramatic",
            "detective profiling board dramatic",
            "news reporter crime scene live",
            "handcuffed perp walk dramatic",
        ],
        "heist": [
            "bank vault door dramatic",
            "police chase urban night",
            "money counting dramatic",
            "getaway car speeding night",
            "police roadblock dramatic",
            "news helicopter aerial dramatic",
        ],
        "cult": [
            "forest dark night dramatic",
            "crowd chanting dramatic",
            "abandoned building interior dark",
            "smoke fire ritual dramatic",
            "documentary interview dramatic",
            "police raid building dramatic",
        ],
        "default": [
            "dark rainy city night",
            "fog forest dark eerie",
            "storm lightning dramatic dark",
            "dark ocean waves night",
            "fire dark night dramatic",
            "dark road night driving",
            "smoke dark atmospheric",
            "rain window dark dramatic",
            "dark alley night cinematic",
            "thunder clouds dark dramatic",
        ],
    }

    UNIVERSAL_IMAGES = [
        "dark dramatic cinematic shadows",
        "vintage sepia photograph dark room",
        "candlelight dark atmospheric room",
        "old typewriter dark dramatic",
        "magnifying glass clue mystery",
        "shadow window rain night",
        "dark cemetery fog night",
        "old clock dramatic dark",
        "newspaper archive reading dark",
        "leather journal pen dark desk",
        "radio vintage dark room dramatic",
        "telephone vintage dramatic dark",
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
# ============================================
# GROQ RATE-LIMIT RETRY WRAPPER
# ============================================
import time as _time

def groq_create_with_retry(client, max_retries=6, **kwargs):
    """
    Drop-in wrapper for client.chat.completions.create that automatically
    retries on 429 RateLimitError.
    - TPM (per-minute) limit: sleeps the exact wait time Groq reports, retries up to max_retries.
    - TPD (per-day)    limit: exits immediately — no point burning Actions minutes waiting 2+ hrs.
    """
    from groq import RateLimitError
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            err_str = str(e)
            # Daily quota exhausted — bail immediately, not retryable within this run
            if "tokens per day" in err_str or "TPD" in err_str:
                print("🚫 Groq daily token quota (100k TPD) exhausted.")
                print("   ➡  Upgrade at https://console.groq.com/settings/billing")
                print("   ⏭  Skipping today's run — will retry tomorrow.")
                sys.exit(0)   # exit 0 so GitHub Actions doesn't flag as failure
            if attempt == max_retries - 1:
                raise
            # TPM (per-minute) — parse exact wait from error message
            match = re.search(r'try again in ([\d.]+)s', err_str)
            if match:
                wait = float(match.group(1)) + 2   # small buffer
            else:
                wait = min(5 * 2 ** attempt, 120)  # exponential backoff, cap 2 min
            print(f"  ⏳ Rate limit hit — waiting {wait:.1f}s then retrying "
                  f"(attempt {attempt + 1}/{max_retries})...")
            _time.sleep(wait)

# STEP 5 — GENERATE SCRIPT (20-min TARGET)
# ============================================

def generate_script(story, language="en"):
    print(f"\n✍️  Step 5: Generating scripts ({language.upper()})...")
    h = load_history()
    recent_titles_str = ", ".join(h["recent_titles"][:5]) if h["recent_titles"] else "none yet"

    client = Groq(api_key=config.GROQ_API_KEY)

    lang_instruction = ""
    if language != "en":
        lang_info = config.SUPPORTED_LANGUAGES.get(language, {})
        lang_instruction = f"\n\nIMPORTANT: Write EVERYTHING (script, title, description, tags, all metadata) in {lang_info.get('name','English')} language."

    # v11: Load proven title formats from config
    title_formats = "\n".join(f"  \u2022 {f}" for f in getattr(config, "HIGH_PERFORMING_TITLE_FORMATS", []))

    prompt = f"""You are the head writer for "Archive of Enigmas" — a true crime YouTube channel aiming to go viral.
Write a COMPLETE 18-22 minute video script (3000+ words) about this case.{lang_instruction}

Story Title: {story['title']}
Story Content: {story['content']}

RECENT TITLES (DO NOT repeat these patterns): {recent_titles_str}

STRUCTURE (CRITICAL — must hit 3000+ words):
[HOOK — 90 seconds] Open with the MOST shocking moment. No intro yet. Drop viewer into the action.
[TEASER] Preview 3 shocking things they will learn. Subscribe reminder.
[CHAPTER 1: THE VICTIM / BACKGROUND — 4 mins] Full scene setting. Who were they? Make viewer care.
  End with cliffhanger question. [PAUSE marker here]
[CHAPTER 2: THE CRIME — 5 mins] Minute-by-minute breakdown. Maximum tension. Specific details.
  [PAUSE] [POLL TEASER: Ask viewers to comment their theory before continuing]
[CHAPTER 3: THE INVESTIGATION — 4 mins] Police failures. Key clues. Suspects. Red herrings.
  [PAUSE] [ENGAGEMENT: Drop your theory below]
[CHAPTER 4: SHOCKING REVELATIONS — 3 mins] Plot twists. Things nobody expected.
[CHAPTER 5: AFTERMATH & JUSTICE — 2 mins] What happened next. Sentencing or cold case status.
[OUTRO — 1 min] Ask 2 engagement questions. Subscribe CTA. Preview next video.

WRITING RULES:
- 3000+ words MINIMUM. Long = more watch time = algorithm favors you.
- Use "you" constantly — make it personal and immersive.
- End EVERY chapter with a cliffhanger or question.
- Add specific dates, names, locations — specificity builds credibility.
- Include [PAUSE] markers every 5-7 minutes for chapter cards.
- Sound like a gripping podcast host, NOT a Wikipedia article.
- Include 2-3 moments that will make viewers COMMENT (controversy, surprise, injustice).


Then:
---METADATA---
TITLE: (CRITICAL RULES:
  1. Under 70 characters.
  2. MUST include a real name (victim OR perpetrator) OR a specific location/year.
  3. Use ONE of these proven high-CTR formats:
{title_formats}
  4. Must create an unanswered question or shocking contrast.
  5. Must NOT be similar to: {recent_titles_str}
  6. NO generic phrases like "True Crime Story" or "Dark Case" — be SPECIFIC.
  BAD title example: "Virginia Horror" — no name, no hook, no specificity.
  GOOD title example: "The Virginia Mom Who Poisoned Her Family for 3 Years")
DESCRIPTION: (400 word SEO-rich description. Include: what happened, why it matters, keywords, timestamps teaser)
TAGS: (30 tags comma-separated — mix of broad and niche true crime terms)
THUMBNAIL_TEXT: (3-5 ALL-CAPS words — shocking, specific, curiosity-gap. NOT generic.
  BAD: "SHOCKING CASE" | GOOD: "SHE KNEW TOO MUCH" or "KILLER NEXT DOOR" or "13 YEARS MISSING")
THUMBNAIL_MOOD: (dark/red/split/face)
THUMBNAIL_STYLE: (1, 2, 3, or 4 — pick best for emotional impact)
PINNED_COMMENT: (A controversial OR divisive question that sparks debate)
COMMUNITY_POST: (60-word Community tab post with poll question)
CHAPTERS: (YouTube timestamps, one per line, format: "0:00 Hook")
"""
    resp = groq_create_with_retry(
        client,
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000, temperature=0.88)

    full = resp.choices[0].message.content

    # Shorts call
    print("  📱 Generating Shorts script (separate call)...")
    try:
        shorts_resp = groq_create_with_retry(
            client,
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content":
                f"""Write a YouTube Shorts script (55 seconds, exactly 130-150 words) \
about this true crime case: {story['title']}\n\nContext: {story['content'][:800]}\n\nRULES:\n- Hook in the FIRST 3 WORDS — no intro, no "hey guys"\n- Fast punchy sentences. Maximum tension.\n- Include ONE shocking specific detail (date, name, number)\n- End with a question that makes viewers follow\n- Final line MUST be: "Follow for daily mysteries."\n- Write ONLY the spoken words, no stage directions.{lang_instruction}"""
            }],
            max_tokens=400, temperature=0.85)
        shorts_script = shorts_resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠️ Shorts call failed: {e}")
        shorts_script = ""

    if "---METADATA---" in full:
        script, meta_raw = full.split("---METADATA---", 1)
    else:
        script, meta_raw = full, ""

    metadata = {}
    cur_key, cur_val = None, []
    for line in meta_raw.strip().split("\n"):
        matched = False
        for key in ["TITLE","DESCRIPTION","TAGS","THUMBNAIL_TEXT","THUMBNAIL_MOOD",
                    "THUMBNAIL_STYLE","PINNED_COMMENT","COMMUNITY_POST","CHAPTERS"]:
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
    metadata.setdefault("thumbnail_style", random.choice(config.THUMBNAIL_STYLES))
    metadata.setdefault("pinned_comment", "What do YOU think happened? Drop your theory! 👇")
    metadata.setdefault("community_post", f"We just dropped a new case. {story['title']}. Do you think justice was served? Comment your theory!")

    topic_key   = story.get("topic", "other")
    _EXTRA_NICHE = {
        "assault":  ["#CrimesAgainstWomen","#JusticeForVictims","#SexualAssaultAwareness"],
        "caste":    ["#CasteViolence","#DalitRights","#HonourCrime","#JusticeInIndia"],
        "poison":   ["#PoisoningCase","#TrueCrimePoison","#DarkMedicine"],
        "fraud":    ["#WhiteCollarCrime","#FinancialFraud","#CorporateCrime"],
        "kidnap":   ["#KidnappingCase","#AbductionStory","#FoundAlive"],
    }
    niche = (config.NICHE_HASHTAGS.get(topic_key) or
             _EXTRA_NICHE.get(topic_key) or
             config.NICHE_HASHTAGS.get("default", []))

    # Add language-specific hashtags
    lang_suffix = config.SUPPORTED_LANGUAGES.get(language, {}).get("hashtag_suffix", "")
    trending = getattr(config, "TRENDING_HASHTAGS", [])
    hashtags = " ".join(config.BASE_HASHTAGS[:15] + niche[:5] + trending[:3]) + lang_suffix
    metadata["hashtags"] = hashtags

    chapters = metadata.get("chapters", "0:00 Hook\n2:00 Background\n6:00 The Crime\n11:00 Investigation\n16:00 Aftermath\n19:00 Conclusion")
    metadata["full_description"] = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters}

🔔 Subscribe for daily true crime → {config.CHANNEL_HANDLE}
👍 Like if this gave you chills
💬 Drop your theory below — we read every comment!
🔕 Turn on notifications so you never miss a case

{hashtags}

© {config.CHANNEL_NAME} — Educational purposes only. All content based on public records."""

    # Auto-inject location + year tags for better SEO discoverability
    import re as _re
    year_matches = _re.findall(r'\b(19|20)\d{2}\b', story.get("content", "") + story.get("title", ""))
    year_tags    = [y for y in dict.fromkeys(year_matches)][:2]          # up to 2 unique years
    # Pull capitalised words likely to be place names (2+ consecutive caps words)
    place_matches = _re.findall(r'\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)', story.get("title",""))
    place_tags    = [p for p in place_matches if p not in ("The","She","He","They","What","Who","How","Why")][:3]
    raw_tags      = [t.strip() for t in metadata["tags"].split(",")]
    bonus_tags    = ([f"true crime {y}" for y in year_tags] +
                     [f"{p} crime" for p in place_tags] +
                     [f"{p} murder" for p in place_tags])
    metadata["tags_list"] = (raw_tags + bonus_tags)[:35]   # YouTube allows up to 500 chars total
    wc = len(script.split())
    print(f"✅ Main script: {wc} words (~{wc//150} mins)")
    print(f"✅ Shorts script: {len(shorts_script.split())} words")
    return script.strip(), shorts_script, metadata


# ============================================
# STEP 5b — TRANSLATE SCRIPT (Multi-language)
# FIX: Now properly updates title, description and all metadata
# ============================================

def translate_script(script, shorts_script, metadata, target_lang):
    """Translate script and ALL metadata to target language using Groq."""
    if target_lang == "en":
        return script, shorts_script, metadata

    lang_info = config.SUPPORTED_LANGUAGES.get(target_lang, {})
    lang_name = lang_info.get("name", target_lang)
    print(f"\n🌍 Translating to {lang_name}...")

    client = Groq(api_key=config.GROQ_API_KEY)

    # Translate main script (truncate to fit token budget)
    resp = groq_create_with_retry(
        client,
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content":
            f"Translate this true crime script to {lang_name}. Keep all [PAUSE] and [CHAPTER] markers. Keep the dramatic tone:\n\n{script[:4000]}"}],
        max_tokens=5000, temperature=0.3)
    translated_script = resp.choices[0].message.content

    # FIX: Translate shorts and metadata using structured JSON output
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
        # Strip markdown fences if present
        raw = re.sub(r'^```[a-z]*\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
        translated_meta = json.loads(raw)

        # Update metadata with translations
        metadata = dict(metadata)  # copy
        metadata["title"]          = translated_meta.get("title", metadata["title"])
        metadata["description"]    = translated_meta.get("description", metadata["description"])
        metadata["pinned_comment"] = translated_meta.get("pinned_comment", metadata["pinned_comment"])
        metadata["community_post"] = translated_meta.get("community_post", metadata["community_post"])
        translated_shorts          = translated_meta.get("shorts_script", shorts_script)

        # Rebuild full description with translated parts
        chapters = metadata.get("chapters", "0:00 Hook")
        lang_suffix = lang_info.get("hashtag_suffix", "")
        trending = getattr(config, "TRENDING_HASHTAGS", [])
        hashtags = " ".join(config.BASE_HASHTAGS[:10] + trending[:3]) + lang_suffix
        metadata["hashtags"] = hashtags
        metadata["full_description"] = f"""{metadata['description']}

⏱️ CHAPTERS:
{chapters}

🔔 Subscribe for daily true crime → {config.CHANNEL_HANDLE}
👍 Like if this gave you chills
💬 Drop your theory below — we read every comment!
🔕 Turn on notifications so you never miss a case

{hashtags}

© {config.CHANNEL_NAME} — Educational purposes only. All content based on public records."""

    except Exception as e:
        print(f"  ⚠️ Metadata translation parse failed: {e} — using English metadata")
        translated_shorts = shorts_script

    print(f"✅ Translation to {lang_name} done!")
    return translated_script, translated_shorts, metadata


# ============================================
# STEP 6 — VOICEOVER
# ============================================

async def _edge_tts_chunk(text, voice, output_path, rate=None, volume=None):
    rate   = rate   or config.TTS_RATE
    volume = volume or config.TTS_VOLUME
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_path)

def generate_voiceover(script, label="voiceover", voice=None, rate=None):
    voice  = voice  or config.TTS_VOICE
    rate   = rate   or config.TTS_RATE
    print(f"\n🎙️  Generating {label} with edge-tts ({voice})...")
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    audio_path = os.path.join(config.OUTPUT_FOLDER, f"{label}.mp3")

    clean = re.sub(r'\[.*?\]', '', script).replace("[PAUSE]"," ... ").strip()
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'\*+', '', clean)

    max_chars = 3000
    chunks    = []
    remaining = clean
    while len(remaining) > max_chars:
        cut = remaining.rfind('. ', 0, max_chars)
        if cut == -1: cut = max_chars
        chunks.append(remaining[:cut + 1])
        remaining = remaining[cut + 1:].strip()
    if remaining:
        chunks.append(remaining)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        p = os.path.join(config.OUTPUT_FOLDER, f"edge_chunk_{i}.mp3")
        try:
            asyncio.run(_edge_tts_chunk(chunk, voice, p, rate))
            chunk_paths.append(p)
            print(f"  🎙️ Chunk {i+1}/{len(chunks)} done")
        except Exception as e:
            print(f"  ⚠️ edge-tts chunk {i} failed: {e}")
            silent = AudioClip(lambda t: 0, duration=5)
            silent.write_audiofile(p, fps=44100, logger=None)
            chunk_paths.append(p)

    if len(chunk_paths) == 1:
        shutil.copy(chunk_paths[0], audio_path)
    else:
        clips  = [AudioFileClip(p) for p in chunk_paths]
        merged = concatenate_audioclips(clips)
        merged.write_audiofile(audio_path, fps=44100, logger=None)
        for c in clips: c.close()

    for p in chunk_paths:
        try: os.remove(p)
        except: pass

    print(f"✅ Voiceover done! ({label})")
    return audio_path


# ============================================
# STEP 6b — BACKGROUND MUSIC
# ============================================

# ============================================
# v12 COPYRIGHT FIX: Background music DISABLED
# ============================================
# WHY: Every Pixabay/CDN URL — even "free" tracks — can carry a
# YouTube Content ID claim that mutes or demonetises your video.
# Voice-only is the default used by top true crime channels.
# To add music later: use ONLY YouTube Audio Library tracks
# (studio.youtube.com > Audio Library) — pre-cleared for YT.
# ============================================

def fetch_background_music():
    print("\n🎵 Background music: DISABLED (copyright protection)")
    return None

def mix_audio_with_music(voice_path, music_path, output_path):
    # Always return voice-only — safe from Content ID claims
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
# STEP 9 — CHAPTER CARDS (Cinematic Style)
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


# ============================================
# STEP 10 — ASSEMBLE MAIN VIDEO (1080p, 20min)
# ============================================

def assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story):
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    print(f"\n🎬 Step 10: Assembling {W}x{H} documentary video...")
    audio     = AudioFileClip(audio_path)
    total_dur = audio.duration

    print(f"  ⏱️  Duration : {total_dur/60:.1f} minutes")
    print(f"  📸 Images   : {len(image_paths)}")
    print(f"  🎥 Videos   : {len(video_clips)}")

    KB_DIRS    = ["zoom_in","zoom_out","pan_left","pan_right","pan_up","diagonal","slow_zoom"]
    IMG_DUR    = 8.0
    VID_DUR    = 14.0
    CARD_DUR   = 3.0
    CARD_EVERY = 4

    media_sequence = []
    img_idx = vid_idx = 0
    while True:
        for _ in range(2):
            if image_paths:
                media_sequence.append(("image", image_paths[img_idx % len(image_paths)], IMG_DUR, KB_DIRS[img_idx % len(KB_DIRS)]))
                img_idx += 1
        if video_clips:
            media_sequence.append(("video", video_clips[vid_idx % len(video_clips)], VID_DUR, None))
            vid_idx += 1
        total_estimated = sum(m[2] for m in media_sequence) + (len(media_sequence)//CARD_EVERY) * CARD_DUR
        if total_estimated >= total_dur + 30: break
        if len(media_sequence) > 600: break

    print(f"  🎞️  Media slots: {len(media_sequence)}")

    clips     = []
    time_used = 0.0
    clips.append(create_chapter_card(metadata.get("title","True Crime")[:55], duration=5.0))
    time_used += 5.0

    chapter_names = ["The Background","The Crime","The Investigation","The Shocking Truth","The Aftermath"]
    chapter_count = media_count = 0

    for m_type, m_data, m_dur, m_extra in media_sequence:
        if time_used >= total_dur - 1.0: break
        remaining = total_dur - time_used

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
    clips.append(create_chapter_card("🔴 Subscribe for Daily Mysteries", duration=outro_dur))

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
    out   = os.path.join(config.OUTPUT_FOLDER, "final_video.mp4")
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
# FIX: Story-seeded randomisation prevents repeated thumbnails
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
    """
    FIX: Use story title as random seed so every story gets a different
    background image, preventing repeated thumbnail visuals.
    Score all candidates, then pick randomly from the top 3.
    """
    import random as _r
    rng = _r.Random(hash(story_title) % 2**31)
    # Score more candidates than before (up to 12)
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
    # FIX: Pick randomly from top 3 (not always the absolute best)
    top3 = [p for _, p in scored[:3]]
    return rng.choice(top3)

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 11: Creating thumbnail...")
    W, H  = config.THUMBNAIL_WIDTH, config.THUMBNAIL_HEIGHT
    thumb = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")

    style      = str(metadata.get("thumbnail_style", "1")).strip()
    thumb_text = metadata.get("thumbnail_text", "SHOCKING CASE").upper()
    if len(thumb_text) > 28:
        thumb_text = thumb_text[:25].rsplit(" ", 1)[0] + "..."

    raw_title  = story["title"]

    FONT_PATH_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    FONT_PATH_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    # v11 FIX: Use Bebas Neue for headline text if available (looks like Netflix/crime docs)
    BEBAS_PATH = BEBAS_FONT_PATH or config.FONT_CACHE_PATH
    HEADLINE_FONT_PATH = BEBAS_PATH if (BEBAS_PATH and os.path.exists(BEBAS_PATH)) else FONT_PATH_BOLD
    try:
        word_count = len(thumb_text.split())
        hl_size    = 118 if word_count <= 2 else (96 if word_count <= 4 else 80)
        f_hl  = ImageFont.truetype(HEADLINE_FONT_PATH, hl_size)
        f_lg  = ImageFont.truetype(FONT_PATH_BOLD, 52)
        f_md  = ImageFont.truetype(FONT_PATH_BOLD, 36)
        f_sm  = ImageFont.truetype(FONT_PATH_REG,  26)
        f_tag = ImageFont.truetype(FONT_PATH_BOLD, 22)
    except:
        f_hl = f_lg = f_md = f_sm = f_tag = ImageFont.load_default()

    # FIX: Pass story title for seeded randomisation
    bg_path  = _best_bg_image(image_paths, story_title=raw_title) if image_paths else None
    base_img = Image.new("RGB", (W, H), (10, 0, 0))
    if bg_path:
        try:
            base_img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)
        except:
            pass

    def draw_headline(draw, text, font, zone_y, zone_h, fill=(255,255,255), max_w=None):
        max_w  = max_w or W - 60
        lines  = _wrap_text(draw, text, font, max_w)
        lh     = draw.textbbox((0,0), "Ag", font=font)[3] + 8
        total  = lh * len(lines)
        y      = zone_y + (zone_h - total) // 2
        for line in lines:
            lw = draw.textbbox((0,0), line, font=font)[2]
            x  = (W - lw) // 2
            _draw_text_shadow(draw, x, y, line, font, fill=fill)
            y += lh
        return y

    def draw_bottom_bar(draw, bar_color=(20,0,0), accent=(200,0,0)):
        draw.rectangle([(0, H-72), (W, H)], fill=bar_color)
        draw.rectangle([(0, H-74), (W, H-72)], fill=accent)
        title_lines = _wrap_text(draw, raw_title, f_md, W - 60)
        line = title_lines[0][:55] + ("..." if len(title_lines[0]) > 55 else "")
        lw   = draw.textbbox((0,0), line, font=f_md)[2]
        draw.text(((W-lw)//2, H-62), line, font=f_md, fill=(240,240,240))

    def draw_badge(draw, bg=(180,0,0), fg=(255,255,255)):
        label = config.CHANNEL_NAME.upper()
        lw    = draw.textbbox((0,0), label, font=f_tag)[2]
        pad   = 12
        draw.rounded_rectangle([(18,14),(lw+pad*2+18, 46)], radius=4, fill=bg)
        draw.text((18+pad, 18), label, font=f_tag, fill=fg)

    if style == "1":
        img = ImageEnhance.Brightness(base_img).enhance(0.28)
        img = ImageEnhance.Color(img).enhance(0.5)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        grad = Image.new("RGBA", (W, H), (0,0,0,0))
        gd   = ImageDraw.Draw(grad)
        for y in range(H):
            alpha = int(160 - 120 * abs(y/H - 0.5))
            gd.line([(0,y),(W,y)], fill=(0,0,0,alpha))
        img = Image.alpha_composite(img.convert("RGBA"), grad).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw_badge(draw)
        draw_headline(draw, thumb_text, f_hl, zone_y=60, zone_h=H-140, fill=(255,255,255))
        draw_bottom_bar(draw)

    elif style == "2":
        left  = base_img.crop((0, 0, W//2, H))
        right = base_img.crop((W//2, 0, W, H))
        left  = ImageEnhance.Brightness(left).enhance(0.22)
        left  = ImageEnhance.Color(left).enhance(0.2)
        right = ImageEnhance.Brightness(right).enhance(0.30)
        right = ImageEnhance.Color(right).enhance(0.45)
        tint     = Image.new("RGBA", (W//2, H), (160,0,0,130))
        left_img = Image.alpha_composite(left.convert("RGBA"), tint).convert("RGB")
        img      = Image.new("RGB", (W, H))
        img.paste(left_img, (0, 0))
        img.paste(right, (W//2, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(W//2-4, 0), (W//2+4, H)], fill=(230,0,0))
        draw_badge(draw)
        draw_headline(draw, thumb_text, f_hl, zone_y=60, zone_h=H-140, max_w=W//2-40, fill=(255,255,255))
        sub_lines = _wrap_text(draw, raw_title, f_md, W//2-40)
        sy = H//2 - 30
        for line in sub_lines[:2]:
            lw = draw.textbbox((0,0), line, font=f_md)[2]
            x  = W//2 + (W//2 - lw)//2
            _draw_text_shadow(draw, x, sy, line, f_md, fill=(255,220,0))
            sy += 46
        draw_bottom_bar(draw, bar_color=(20,0,0), accent=(200,0,0))

    elif style == "3":
        img  = ImageEnhance.Brightness(base_img).enhance(0.15)
        img  = ImageEnhance.Color(img).enhance(0.2)
        img  = img.filter(ImageFilter.GaussianBlur(radius=2))
        vig  = Image.new("RGBA", (W, H), (0,0,0,0))
        vd   = ImageDraw.Draw(vig)
        for i in range(0, 350, 2):
            a = min(int(i * 0.65), 255)
            vd.rectangle([(i,i),(W-i,H-i)], outline=(0,0,0,a))
        img  = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw_badge(draw, bg=(120,0,0))
        draw_headline(draw, thumb_text, f_hl, zone_y=60, zone_h=H-140, fill=(255,40,40))
        draw_bottom_bar(draw, bar_color=(15,0,0), accent=(160,0,0))

    else:
        img  = ImageEnhance.Brightness(base_img).enhance(0.25)
        img  = ImageEnhance.Color(img).enhance(0.35)
        grad = Image.new("RGBA", (W, H), (0,0,0,0))
        gd   = ImageDraw.Draw(grad)
        for y in range(H):
            alpha = int(180 * (1 - y/H * 0.4))
            gd.line([(0,y),(W,y)], fill=(0,0,0,alpha))
        img  = Image.alpha_composite(img.convert("RGBA"), grad).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0),(W,64)], fill=(220,170,0))
        warn = "TRUE CRIME  //  " + config.CHANNEL_NAME.upper() + "  //  DARK CASE"
        ww   = draw.textbbox((0,0), warn, font=f_sm)[2]
        draw.text(((W-ww)//2, 18), warn, font=f_sm, fill=(0,0,0))
        draw_headline(draw, thumb_text, f_hl, zone_y=70, zone_h=H-160, fill=(255,255,255))
        sub_lines = _wrap_text(draw, raw_title, f_lg, W-80)
        sy = H - 130
        for line in sub_lines[:1]:
            lw = draw.textbbox((0,0), line, font=f_lg)[2]
            _draw_text_shadow(draw, (W-lw)//2, sy, line, f_lg, fill=(255,210,0))
        draw.rectangle([(0,H-60),(W,H)], fill=(10,0,0))
        draw.rectangle([(0,H-62),(W,H-60)], fill=(220,170,0))
        draw.text((24,H-48), "UNSOLVED  *  TRUE CRIME  *  DARK MYSTERIES", font=f_tag, fill=(130,130,130))

    img.save(thumb, "JPEG", quality=95, optimize=True)
    size_kb = os.path.getsize(thumb) // 1024
    print(f"✅ Thumbnail created! Style {style} | {W}x{H} | {size_kb}KB")
    return thumb


# ============================================
# STEP 12 — UPLOAD TO YOUTUBE
# FIX: Now accepts language parameter and sets correct defaultLanguage
# ============================================

def upload_to_youtube(video_path, thumbnail_path, metadata, is_short=False, language="en"):
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
        tags        = metadata.get("tags_list",[]) + ["Shorts","TrueCrimeShorts","#Shorts"]
    else:
        description = metadata.get("full_description","")
        tags        = metadata.get("tags_list",[])

    # FIX: Use the actual language code for this video
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:500],
            "categoryId": "25",
            "defaultLanguage": language,          # FIX: was hardcoded "en"
            "defaultAudioLanguage": language,     # FIX: was hardcoded "en"
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    try:
        resp = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    except Exception as e:
        if "uploadLimitExceeded" in str(e):
            print("\u26a0\ufe0f  YouTube daily upload limit reached for this channel.")
            print("   \u27a1  Verify your channel at https://youtube.com/verify to lift the cap.")
            print("   \u23ed  Skipping upload — video saved locally at:", video_path)
            return None
        raise
    vid   = resp.get("id")
    print(f"✅ {kind} uploaded! ID: {vid}")

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
                import traceback
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
        pinned     = metadata.get("pinned_comment","What do YOU think happened? 👇")
        tmpl       = random.choice(config.PINNED_COMMENT_TEMPLATES)
        pinned_msg = tmpl.format(question=pinned, handle=config.CHANNEL_HANDLE)
        try:
            thread = yt.commentThreads().insert(
                part="snippet",
                body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{"textOriginal":pinned_msg}}}}).execute()
            comment_id = thread["snippet"]["topLevelComment"]["id"]
            # Pin it so it's always top
            try:
                yt.comments().setModerationStatus(
                    id=comment_id,
                    moderationStatus="published",
                    banAuthor=False
                ).execute()
            except Exception:
                pass  # pinning needs extra OAuth scope; gracefully skip if unavailable
            print("✅ Pinned comment posted!")
        except Exception as e:
            print(f"⚠️ Comment: {e}")

    print(f"\n🎉 LIVE: https://youtube.com/watch?v={vid}")
    return vid


# ============================================
# MAIN PIPELINE
# FIX: Now reads BOT_LANGUAGE env var to run any language
# ============================================

def run_pipeline():
    global BEBAS_FONT_PATH

    # v11: Read language from environment variable
    lang = os.environ.get("BOT_LANGUAGE", "en").strip().lower()
    lang_cfg  = config.SUPPORTED_LANGUAGES.get(lang, config.SUPPORTED_LANGUAGES["en"])
    lang_name = lang_cfg.get("name", "English")
    voice     = lang_cfg.get("voice", config.TTS_VOICE)
    rate      = lang_cfg.get("rate",  config.TTS_RATE)

    print("="*55)
    print(f"🚀 ARCHIVE OF ENIGMAS — Pipeline v11 | Lang: {lang_name}")
    print("="*55)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    # v11 FIX: Download Bebas Neue font once per run for better thumbnails
    BEBAS_FONT_PATH = ensure_bebas_font()

    try:
        # 1. Fetch story (Wikipedia = English guaranteed)
        story = fetch_story()
        topic = story.get("topic", "other")
        print(f"  📌 Topic: {topic} | Language: {lang_name}")

        # 2. Generate script
        if lang == "en":
            script, shorts_script, metadata = generate_script(story, language="en")
        else:
            print(f"  🌐 Generating English base, then translating to {lang_name}...")
            script, shorts_script, metadata = generate_script(story, language="en")
            script, shorts_script, metadata = translate_script(script, shorts_script, metadata, lang)

        # 3. Fetch media
        img_queries, vid_queries = extract_keywords(story)
        image_paths = fetch_images(img_queries, target=24)
        video_clips = fetch_videos(vid_queries, target=14)

        # 4. Voiceover with language-specific voice
        audio_path        = generate_voiceover(script, label=f"voiceover_{lang}", voice=voice, rate=rate)
        shorts_audio_path = None
        if shorts_script:
            shorts_audio_path = generate_voiceover(
                shorts_script, label=f"shorts_voiceover_{lang}", voice=voice, rate=rate)

        # 4b. Background music
        music_path       = fetch_background_music()
        mixed_audio_path = os.path.join(config.OUTPUT_FOLDER, f"voiceover_{lang}_mixed.mp3")
        audio_path       = mix_audio_with_music(audio_path, music_path, mixed_audio_path)

        # 5. Thumbnail (story-seeded, no repeats, Bebas Neue font)
        thumbnail_path = create_thumbnail(image_paths, metadata, story)

        # 6. Assemble main video
        video_path = assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story)

        # 7. Assemble Shorts
        shorts_path = None
        if shorts_audio_path and image_paths:
            try:
                shorts_path = assemble_shorts_video(shorts_audio_path, image_paths, metadata)
            except Exception as e:
                print(f"⚠️ Shorts assembly failed: {e}")

        # 8. Upload with correct language metadata
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

        # 9. v11 FIX: Update history for ALL languages (prevents cross-language topic duplicates)
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
        print(f"🎤 Voice   : edge-tts ({voice})")
        print("="*55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback; traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
    

