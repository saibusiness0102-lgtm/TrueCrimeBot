Skip to content
saibusiness0102-lgtm
TrueCrimeBot
Repository navigation
Code
Issues
Pull requests
Actions
Projects
Security and quality
Insights
Settings
Files
Go to file
t
.github
README.md
bot.py
config.py
requirements.txt
TrueCrimeBot
/
config.py
in
main

Edit

Preview
Indent mode

Spaces
Indent size

4
Line wrap mode

No wrap
Editing config.py file contents
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
 24
 25
 26
 27
 28
 29
 30
 31
 32
 33
 34
 35
 36
 37
 38
 39
 40
 41
 42
 43
 44
 45
 46
 47
 48
 49
 50
 51
 52
 53
 54
 55
 56
 57
 58
 59
 60
 61
 62
 63
 64
 65
 66
 67
 68
 69
 70
 71
# ============================================
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

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
.github/workflows content loaded
