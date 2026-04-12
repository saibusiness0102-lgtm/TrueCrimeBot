# ============================================
# ARCHIVE OF ENIGMAS — DOCUMENTARY BOT v8 VIRAL
# 20-min videos | 1080p | 7-Language | Peak SEO
# Interactive Shorts | A/B Thumbnails | Polls
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

def update_history(title, topic_type, keywords):
    h = load_history()
    h["recent_titles"]   = ([title] + h["recent_titles"])[:20]
    h["recent_topics"]   = ([topic_type] + h["recent_topics"])[:10]
    h["recent_keywords"] = (keywords + h["recent_keywords"])[:30]
    save_history(h)

# Core crime nouns — if ANY of these overlap between titles we block it
_CRIME_NOUNS = {
    "vanish","vanishes","vanished","missing","disappear","disappeared",
    "murder","murdered","killer","killed","killing","kill","dead","death",
    "rape","raped","assault","assaulted","kidnap","kidnapped","abduct",
    "found","body","hunt","case","mom","mother","father","dad","daughter",
    "son","child","children","woman","man","girl","boy","teen","wife",
    "husband","family","couple","sister","brother","baby","infant",
}

def _title_key_nouns(title):
    """Return the set of crime-relevant words in a title (lowercase)."""
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
        # Block if 2+ key nouns overlap (e.g. "mom"+"vanish" = same story angle)
        if len(overlap) >= 2:
            print(f"  ⚠️  Too similar to: '{old_title}' (shared: {overlap}). Skipping.")
            return True
        # Also block exact first-3-word match
        if title.lower().split()[:3] == old_title.lower().split()[:3]:
            print(f"  ⚠️  Title starts identically to: '{old_title}'. Skipping.")
            return True
    return False

