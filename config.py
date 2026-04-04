# ============================================
# ARCHIVE OF ENIGMAS - CONFIG
# Viral Optimized Version
# ============================================

import os

# Groq AI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# gTTS Voiceover
TTS_LANGUAGE = "en"
TTS_SLOW = False

# Pexels
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN = os.environ.get("YOUTUBE_TOKEN", "")

# ============================================
# VIRAL SETTINGS
# ============================================

OUTPUT_FOLDER = "output"
PREFER_WIKIPEDIA = False

# Target video length — 15 mins for YouTube algorithm boost
TARGET_WORDS = 2200  # ~15 mins of narration at avg speaking pace

# Channel branding
CHANNEL_NAME = "Archive of Enigmas"
CHANNEL_HANDLE = "@Archive-of-Enigmas-04"

# Upload timing — 6PM IST = 12:30 UTC (peak Indian + US overlap)
# Cron handles this in workflow

# ============================================
# VIRAL HASHTAGS POOL
# ============================================

BASE_HASHTAGS = [
    "#TrueCrime", "#UnsolvedMysteries", "#DarkCases",
    "#CriminalMinds", "#MysteryStories", "#TrueCrimeStories",
    "#ColdCase", "#MurderMystery", "#ArchiveOfEnigmas",
    "#TrueCrimeCommunity", "#UnsolvedCase", "#CrimeStorytime",
    "#MysteryDocumentary", "#DarkSecrets", "#TrueCrimeJunkie"
]

NICHE_HASHTAGS = {
    "murder": ["#MurderCase", "#KillerCaught", "#TrueMurder"],
    "missing": ["#MissingPerson", "#ColdCaseMystery", "#MissingPersons"],
    "serial": ["#SerialKiller", "#SerialKillerStories", "#TrueSerialKiller"],
    "unsolved": ["#UnsolvedCrime", "#OpenCase", "#Unexplained"],
    "default": ["#CrimePodcast", "#TrueEvents", "#RealCrime"]
}

# ============================================
# WIKIPEDIA CASES — EXPANDED HIGH-INTEREST LIST
# ============================================

WIKIPEDIA_CASES = [
    # Iconic unsolved
    "Zodiac Killer",
    "Jack the Ripper",
    "DB Cooper",
    "Black Dahlia murder",
    "Tamam Shud case",
    "Dyatlov Pass incident",
    "Isdal Woman",
    "Boy in the box Philadelphia",
    "Max Headroom broadcast intrusion",
    "Sodder children disappearance",
    # Famous killers
    "Golden State Killer",
    "Ted Bundy",
    "Jeffrey Dahmer",
    "John Wayne Gacy",
    "Aileen Wuornos",
    "BTK killer",
    "Lizzie Borden",
    # Famous cases
    "Jonbenet Ramsey",
    "Tylenol murders",
    "Isabella Stewart Gardner Museum theft",
    "Springfield Three",
    "Wonderland murders",
    "Villisca axe murders",
    "Cleveland torso murderer",
    "Axeman of New Orleans"
]
