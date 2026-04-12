# ============================================
# ARCHIVE OF ENIGMAS - CONFIG v5
# ============================================

import os

# ============================================
# API KEYS — set these as GitHub Secrets
# ============================================

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL       = "llama-3.3-70b-versatile"

PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")

# ElevenLabs — for human-quality voice (HIGHLY RECOMMENDED)
# Free tier: 10,000 chars/month. Starter: $5/mo for 30k chars.
# Sign up: https://elevenlabs.io
# Get API key from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

# ElevenLabs Voice ID — choose a deep, dramatic male voice
# Recommended voices (copy the ID from ElevenLabs voice library):
#   "pNInz6obpgDQGcFmaJgB"  → Adam (deep, authoritative)
#   "VR6AewLTigWG4xSOukaG"  → Arnold (strong)
#   "ErXwobaYiN019PkySvjV"  → Antoni (warm, narrative)
#   "yoZ06aMxZJJ28mfd3POQ"  → Sam (clear, documentary)
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

# YouTube OAuth
YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN          = os.environ.get("YOUTUBE_TOKEN", "")

# ============================================
# CHANNEL SETTINGS
# ============================================

OUTPUT_FOLDER    = "output"
PREFER_WIKIPEDIA = False          # Set True to skip RSS and use Wikipedia only
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
    "murder":      ["#MurderCase", "#KillerCaught", "#TrueMurder"],
    "missing":     ["#MissingPerson", "#ColdCaseMystery", "#MissingPersons"],
    "serial":      ["#SerialKiller", "#SerialKillerStories", "#TrueSerialKiller"],
    "unsolved":    ["#UnsolvedCrime", "#OpenCase", "#Unexplained"],
    "heist":       ["#TrueCrimeHeist", "#RobberyStory", "#CrimeStories"],
    "cult":        ["#CultDocumentary", "#DarkCults", "#TrueCrimeCult"],
    "coldcase":    ["#ColdCase", "#ColdCaseSolved", "#ColdCaseMystery"],
    "conspiracy":  ["#ConspiracyTheory", "#DarkSecrets", "#HiddenTruth"],
    "default":     ["#CrimePodcast", "#TrueEvents", "#RealCrime"]
}