def detect_topic_type(text):
    text = text.lower()
    # Order matters: more specific first
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
        # ── International true crime ─────────────────────
        "https://www.crimeonline.com/feed/",
        "https://www.oxygen.com/rss.xml",
        "https://www.investigationdiscovery.com/feed",
        # ── General news — murders/fraud/assault reported ─
        "https://abcnews.go.com/US/feed",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Crime.xml",
        "https://www.theguardian.com/uk/crime/rss",
        # ── India / South Asia crimes ─────────────────────
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://feeds.feedburner.com/ndtvnews-india-news",
        # ── Court / justice reporting ─────────────────────
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
        # ── ICONIC SERIAL KILLERS ─────────────────────────────────────────
        "Zodiac Killer","Jack the Ripper","Golden State Killer","Ted Bundy",
        "Jeffrey Dahmer","John Wayne Gacy","BTK killer","Gary Ridgway",
        "Samuel Little","Ed Kemper","Richard Ramirez","Dean Corll",
        "Andrei Chikatilo","Aileen Wuornos","Harold Shipman","H. H. Holmes",
        "Charles Manson","Pedro Lopez","Luis Garavito","John Edward Robinson",
        # ── MURDERS & HIGH-PROFILE CASES ─────────────────────────────────
        "Black Dahlia murder","Villisca axe murders","Hinterkaifeck murders",
        "Axeman of New Orleans","Cleveland torso murderer","Lizzie Borden",
        "Chris Watts murders","JonBenet Ramsey","Tylenol murders",
        "West Memphis Three","Delphi murders","OJ Simpson trial",
        "Amanda Knox","Steven Avery","Scott Peterson case",
        "Menendez brothers","Pamela Smart","Drew Peterson",
        "Robert Durst","Phil Spector murder","Oscar Pistorius trial",
        "Murder of Meredith Kercher","Yvonne Fletcher murder",
        # ── CASTE / HONOUR / DOWRY CRIMES (India & South Asia) ───────────
        "Khairlanji massacre","Nithari killings","Priyadarshini Mattoo case",
        "Bhanwari Devi murder case","Jessica Lal murder case",
        "Aarushi Talwar murder case","Sheena Bora murder case",
        "Bijal Joshi rape case","Nirbhaya case","Unnao rape case",
        "Kathua rape case","Hathras case","Budaun murders India",
        "Rohtak honour killing India","Manoj Babli honour killing",
        "Ilavarasan death case Tamil Nadu","Thangjam Manorama case",
        # ── FRAUD / FINANCIAL CRIME ───────────────────────────────────────
        "Bernie Madoff Ponzi scheme","Enron scandal","WorldCom fraud",
        "Elizabeth Holmes Theranos","Anna Sorokin fraud","Frank Abagnale",
        "Satyam scandal India","2G spectrum scam India","Harshad Mehta scam",
        "Vijay Mallya fraud","Nirav Modi diamond fraud","Subrata Roy fraud",
        # ── KIDNAPPING / ABDUCTION ────────────────────────────────────────
        "Jaycee Dugard kidnapping","Elizabeth Smart kidnapping",
        "Ariel Castro kidnappings","Natascha Kampusch kidnapping",
        "Patty Hearst kidnapping","Lindbergh kidnapping",
        "Getty kidnapping 1973","Frank Sinatra Jr kidnapping",
        # ── POISONING CASES ───────────────────────────────────────────────
        "Alexander Litvinenko poisoning","Salisbury Novichok attack",
        "Georgi Markov assassination","Graham Young poisoner",
        "Marie Besnard poison murders","Nannie Doss poisoner",
        # ── CULTS / MASS EVENTS ───────────────────────────────────────────
        "Jonestown massacre","Heaven's Gate cult","NXIVM cult",
        "Aum Shinrikyo","Branch Davidians Waco","The Family cult Australia",
        "Order of the Solar Temple","Rajneeshee bioterror attack",
        # ── HEISTS / THEFT ────────────────────────────────────────────────
        "DB Cooper","Isabella Stewart Gardner Museum theft",
        "Great Train Robbery 1963","Antwerp diamond heist",
        "Hatton Garden heist","Banco Central Brazil robbery",
        "Dunbar Armored robbery","Lufthansa heist 1978",
        # ── UNSOLVED / MYSTERIOUS ─────────────────────────────────────────
        "Tamam Shud case","Dyatlov Pass incident","Isdal Woman",
        "Beaumont children disappearance","Sodder children disappearance",
        "Zodiac ciphers","D.B. Cooper","Marilyn Monroe death",
        "Elisa Lam case","Max Headroom broadcast intrusion",
        "Boy in the box Philadelphia","Babushka Lady assassination",
        "Gabby Petito case","Delphi murders cold case",
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
    content = story["content"].lower()

    image_queries = [
        "crime scene tape dark night","detective noir shadow investigation",
        "old newspaper crime headline vintage","dark foggy forest mystery",
        "fingerprint forensic evidence closeup","abandoned house dark night",
        "silhouette dark figure mystery","courtroom justice vintage dark",
        "wanted poster vintage crime","dark alley rain night cinematic",
        "candlelight dark room mystery","old photograph vintage sepia dark",
        "magnifying glass detective clue","police badge dark dramatic",
        "prison bars dark shadow","forensic lab dark dramatic",
        "detective board crime suspects","blood spatter dark investigation",
        "crime map pins detective board","jail cell dramatic",
        "dark cemetery tombstones fog","handcuffs dramatic arrest",
    ]

    video_queries = [
        "dark rainy city night","police car lights night",
        "fog forest dark eerie","rain window dark night",
        "storm lightning dramatic dark","dark ocean waves night",
        "smoke dark dramatic","fire dark night dramatic",
        "dark road night driving","prison gate dramatic",
        "detective walking rain coat","court room gavel dramatic",
    ]

    if any(w in title + content for w in ["murder","kill","dead","homicide"]):
        image_queries = ["crime scene investigation police","forensic dark dramatic","murder mystery detective noir"] + image_queries
    if any(w in title + content for w in ["missing","disappear","vanish"]):
        image_queries = ["missing person poster dark","search party flashlight","empty road dark night"] + image_queries
    if any(w in title + content for w in ["serial","killer"]):
        image_queries = ["detective board suspects investigation","prison dark corridor","shadow figure dark"] + image_queries

    random.shuffle(image_queries)
    random.shuffle(video_queries)
    return image_queries[:24], video_queries[:14]


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
                # Prefer original quality for 1080p output
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
                # Prefer 1080p quality
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

    prompt = f"""You are the writer for "Archive of Enigmas" — a top true crime YouTube channel.
Write a COMPLETE 18-22 minute video script (3000+ words) about this case.{lang_instruction}

Story Title: {story['title']}
Story Content: {story['content']}

RECENT TITLES (DO NOT repeat these patterns): {recent_titles_str}

STRUCTURE (CRITICAL — must hit 3000+ words):
[HOOK — 90 seconds] Open with the MOST shocking moment. No intro yet. Drop viewer into the action.
[TEASER] Preview 3 shocking things they'll learn. "Before we begin..." Subscribe reminder.
[CHAPTER 1: THE VICTIM / BACKGROUND — 4 mins] Full scene setting. Who were they? Make viewer care.
  End with cliffhanger question. [PAUSE marker here]
[CHAPTER 2: THE CRIME — 5 mins] Minute-by-minute breakdown. Maximum tension. Specific details.
  [PAUSE] [POLL TEASER: Ask viewers to comment their theory before continuing]
[CHAPTER 3: THE INVESTIGATION — 4 mins] Police failures. Key clues. Suspects. Red herrings.
  [PAUSE] [ENGAGEMENT: "Drop your theory below — who do you think did it?"]
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
TITLE: (Clickbait but accurate, under 70 chars — emotionally charged, NOT similar to: {recent_titles_str})
DESCRIPTION: (400 word SEO-rich description. Include: what happened, why it matters, keywords, timestamps teaser)
TAGS: (30 tags comma-separated — mix of broad and niche true crime terms)
THUMBNAIL_TEXT: (3-5 shocking all-caps words for thumbnail — e.g. "SHE KNEW TOO MUCH")
THUMBNAIL_MOOD: (dark/red/split/face)
THUMBNAIL_STYLE: (1, 2, 3, or 4 — pick best for emotional impact)
PINNED_COMMENT: (Controversial or intriguing question that drives comments)
COMMUNITY_POST: (60-word Community tab post with poll question)
CHAPTERS: (YouTube timestamps, one per line, format: "0:00 Hook")
"""

    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000, temperature=0.88)

    full = resp.choices[0].message.content

    # ── Separate Shorts call — never truncated by main script length ─────────
    print("  📱 Generating Shorts script (separate call)...")
    try:
        shorts_resp = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content":
                f"""Write a YouTube Shorts script (55 seconds, exactly 130-150 words) \
about this true crime case: {story['title']}\n\nContext: {story['content'][:800]}\n\nRULES:\n- Hook in the FIRST 3 WORDS — no intro, no "hey guys"\n- Fast punchy sentences. Maximum tension.\n- Include ONE shocking specific detail (date, name, number)\n- End with a question that makes viewers follow\n- Final line MUST be: "Follow for daily mysteries."\n- Write ONLY the spoken words, no stage directions."""
            }],
            max_tokens=400, temperature=0.85)
        shorts_script = shorts_resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠️ Shorts call failed: {e}")
        shorts_script = ""
    # ─────────────────────────────────────────────────────────────────────────

    # Extract metadata
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

    title_lower = story["title"].lower()
    topic_key   = story.get("topic", "other")
    # Extra niche hashtags for new topic types not in config
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

    # Add trending hashtags
    trending = getattr(config, "TRENDING_HASHTAGS", [])
    hashtags = " ".join(config.BASE_HASHTAGS[:15] + niche[:5] + trending[:3])
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

    metadata["tags_list"] = [t.strip() for t in metadata["tags"].split(",")][:30]
    wc = len(script.split())
    print(f"✅ Main script: {wc} words (~{wc//150} mins)")
    print(f"✅ Shorts script: {len(shorts_script.split())} words")
    return script.strip(), shorts_script, metadata


