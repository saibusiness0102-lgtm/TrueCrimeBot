# ============================================================
# ARCHIVE OF ENIGMAS — config.py  (v11 GROWTH EDITION)
# FIXES: English-only by default, Wikipedia-first, font download,
#        better thumbnail hooks, updated music URLs
# ============================================================

import os

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
# v13: Use two models strategically
# - 8b-instant for chapters (high rate limit: 131k tokens/min, 6 parallel calls safe)
# - 70b-versatile for metadata only (better quality for titles/descriptions)
GROQ_MODEL         = "llama-3.3-70b-versatile"   # metadata, translation
GROQ_MODEL_FAST    = "llama-3.1-8b-instant"       # chapter generation (131k TPM limit)

PEXELS_API_KEY  = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

YOUTUBE_CLIENT_SECRETS = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_TOKEN          = os.environ.get("YOUTUBE_TOKEN", "")

TTS_VOICE  = "en-US-ChristopherNeural"
TTS_RATE   = "-5%"
TTS_VOLUME = "+0%"

# v16: 720p — YouTube still shows as HD, ffmpeg render drops from 35→18 min
VIDEO_WIDTH   = 1280
VIDEO_HEIGHT  = 720
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


# ============================================================
# GLOBAL SEO EXPANSION (v14)
# ============================================================

# High search-volume keywords per topic — injected into description
# These are the exact phrases people type into YouTube search globally
TOPIC_SEO_KEYWORDS = {
    "serial": [
        "serial killer documentary", "serial killer true story", "real serial killer",
        "serial killer caught", "serial killer crimes", "most dangerous serial killers",
        "serial killer confession", "serial killer investigation",
    ],
    "murder": [
        "murder mystery documentary", "real murder case", "unsolved murder",
        "murder investigation", "true murder story", "homicide documentary",
        "cold case murder", "murder trial",
    ],
    "missing": [
        "missing person case", "disappearance mystery", "missing without a trace",
        "unsolved disappearance", "missing person found", "cold case missing person",
        "kidnapping true story", "abduction documentary",
    ],
    "heist": [
        "biggest heist in history", "true crime heist", "bank robbery documentary",
        "real life heist", "greatest robbery ever", "heist gone wrong",
    ],
    "cult": [
        "cult documentary", "cult leader exposed", "cult survivor story",
        "dangerous cults", "cult crimes", "cult manipulation",
    ],
    "unsolved": [
        "unsolved mystery", "cold case documentary", "unsolved true crime",
        "unexplained disappearance", "mystery never solved", "cold case solved 2024",
    ],
    "fraud": [
        "financial fraud documentary", "biggest scam ever", "ponzi scheme documentary",
        "con artist true story", "white collar crime", "billion dollar fraud",
    ],
    "conspiracy": [
        "conspiracy documentary", "cover up exposed", "government conspiracy true crime",
        "dark secrets exposed", "conspiracy theory documentary",
    ],
    "coldcase": [
        "cold case solved", "cold case documentary 2024", "decades old mystery solved",
        "cold case investigation", "cold case files documentary",
    ],
    "default": [
        "true crime documentary 2024", "real crime story", "shocking true crime",
        "documentary true crime", "best true crime cases",
    ],
}

# Global audience search terms — added to EVERY video description regardless of topic
GLOBAL_SEO_TERMS = [
    "true crime 2024", "true crime documentary", "real crime cases",
    "unsolved mysteries documentary", "crime documentary", "shocking crimes",
    "criminal investigation", "dark history documentary", "mysterious deaths",
    "real life crime story",
]

# Language-specific high-volume search keywords added to non-EN descriptions
LANGUAGE_SEO_KEYWORDS = {
    "hi": [
        "सच्ची घटना", "हिंदी क्राइम", "अपराध की कहानी", "रहस्यमय मामला",
        "सीरियल किलर हिंदी", "भारत का सबसे बड़ा अपराध", "Crime Hindi",
        "crime story hindi", "true crime hindi documentary", "hindi crime documentary 2024",
    ],
    "es": [
        "crimen real", "caso criminal", "documental crimen", "misterio sin resolver",
        "casos criminales reales", "asesino en serie documental", "crimen verdadero 2024",
        "investigacion criminal", "caso misterioso", "documental true crime español",
    ],
    "pt": [
        "crime verdadeiro", "caso criminal real", "documentario crime",
        "misterio nao resolvido", "serial killer brasil", "crime brasil documentario",
        "caso criminal brasileiro", "investigacao criminal", "true crime portugues 2024",
    ],
    "fr": [
        "crime vrai", "affaire criminelle", "documentaire crime",
        "mystere non resolu", "tueur en serie documentaire", "affaire criminelle reelle",
        "enquete criminelle", "true crime francais 2024", "affaire policiere",
    ],
    "en": [],  # English already has the base GLOBAL_SEO_TERMS
}

# Cards / End screen text injected into description
END_SCREEN_CTA = {
    "en": "🔴 WATCH NEXT → Our most-viewed cases are on screen right now\n📋 PLAYLIST → All True Crime Cases: [link your playlist here]",
    "hi": "🔴 अगला देखें → हमारे सबसे ज़्यादा देखे गए मामले अभी स्क्रीन पर हैं",
    "es": "🔴 VER DESPUÉS → Nuestros casos más vistos están en pantalla ahora",
    "pt": "🔴 ASSISTIR A SEGUIR → Nossos casos mais vistos estão na tela agora",
    "fr": "🔴 REGARDER ENSUITE → Nos cas les plus vus sont à l'écran maintenant",
}

# First-comment SEO boost — posted as a comment with timestamps
# YouTube indexes comment text for search, this boosts discoverability
FIRST_COMMENT_TEMPLATE = (
    "⏱️ JUMP TO:\n"
    "{chapters}\n\n"
    "💬 What do YOU think? Drop your theory below 👇\n"
    "🔔 Subscribe for daily true crime → {handle}"
)
