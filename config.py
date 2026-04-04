# ============================================
# ARCHIVE OF ENIGMAS - CONFIG
# ============================================

import os

# Groq AI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# gTTS
TTS_LANGUAGE = "en"
TTS_SLOW = False

# Pexels
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN = os.environ.get("YOUTUBE_TOKEN", "")

# ============================================
# SETTINGS
# ============================================

OUTPUT_FOLDER = "output"
PREFER_WIKIPEDIA = False
CHANNEL_NAME = "Archive of Enigmas"
CHANNEL_HANDLE = "@Archive-of-Enigmas-04"

# ============================================
# VIRAL HASHTAGS
# ============================================

BASE_HASHTAGS = [
    "#TrueCrime", "#UnsolvedMysteries", "#DarkCases",
    "#CriminalMinds", "#MysteryStories", "#TrueCrimeStories",
    "#ColdCase", "#MurderMystery", "#ArchiveOfEnigmas",
    "#TrueCrimeCommunity", "#UnsolvedCase", "#CrimeStorytime",
    "#MysteryDocumentary", "#DarkSecrets", "#TrueCrimeJunkie"
]

NICHE_HASHTAGS = {
    "murder":   ["#MurderCase", "#KillerCaught", "#TrueMurder"],
    "missing":  ["#MissingPerson", "#ColdCaseMystery", "#MissingPersons"],
    "serial":   ["#SerialKiller", "#SerialKillerStories", "#TrueSerialKiller"],
    "unsolved": ["#UnsolvedCrime", "#OpenCase", "#Unexplained"],
    "default":  ["#CrimePodcast", "#TrueEvents", "#RealCrime"]
}

# ============================================
# WIKIPEDIA CASES
# ============================================

WIKIPEDIA_CASES = [
    "Zodiac Killer", "Jack the Ripper", "DB Cooper",
    "Black Dahlia murder", "Tamam Shud case",
    "Dyatlov Pass incident", "Isdal Woman",
    "Boy in the box Philadelphia", "Golden State Killer",
    "Ted Bundy", "Jeffrey Dahmer", "John Wayne Gacy",
    "Aileen Wuornos", "BTK killer", "Lizzie Borden",
    "Jonbenet Ramsey", "Tylenol murders",
    "Sodder children disappearance", "Springfield Three",
    "Villisca axe murders", "Axeman of New Orleans",
    "Cleveland torso murderer", "Wonderland murders",
    "Isabella Stewart Gardner Museum theft",
    "Max Headroom broadcast intrusion"
]