# ============================================
# STEP 5b — TRANSLATE SCRIPT (Multi-language)
# ============================================

def translate_script(script, shorts_script, metadata, target_lang):
    """Translate script and metadata to target language using Groq."""
    if target_lang == "en":
        return script, shorts_script, metadata

    lang_info = config.SUPPORTED_LANGUAGES.get(target_lang, {})
    lang_name = lang_info.get("name", target_lang)
    print(f"\n🌍 Translating to {lang_name}...")

    client = Groq(api_key=config.GROQ_API_KEY)

    # Translate main script
    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": f"Translate this true crime script to {lang_name}. Keep all [PAUSE] and [CHAPTER] markers. Keep the dramatic tone:\n\n{script[:4000]}"}],
        max_tokens=5000, temperature=0.3)
    translated_script = resp.choices[0].message.content

    # Translate shorts + metadata
    resp2 = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": f"Translate to {lang_name}: Title: {metadata['title']}\nDescription: {metadata['description'][:500]}\nShorts script: {shorts_script}\nPinned comment: {metadata['pinned_comment']}\n\nReturn in same format with labels."}],
        max_tokens=1500, temperature=0.3)

    print(f"✅ Translation to {lang_name} done!")
    return translated_script, shorts_script, metadata


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

FREE_MUSIC_URLS = [
    "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946f0a5c40.mp3",
    "https://cdn.pixabay.com/download/audio/2022/08/23/audio_d16737dc28.mp3",
    "https://cdn.pixabay.com/download/audio/2021/11/25/audio_cb31e37bb1.mp3",
    "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749dbac.mp3",
]

