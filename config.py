# ============================================
# TRUE CRIME BOT - CONFIG
# Keys are loaded from GitHub Secrets!
# ============================================

import os

# AI Script Generation (Groq - Free!)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-8b-8192"

# Voiceover (gTTS - Completely Free!)
TTS_LANGUAGE = "en"
TTS_SLOW = False

# Pexels (Background footage)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")

# ============================================
# SETTINGS
# ============================================

OUTPUT_FOLDER = "output"
PREFER_WIKIPEDIA = False

WIKIPEDIA_CASES = [
    "Zodiac Killer",
    "Jack the Ripper",
    "DB Cooper",
    "Black Dahlia murder",
    "Golden State Killer",
    "Ted Bundy",
    "Jonbenet Ramsey",
    "Dyatlov Pass incident",
    "Tamam Shud case",
    "Sodder children disappearance",
    "Isdal Woman",
    "Springfield Three",
    "Tylenol murders",
    "Isabella Stewart Gardner Museum theft",
    "Max Headroom broadcast intrusion"
]
