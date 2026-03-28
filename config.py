# ============================================
# TRUE CRIME BOT - CONFIG
# All keys loaded from GitHub Secrets!
# ============================================

import os

# Groq AI (Script Generation - Free!)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# gTTS (Voiceover - Completely Free!)
TTS_LANGUAGE = "en"
TTS_SLOW = False

# Pexels (Background Footage - Free!)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# YouTube (Upload)
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN = os.environ.get("YOUTUBE_TOKEN", "")

# ============================================
# SETTINGS
# ============================================

OUTPUT_FOLDER = "output"
PREFER_WIKIPEDIA = False  # False = try RSS first, True = Wikipedia always

# Famous cases — bot picks one randomly each run
# Add more anytime!
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
    "Max Headroom broadcast intrusion",
    "Aileen Wuornos",
    "Lizzie Borden",
    "Boy in the box Philadelphia"
]