def fetch_background_music():
    print("\n🎵 Fetching background music...")
    music_path = os.path.join(config.OUTPUT_FOLDER, "bgmusic.mp3")
    if os.path.exists(music_path) and os.path.getsize(music_path) > 50000:
        print("  ✅ Using cached music")
        return music_path

    random.shuffle(FREE_MUSIC_URLS)
    for url in FREE_MUSIC_URLS:
        try:
            r = requests.get(url, timeout=20, stream=True)
            if r.status_code == 200:
                with open(music_path, "wb") as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                if os.path.getsize(music_path) > 50000:
                    print("  ✅ Background music downloaded!")
                    return music_path
        except Exception as e:
            print(f"  ⚠️ Music fetch: {e}")
    return None

def mix_audio_with_music(voice_path, music_path, output_path):
    if not music_path or not os.path.exists(music_path):
        return voice_path
    try:
        voice = AudioFileClip(voice_path)
        music = AudioFileClip(music_path)
        if music.duration < voice.duration:
            loops = int(math.ceil(voice.duration / music.duration)) + 1
            music = concatenate_audioclips([music] * loops)
        music = music.subclip(0, voice.duration)
        music = music.audio_fadein(3).audio_fadeout(5)
        music = music.volumex(0.10)  # 10% volume — barely audible atmosphere
        final_audio = CompositeAudioClip([voice, music])
        final_audio.write_audiofile(output_path, fps=44100, logger=None)
        voice.close(); music.close()
        print("  ✅ Audio mixed!")
        return output_path
    except Exception as e:
        print(f"  ⚠️ Mix failed: {e} — voice only")
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
        # Dark crimson fallback — never pure black; keeps cinematic feel
        fallback = np.zeros((H, W, 3), dtype=np.uint8)
        fallback[:, :, 0] = 18   # slight red tint
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
        p = p * p * (3 - 2 * p)  # Smooth ease
        x1 = max(0, min(int(sx1+(ex1-sx1)*p), nw-2))
        y1 = max(0, min(int(sy1+(ey1-sy1)*p), nh-2))
        x2 = max(x1+1, min(int(sx2+(ex2-sx2)*p), nw))
        y2 = max(y1+1, min(int(sy2+(ey2-sy2)*p), nh))
        crop = arr[y1:y2, x1:x2]
        if crop.size == 0:
            # Never return black — clamp coords and return full scaled array
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
        # Scale to 1080p maintaining aspect ratio
        clip = clip.resize(height=H)
        if clip.size[0] < W: clip = clip.resize(width=W)
        if clip.size[0] > W:
            xc = clip.size[0] // 2
            clip = clip.crop(x1=xc - W//2, x2=xc + W//2)
        if clip.size[1] > H:
            yc = clip.size[1] // 2
            clip = clip.crop(y1=yc - H//2, y2=yc + H//2)
        # Cinematic color grading
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

        # Cinematic red line accent
        lw = int(400 * alpha)
        draw.rectangle([(W//2 - lw//2, H//2 - 72), (W//2 + lw//2, H//2 - 68)], fill=(int(200*alpha),0,0))

        # Channel name
        sub = config.CHANNEL_NAME.upper()
        b   = draw.textbbox((0,0), sub, font=f_sub)
        draw.text(((W-(b[2]-b[0]))//2, H//2-112), sub, font=f_sub, fill=(int(100*alpha),0,0))

        # Chapter text
        b = draw.textbbox((0,0), text, font=f_big)
        tw = b[2]-b[0]
        # Shadow
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

    # Build media sequence
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
    # "compose" is safe now that every clip has .size set explicitly.
    # Do NOT free clips before write_videofile — concatenate is lazy and
    # holds live references into the clips list until rendering is done.
    try:
        video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print(f"  ⚠️ compose failed: {e}, trying chain...")
        video = concatenate_videoclips(clips, method="chain")

    if video.duration > total_dur + 0.5:
        video = video.subclip(0, total_dur)

    # Watermark overlay
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
    # threads=2: leave headroom so the runner OS isn't starved
    final.write_videofile(out, fps=config.VIDEO_FPS, codec="libx264", audio_codec="aac",
                          threads=2, preset="ultrafast", bitrate=config.VIDEO_BITRATE, logger=None)
    # Safe to free everything NOW — write_videofile has fully rendered all frames
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

        # Caption overlay at bottom
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
            # Red dot + channel name
            draw.ellipse([(36,20),(62,46)], fill=(220,0,0,255))
            draw.text((72, 22), config.CHANNEL_NAME, font=f_ch, fill=(220,220,220,230))
            # Title (split into 2 lines)
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

def create_thumbnail(image_paths, metadata, story):
    print("\n🖼️  Step 11: Creating thumbnail...")
    W, H  = config.THUMBNAIL_WIDTH, config.THUMBNAIL_HEIGHT
    thumb = os.path.join(config.OUTPUT_FOLDER, "thumbnail.jpg")

    style      = metadata.get("thumbnail_style","1").strip()
    thumb_text = metadata.get("thumbnail_text","SHOCKING CASE").upper()
    title_text = story["title"][:45] + ("..." if len(story["title"]) > 45 else "")

    try:
        f_xl  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 96)
        f_lg  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 58)
        f_md  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
        f_sm  = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 28)
    except:
        f_xl = f_lg = f_md = f_sm = ImageFont.load_default()

    base_img = Image.new("RGB",(W,H),(8,0,0))
    if image_paths:
        try:
            base_img = Image.open(image_paths[0]).convert("RGB").resize((W,H), Image.LANCZOS)
        except:
            pass

    if style == "2":
        # Red split — great for murders/killers
        left  = base_img.crop((0,0,W//2,H))
        right = base_img.crop((W//2,0,W,H))
        left  = ImageEnhance.Brightness(left).enhance(0.30)
        left  = ImageEnhance.Color(left).enhance(0.35)
        right = ImageEnhance.Brightness(right).enhance(0.20)
        right = ImageEnhance.Color(right).enhance(0.28)
        red_tint = Image.new("RGBA",(W//2,H),(150,0,0,110))
        left_rgba = Image.alpha_composite(left.convert("RGBA"), red_tint)
        img = Image.new("RGB",(W,H))
        img.paste(left_rgba.convert("RGB"),(0,0))
        img.paste(right,(W//2,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(W//2-5,0),(W//2+5,H)], fill=(230,0,0))
        draw.text((20,18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(220,220,220))
        words = thumb_text.split()
        lines = [" ".join(words[:len(words)//2]), " ".join(words[len(words)//2:])] if len(words)>2 else [thumb_text]
        y = H//2 - len(lines)*100//2
        for line in lines:
            b = draw.textbbox((0,0),line,font=f_xl)
            x = (W//2-(b[2]-b[0]))//2
            for s in range(6,0,-1): draw.text((x+s,y+s),line,font=f_xl,fill=(0,0,0))
            draw.text((x,y),line,font=f_xl,fill=(255,255,255))
            y += 104
        b = draw.textbbox((0,0),title_text,font=f_md)
        draw.text((W//2+(W//2-(b[2]-b[0]))//2, H//2-22),title_text,font=f_md,fill=(255,220,0))

    elif style == "3":
        # Dark vignette + red text — for unsolved/conspiracy
        img = ImageEnhance.Brightness(base_img).enhance(0.18)
        img = ImageEnhance.Color(img).enhance(0.28)
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        vignette = Image.new("RGBA",(W,H),(0,0,0,0))
        vd = ImageDraw.Draw(vignette)
        for i in range(280):
            alpha = int(i*0.78)
            vd.rectangle([(i,i),(W-i,H-i)], outline=(0,0,0,alpha))
        img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.text((20,18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(180,180,180))
        words = thumb_text.split()
        lines = ([thumb_text] if len(words)<=2 else [" ".join(words[:len(words)//2])," ".join(words[len(words)//2:])])
        y = H//2-140
        for line in lines:
            b = draw.textbbox((0,0),line,font=f_xl)
            x = (W-(b[2]-b[0]))//2
            for r in range(10,0,-3): draw.text((x,y),line,font=f_xl,fill=(180,0,0,30))
            for s in range(5,0,-1): draw.text((x+s,y+s),line,font=f_xl,fill=(0,0,0))
            draw.text((x,y),line,font=f_xl,fill=(255,50,50))
            y += 108
        draw.rectangle([(0,H-88),(W,H)], fill=(180,0,0))
        b = draw.textbbox((0,0),title_text,font=f_md)
        draw.text(((W-(b[2]-b[0]))//2, H-68),title_text,font=f_md,fill=(255,255,255))

    elif style == "4":
        # Yellow warning style — high contrast, attention-grabbing
        img = ImageEnhance.Brightness(base_img).enhance(0.22)
        img = ImageEnhance.Color(img).enhance(0.3)
        draw = ImageDraw.Draw(img)
        # Top yellow bar
        draw.rectangle([(0,0),(W,70)], fill=(230,180,0))
        draw.text((20,18), f"⚠️  {config.CHANNEL_NAME.upper()} — DARK CASE", font=f_sm, fill=(0,0,0))
        # Big white text center
        words = thumb_text.split()
        lines = ([thumb_text] if len(words)<=2 else [" ".join(words[:len(words)//2])," ".join(words[len(words)//2:])])
        y = H//2-140
        for line in lines:
            b = draw.textbbox((0,0),line,font=f_xl)
            x = (W-(b[2]-b[0]))//2
            for s in range(8,0,-1): draw.text((x+s,y+s),line,font=f_xl,fill=(0,0,0))
            draw.text((x,y),line,font=f_xl,fill=(255,255,255))
            y += 108
        draw.text(((W-draw.textbbox((0,0),title_text,font=f_lg)[2])//2, y+10), title_text, font=f_lg, fill=(230,180,0))
        draw.rectangle([(0,H-62),(W,H)], fill=(20,0,0))
        draw.text((24,H-46),"TRUE CRIME  •  UNSOLVED  •  DARK CASES", font=f_sm, fill=(155,155,155))

    else:
        # STYLE 1: Classic dark with red outline glow
        img = ImageEnhance.Brightness(base_img).enhance(0.24)
        img = ImageEnhance.Color(img).enhance(0.45)
        draw = ImageDraw.Draw(img)
        draw.text((28,18), f"🔴 {config.CHANNEL_NAME.upper()}", font=f_sm, fill=(210,210,210))
        words = thumb_text.split()
        lines = ([thumb_text] if len(words)<=2 else [" ".join(words[:len(words)//2])," ".join(words[len(words)//2:])])
        y = H//2-len(lines)*110//2-10
        for line in lines:
            b = draw.textbbox((0,0),line,font=f_xl)
            x = (W-(b[2]-b[0]))//2
            for s in range(8,0,-1): draw.text((x+s,y+s),line,font=f_xl,fill=(0,0,0))
            for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]: draw.text((x+dx,y+dy),line,font=f_xl,fill=(215,0,0))
            draw.text((x,y),line,font=f_xl,fill=(255,255,255))
            y += 112
        b = draw.textbbox((0,0),title_text,font=f_lg)
        draw.text(((W-(b[2]-b[0]))//2, y+10), title_text, font=f_lg, fill=(230,185,0))
        draw.rectangle([(0,H-62),(W,H)], fill=(12,0,0))
        draw.rectangle([(0,H-64),(W,H-62)], fill=(200,0,0))
        draw.text((28,H-48),"TRUE CRIME  •  UNSOLVED MYSTERIES  •  DARK CASES", font=f_sm, fill=(155,155,155))

    img.save(thumb, "JPEG", quality=96)
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

    yt = build("youtube","v3",credentials=creds)

    title = metadata.get("title","True Crime")[:100]
    if is_short:
        title       = f"#Shorts {title}"[:100]
        description = f"🔴 {title}\n\n{metadata.get('hashtags','')}\n\n#Shorts\n\n🔔 Subscribe → {config.CHANNEL_HANDLE}"
        tags        = metadata.get("tags_list",[]) + ["Shorts","TrueCrimeShorts","#Shorts"]
    else:
        description = metadata.get("full_description","")
        tags        = metadata.get("tags_list",[])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:500],
            "categoryId": "25",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    resp  = yt.videos().insert(part="snippet,status",body=body,media_body=media).execute()
    vid   = resp.get("id")
    print(f"✅ {kind} uploaded! ID: {vid}")

    if not is_short and thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(videoId=vid,
                media_body=MediaFileUpload(thumbnail_path,mimetype="image/jpeg")).execute()
            print("✅ Thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail: {e}")

    if not is_short:
        # Pinned comment with engagement question
        pinned     = metadata.get("pinned_comment","What do YOU think happened? 👇")
        tmpl       = random.choice(config.PINNED_COMMENT_TEMPLATES)
        pinned_msg = tmpl.format(question=pinned, handle=config.CHANNEL_HANDLE)
        try:
            yt.commentThreads().insert(
                part="snippet",
                body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{"textOriginal":pinned_msg}}}}).execute()
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
    print("🚀 ARCHIVE OF ENIGMAS — Documentary Pipeline v8 VIRAL")
    print("="*55)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

    try:
        # 1. Fetch story
        story = fetch_story()
        topic = story.get("topic","other")
        print(f"  📌 Topic: {topic}")

        # 2. Generate script (20-min target)
        script, shorts_script, metadata = generate_script(story, language="en")

        # 3. Fetch media (more assets for longer video)
        img_queries, vid_queries = extract_keywords(story)
        image_paths = fetch_images(img_queries, target=24)
        video_clips = fetch_videos(vid_queries, target=14)

        # 4. Voiceover (free Microsoft Neural)
        audio_path        = generate_voiceover(script, label="voiceover")
        shorts_audio_path = None
        if shorts_script:
            shorts_audio_path = generate_voiceover(shorts_script, label="shorts_voiceover")

        # 4b. Background music
        music_path       = fetch_background_music()
        mixed_audio_path = os.path.join(config.OUTPUT_FOLDER, "voiceover_mixed.mp3")
        audio_path       = mix_audio_with_music(audio_path, music_path, mixed_audio_path)

        # 5. Thumbnail (A/B rotating styles)
        thumbnail_path = create_thumbnail(image_paths, metadata, story)

        # 6. Assemble main video (1080p, 20min)
        video_path = assemble_documentary_video(audio_path, image_paths, video_clips, metadata, story)

        # 7. Assemble Shorts
        shorts_path = None
        if shorts_audio_path and image_paths:
            try:
                shorts_path = assemble_shorts_video(shorts_audio_path, image_paths, metadata)
            except Exception as e:
                print(f"⚠️ Shorts assembly failed: {e}")

        # 8. Upload main + short
        video_id  = upload_to_youtube(video_path, thumbnail_path, metadata, is_short=False)
        shorts_id = None
        if shorts_path:
            try:
                shorts_id = upload_to_youtube(shorts_path, None, metadata, is_short=True)
            except Exception as e:
                print(f"⚠️ Shorts upload failed: {e}")

        # 9. Update history
        keywords = [story["title"].lower().split()[0]] if story["title"] else []
        update_history(metadata["title"], topic, keywords)

        print("\n"+"="*55)
        print("🎉 SUCCESS!")
        print(f"📺 Main:  https://youtube.com/watch?v={video_id}")
        print(f"🎬 Studio: https://studio.youtube.com/video/{video_id}/edit")
        print("⏳ NOTE: YouTube takes 30min–4hrs to process 1080p.")
        print("   Check YouTube Studio → Content tab immediately.")
        if shorts_id:
            print(f"📱 Short: https://youtube.com/watch?v={shorts_id}")
        print(f"📊 Title : {metadata.get('title')}")
        print(f"🎭 Style : Thumbnail style {metadata.get('thumbnail_style','1')}")
        print(f"🎤 Voice : edge-tts ({config.TTS_VOICE})")
        print(f"📐 Res   : {config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT} @ {config.VIDEO_FPS}fps")
        print("="*55)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback; traceback.print_exc()
        raise


if __name__ == "__main__":
    run_pipeline()
