# ============================================================
# ARCHIVE OF ENIGMAS — config.py  (v9 VIRAL EDITION)
# Fixed + Fully Optimized for Growth, SEO & Global Reach
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
# Deep, authoritative voices for true crime atmosphere:
#   en-US-ChristopherNeural  — deep, authoritative  ✅ primary
#   en-GB-RyanNeural         — British, cinematic
#   en-US-GuyNeural          — clear American narrator
#   en-US-EricNeural         — warm, gripping
#   en-IE-ConnorNeural       — Irish accent, distinctive

TTS_VOICE  = "en-US-ChristopherNeural"
TTS_RATE   = "-5%"    # Slightly slower = more dramatic
TTS_VOLUME = "+0%"


# ============================================================
# VIDEO QUALITY — 1080p / 24fps cinematic
# ============================================================

VIDEO_WIDTH   = 1920
VIDEO_HEIGHT  = 1080
VIDEO_FPS     = 24           # Cinematic feel (vs 30 which looks "TV")
VIDEO_BITRATE = "8000k"      # High quality 1080p stream


# ============================================================
# THUMBNAIL SETTINGS
# ============================================================

THUMBNAIL_WIDTH  = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_STYLES = ["1", "2", "3", "4"]   # Rotating A/B test styles


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

MAX_SAME_TOPIC_IN_5 = 1   # Max times same topic type can appear in last 5 videos


# ============================================================
# HASHTAGS  — Peak SEO, Viral-Optimised
# ============================================================

BASE_HASHTAGS = [
    # Core true crime (highest search volume)
    "#TrueCrime", "#UnsolvedMysteries", "#TrueCrimeStories",
    "#CriminalMinds", "#MurderMystery", "#TrueCrimeCommunity",
    "#ColdCase", "#DarkCases", "#TrueCrimeJunkie",
    "#ArchiveOfEnigmas", "#UnsolvedCase", "#MysteryStories",
    "#CrimeDocumentary", "#DarkSecrets", "#TrueCrimePodcast",
    # Algorithm-boost trending tags
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

# Trending/seasonal hashtags — update monthly for algorithm freshness
TRENDING_HASHTAGS = [
    "#NewTrueCrime", "#ViralMystery", "#MustWatch",
    "#CrimeAlert", "#JusticeForVictims", "#ShockingCase",
]


# ============================================================
# PINNED COMMENT TEMPLATES — Engagement Maximisers
# ============================================================

PINNED_COMMENT_TEMPLATES = [
    "🔴 QUESTION FOR YOU: {question}\n\nDrop your theory below 👇 We read EVERY comment!\n\nFollow us → {handle}",
    "💬 COMMUNITY POLL: {question}\n\nComment A or B — let's see what you think!\n📺 More cases → {handle}",
    "🕵️ DETECTIVE CHALLENGE: {question}\n\nShare your theory in the comments. Best answer gets pinned! 🏆\n🔔 {handle}",
    "⚠️ VIEWER DEBATE: {question}\n\nAgree or disagree? COMMENT BELOW — this case divided millions.\n{handle}",
    "🧩 UNSOLVED ANGLE: {question}\n\nWe think the truth is darker. What about you? 👇\nSubscribe for more → {handle}",
]


# ============================================================
# 7-LANGUAGE GLOBAL SUPPORT
# ============================================================
# Global true crime audience — each language unlocks a new
# algorithm territory. YouTube ranks localized content separately.
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
        "hashtag_suffix": " #CrimenReal #MisterioVerdadero #CasosCriminales",
    },
    "pt": {
        "name": "Portuguese",
        "voice": "pt-BR-AntonioNeural",
        "rate": "-3%",
        "audience": "BR, PT",
        "subscribers_target": "Brazil + Portugal",
        "hashtag_suffix": " #CrimeVerdadeiro #MisteriosBrasil #CasoCriminal",
    },
    "fr": {
        "name": "French",
        "voice": "fr-FR-HenriNeural",
        "rate": "-4%",
        "audience": "FR, BE, CH, CA-QC, AF",
        "subscribers_target": "France + Francophone",
        "hashtag_suffix": " #CrimeVrai #Mystere #AffaireCriminelle",
    },
    "de": {
        "name": "German",
        "voice": "de-DE-ConradNeural",
        "rate": "-4%",
        "audience": "DE, AT, CH",
        "subscribers_target": "DACH Region",
        "hashtag_suffix": " #EchteKrimis #UngeloesterFall #Kriminalfall",
    },
    "hi": {
        "name": "Hindi",
        "voice": "hi-IN-MadhurNeural",
        "rate": "-3%",
        "audience": "IN",
        "subscribers_target": "India (1.4B market)",
        "hashtag_suffix": " #HindiCrime #SachchiGhatna #RahasyaKes",
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

# Primary upload language (always English first)
PRIMARY_LANGUAGE = "en"
# Optional: produce multi-language versions (set to [] to disable)
EXTRA_LANGUAGES  = [es,hi,ja,de,fr,pt]   # e.g. ["es", "hi"] — each produces a separate upload
