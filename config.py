# ============================================================
# ARCHIVE OF ENIGMAS — config.py  (v11 GROWTH EDITION)
# FIXES: English-only by default, Wikipedia-first, font download,
#        better thumbnail hooks, updated music URLs
# ============================================================

import os

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL     = "llama-3.3-70b-versatile"

PEXELS_API_KEY  = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN          = os.environ.get("YOUTUBE_TOKEN", "")

TTS_VOICE  = "en-US-ChristopherNeural"
TTS_RATE   = "-5%"
TTS_VOLUME = "+0%"

VIDEO_WIDTH   = 1920
VIDEO_HEIGHT  = 1080
VIDEO_FPS     = 24
VIDEO_BITRATE = "8000k"

THUMBNAIL_WIDTH  = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_STYLES = ["1", "2", "3", "4"]

# FIX v11: Bot auto-downloads Bebas Neue (impact-style) for thumbnails
BEBAS_NEUE_URL = (
    "https://github.com/dharmatype/Bebas-Neue/raw/master/fonts/BebasNeue(2019)by_Dharma_Type/otf/BebasNeue-Regular.otf"
)
FONT_CACHE_PATH = "/tmp/BebasNeue.otf"

CHANNEL_NAME     = "Archive of Enigmas"
CHANNEL_HANDLE   = "@Archive-of-Enigmas-04"
OUTPUT_FOLDER    = "output"

# FIX v11: MUST be True — RSS pulls multilingual stories which breaks the algorithm
PREFER_WIKIPEDIA = True

WATERMARK_TEXT    = "Archive of Enigmas"
WATERMARK_OPACITY = 0.35

SHORTS_TARGET_DURATION = 58

MAX_SAME_TOPIC_IN_5 = 1

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

# FIX v11: More debate-sparking pinned comment templates
PINNED_COMMENT_TEMPLATES = [
    "🔴 DEBATE THIS: {question}\n\nComment A or B 👇 We read EVERY single one.\n\n📺 More cases → {handle}",
    "💬 HOT TAKE: {question}\n\nDrop your theory — we'll pin the best one! 🏆\n🔔 {handle}",
    "🕵️ DETECTIVE CHALLENGE: {question}\n\nShare your theory below. Best answer gets pinned! 🏆\n🔕 {handle}",
    "⚠️ CONTROVERSIAL: {question}\n\nAgree or disagree? COMMENT BELOW — this case divided millions.\n{handle}",
    "🧩 WE THINK THE POLICE GOT IT WRONG: {question}\n\nWhat do YOU think? 👇\n→ {handle}",
    "🔥 UNPOPULAR OPINION: {question}\n\nDo you agree? Drop your take — we respond to every comment.\n{handle}",
]

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
        "hashtag_suffix": " #CrimenReal #MisterioVerdadero #CasosCriminales #CrimesReales",
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
}

PRIMARY_LANGUAGE = "en"
EXTRA_LANGUAGES  = ["es", "pt", "hi", "fr"]   # use ONLY with separate channels per language

# Title formats that perform well — used in prompt examples
HIGH_PERFORMING_TITLE_FORMATS = [
    "The [City] [Crime] That Shocked the Nation",
    "How [Name] Killed [N] People and Almost Got Away With It",
    "The Disturbing Truth Behind the [Name] Case",
    "She Vanished in [Year]. No One Looked For Her.",
    "[Name]: The Serial Killer Your Town Forgot",
    "The [N]-Year-Old Cold Case Police Still Can't Solve",
    "He Confessed to [N] Murders. They Only Charged Him With One.",
    "What Really Happened to [Name]?",
    "The [Profession] Who Led a Double Life as a [Crime]",
    "Inside the [N]-Day Manhunt That Captivated a Nation",
]
