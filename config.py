# ============================================================
# ARCHIVE OF ENIGMAS — config.py  (v10 MONETIZATION EDITION)
# Top-5 language strategy for fastest path to YouTube monetisation
# ============================================================

import os

# ============================================================
# API KEYS  (set as GitHub Secrets / env vars — never hardcode)
# ============================================================

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL     = "llama-3.3-70b-versatile"

PEXELS_API_KEY  = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

# YouTube OAuth (JSON string stored as GitHub Secret)
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN          = os.environ.get("YOUTUBE_TOKEN", "")


# ============================================================
# VOICE — edge-tts (FREE Microsoft Neural, no API key needed)
# ============================================================

TTS_VOICE  = "en-US-ChristopherNeural"
TTS_RATE   = "-5%"
TTS_VOLUME = "+0%"


# ============================================================
# VIDEO QUALITY — 1080p / 24fps cinematic
# ============================================================

VIDEO_WIDTH   = 1920
VIDEO_HEIGHT  = 1080
VIDEO_FPS     = 24
VIDEO_BITRATE = "8000k"


# ============================================================
# THUMBNAIL SETTINGS
# ============================================================

THUMBNAIL_WIDTH  = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_STYLES = ["1", "2", "3", "4"]


# ============================================================
# CHANNEL BRANDING
# ============================================================

CHANNEL_NAME     = "Archive of Enigmas"
CHANNEL_HANDLE   = "@Archive-of-Enigmas-04"
OUTPUT_FOLDER    = "output"
PREFER_WIKIPEDIA = False

WATERMARK_TEXT    = "Archive of Enigmas"
WATERMARK_OPACITY = 0.35


# ============================================================
# SHORTS SETTINGS
# ============================================================

SHORTS_TARGET_DURATION = 58   # Keep under 60s for YouTube Shorts boost


# ============================================================
# DIVERSITY GUARD
# ============================================================

MAX_SAME_TOPIC_IN_5 = 1


# ============================================================
# HASHTAGS  — Peak SEO, Viral-Optimised
# ============================================================

BASE_HASHTAGS = [
    "#TrueCrime", "#UnsolvedMysteries", "#TrueCrimeStories",
    "#CriminalMinds", "#MurderMystery", "#TrueCrimeCommunity",
    "#ColdCase", "#DarkCases", "#TrueCrimeJunkie",
    "#ArchiveOfEnigmas", "#UnsolvedCase", "#MysteryStories",
    "#CrimeDocumentary", "#DarkSecrets", "#TrueCrimePodcast",
    "#Documentary", "#MysteryDoc", "#RealCrime",
    "#CrimeStorytime", "#Enigma", "#DarkHistory",
]

NICHE_HASHTAGS = {
    "murder":     ["#MurderCase", "#KillerCaught", "#TrueMurder",
                   "#HomicideCase", "#MurderInvestigation"],
    "missing":    ["#MissingPerson", "#ColdCaseMystery", "#MissingPersons",
                   "#DisappearedWithoutTrace", "#SearchAndRescue"],
    "serial":     ["#SerialKiller", "#SerialKillerStories", "#TrueSerialKiller",
                   "#SerialKillerDocumentary", "#MultipleVictims"],
    "unsolved":   ["#UnsolvedCrime", "#OpenCase", "#Unexplained",
                   "#UnsolvedKillings", "#JusticeNeeded"],
    "heist":      ["#TrueCrimeHeist", "#RobberyStory", "#CrimeStories",
                   "#BankHeist", "#CriminalMastermind"],
    "cult":       ["#CultDocumentary", "#DarkCults", "#TrueCrimeCult",
                   "#CultLeader", "#CultSurvivor"],
    "coldcase":   ["#ColdCase", "#ColdCaseSolved", "#ColdCaseMystery",
                   "#DecadeOldMystery", "#ColdCaseFiles"],
    "conspiracy": ["#ConspiracyTheory", "#DarkSecrets", "#HiddenTruth",
                   "#CoverUp", "#GovernmentSecret"],
    "default":    ["#CrimePodcast", "#TrueEvents", "#RealCrime",
                   "#CrimeFiles", "#DarkTruths"],
}

