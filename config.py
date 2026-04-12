# ============================================
# ARCHIVE OF ENIGMAS - CONFIG v6
# 100% FREE — No paid services
# ============================================

import os

# ============================================
# API KEYS — set as GitHub Secrets
# ============================================

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL     = "llama-3.3-70b-versatile"

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Pixabay — FREE backup video source
# Sign up free: https://pixabay.com/api/docs/
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

# YouTube OAuth
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN          = os.environ.get("YOUTUBE_TOKEN", "")

# ============================================
# VOICE — edge-tts (FREE Microsoft Neural, no key)
# ============================================
# Best voices for true crime:
#   en-US-ChristopherNeural  — deep, authoritative  ✅ recommended
#   en-GB-RyanNeural         — British, cinematic
#   en-US-GuyNeural          — clear American narrator
#   en-US-EricNeural         — warm, gripping
#   en-IE-ConnorNeural       — Irish accent, distinctive

TTS_VOICE  = "en-US-ChristopherNeural"
TTS_RATE   = "-5%"    # Slightly slower = more dramatic
TTS_VOLUME = "+0%"

# ============================================
# CHANNEL SETTINGS
# ============================================

OUTPUT_FOLDER    = "output"
PREFER_WIKIPEDIA = False
CHANNEL_NAME     = "Archive of Enigmas"
CHANNEL_HANDLE   = "@Archive-of-Enigmas-04"

# ============================================
# HASHTAGS
# ============================================

BASE_HASHTAGS = [
    "#TrueCrime", "#UnsolvedMysteries", "#DarkCases",
    "#CriminalMinds", "#MysteryStories", "#TrueCrimeStories",
    "#ColdCase", "#MurderMystery", "#ArchiveOfEnigmas",
    "#TrueCrimeCommunity", "#UnsolvedCase", "#CrimeStorytime",
    "#MysteryDocumentary", "#DarkSecrets", "#TrueCrimeJunkie"
]

NICHE_HASHTAGS = {
    "murder":     ["#MurderCase", "#KillerCaught", "#TrueMurder"],
    "missing":    ["#MissingPerson", "#ColdCaseMystery", "#MissingPersons"],
    "serial":     ["#SerialKiller", "#SerialKillerStories", "#TrueSerialKiller"],
    "unsolved":   ["#UnsolvedCrime", "#OpenCase", "#Unexplained"],
    "heist":      ["#TrueCrimeHeist", "#RobberyStory", "#CrimeStories"],
    "cult":       ["#CultDocumentary", "#DarkCults", "#TrueCrimeCult"],
    "coldcase":   ["#ColdCase", "#ColdCaseSolved", "#ColdCaseMystery"],
    "conspiracy": ["#ConspiracyTheory", "#DarkSecrets", "#HiddenTruth"],
    "default":    ["#CrimePodcast", "#TrueEvents", "#RealCrime"]
}