TRENDING_HASHTAGS = [
    "#NewTrueCrime", "#ViralMystery", "#MustWatch",
    "#CrimeAlert", "#JusticeForVictims", "#ShockingCase",
]


# ============================================================
# PINNED COMMENT TEMPLATES
# ============================================================

PINNED_COMMENT_TEMPLATES = [
    "🔴 QUESTION FOR YOU: {question}\n\nDrop your theory below 👇 We read EVERY comment!\n\nFollow us → {handle}",
    "💬 COMMUNITY POLL: {question}\n\nComment A or B — let's see what you think!\n📺 More cases → {handle}",
    "🕵️ DETECTIVE CHALLENGE: {question}\n\nShare your theory in the comments. Best answer gets pinned! 🏆\n🔔 {handle}",
    "⚠️ VIEWER DEBATE: {question}\n\nAgree or disagree? COMMENT BELOW — this case divided millions.\n{handle}",
    "🧩 UNSOLVED ANGLE: {question}\n\nWe think the truth is darker. What about you? 👇\nSubscribe for more → {handle}",
]


# ============================================================
# TOP-5 LANGUAGE STRATEGY FOR MONETISATION
# ============================================================
# Priority order is based on YouTube audience size and CPM rates:
#   1. English (en)  — highest CPM, global reach ✅ already running
#   2. Spanish (es)  — 500M+ speakers, #2 YouTube language globally
#   3. Portuguese (pt) — Brazil is TOP-3 YouTube market worldwide
#   4. Hindi (hi)    — 1.4B market, fastest-growing YouTube audience
#   5. French (fr)   — France + 29 Francophone countries, high CPM
#
# German and Japanese are smaller audiences and take longer to monetise.
# Removed from priority list. Re-add once monetised in top-5.
# ============================================================

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "voice": "en-US-ChristopherNeural",
        "rate": "-5%",
        "audience": "US, UK, CA, AU, IN",
        "subscribers_target": "Global English",
        "hashtag_suffix": "",
    },
    "es": {
        "name": "Spanish",
        "voice": "es-ES-AlvaroNeural",
        "rate": "-3%",
        "audience": "ES, MX, AR, CO, CL",
        "subscribers_target": "Latin America + Spain",
        "hashtag_suffix": " #CrimenReal #MisterioVerdadero #CasosCriminales #CrimenesReales",
    },
    "pt": {
        "name": "Portuguese",
        "voice": "pt-BR-AntonioNeural",
        "rate": "-3%",
        "audience": "BR, PT",
        "subscribers_target": "Brazil + Portugal",
        "hashtag_suffix": " #CrimeVerdadeiro #MisteriosBrasil #CasoCriminal #CrimesReais",
    },
    "hi": {
        "name": "Hindi",
        "voice": "hi-IN-MadhurNeural",
        "rate": "-3%",
        "audience": "IN",
        "subscribers_target": "India (1.4B market)",
        "hashtag_suffix": " #HindiCrime #SachchiGhatna #RahasyaKes #ApradhKaach",
    },
    "fr": {
        "name": "French",
        "voice": "fr-FR-HenriNeural",
        "rate": "-4%",
        "audience": "FR, BE, CH, CA-QC, AF",
        "subscribers_target": "France + Francophone",
        "hashtag_suffix": " #CrimeVrai #Mystere #AffaireCriminelle #CrimesReels",
    },
    # Keep but deprioritised — add separate workflows later once monetised
    "de": {
        "name": "German",
        "voice": "de-DE-ConradNeural",
        "rate": "-4%",
        "audience": "DE, AT, CH",
        "subscribers_target": "DACH Region",
        "hashtag_suffix": " #EchteKrimis #UngeloesterFall #Kriminalfall",
    },
    "ja": {
        "name": "Japanese",
        "voice": "ja-JP-KeitaNeural",
        "rate": "-5%",
        "audience": "JP",
        "subscribers_target": "Japan",
        "hashtag_suffix": " #TrueCrimeJapan #MysteryJapan #CriminalCase",
    },
}

# Primary language — always uploaded by the main workflow
PRIMARY_LANGUAGE = "en"

# Languages with dedicated workflows (each runs in its own GitHub Actions job)
# Managed via BOT_LANGUAGE env var in each workflow file
EXTRA_LANGUAGES = ["es", "pt", "hi", "fr"]   # for documentation/reference only
