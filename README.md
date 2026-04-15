# Archive of Enigmas — Bot v6 (100% FREE)

## Total monthly cost: ₹0

| Service | What it does | Cost |
|---------|-------------|------|
| edge-tts | Microsoft Neural voice (Christopher/Ryan) | Free |
| Groq | AI script writer (Llama 3.3 70B) | Free |
| Pexels | Stock images + videos | Free |
| Pixabay | Backup stock videos | Free |
| YouTube API | Upload to your channel | Free |
| GitHub Actions | Run 2x daily automatically | Free |

## Voice quality
edge-tts uses Microsoft's actual neural TTS (same tech inside Edge browser).
`en-US-ChristopherNeural` sounds deep and authoritative — ideal for true crime.
Change `TTS_VOICE` in config.py to try different voices.

## GitHub Secrets needed (Settings → Secrets → Actions)
| Secret | Where to get |
|--------|-------------|
| `GROQ_API_KEY` | https://console.groq.com (free) |
| `PEXELS_API_KEY` | https://www.pexels.com/api (free) |
| `PIXABAY_API_KEY` | https://pixabay.com/api/docs (free, 1 min signup) |
| `YOUTUBE_CLIENT_SECRETS` | Google Cloud Console → OAuth credentials |
| `YOUTUBE_TOKEN` | Run get_token.py once on your PC |

## Setup steps
1. Get all API keys above (all free)
2. Run `python get_token.py` on your PC → paste token.json content as YOUTUBE_TOKEN
3. Push this folder to a private GitHub repo
4. Add all 5 secrets to GitHub
5. Go to Actions tab → Run workflow manually to test
6. Bot then auto-runs every day at 6 PM and 9 AM IST

## Changing voice
Edit `TTS_VOICE` in config.py:
- `en-US-ChristopherNeural` — deep, authoritative (default)
- `en-GB-RyanNeural` — British, very cinematic
- `en-IE-ConnorNeural` — Irish accent, distinctive
- `en-US-GuyNeural` — clear American

---

## v10 Changes (Multi-Language Fix)

### Bugs Fixed
1. **Multi-language pipeline was completely missing** — `run_pipeline()` never called translation. Fixed: reads `BOT_LANGUAGE` env var, translates script + ALL metadata (title, description, pinned comment) before voiceover generation.
2. **Repeated thumbnails** — `_best_bg_image()` always picked the same image by brightness score. Fixed: story-title seeded randomisation picks from top-3 candidates, guaranteeing every story gets a different thumbnail.
3. **Non-crime content in feed** — Tamil Nadu election polls and similar non-crime RSS articles were slipping through. Fixed: `is_crime_story()` filter requires at least one crime keyword before accepting an RSS story.
4. **Wrong language in YouTube upload** — `defaultLanguage` and `defaultAudioLanguage` were hardcoded to `"en"`. Fixed: pass actual `lang` variable.
5. **Workflow patch was a no-op** — the old workflow patched `config.EXTRA_LANGUAGES` in a separate subprocess that immediately exited. Fixed: each language has its own workflow file that passes `BOT_LANGUAGE` as an env var.

### New Files
- `.github/workflows/daily_upload_en.yml` — English, 6AM + 6PM IST
- `.github/workflows/daily_upload_es.yml` — Spanish, 8AM + 8PM IST  
- `.github/workflows/daily_upload_pt.yml` — Portuguese, 10PM + 1PM IST
- `.github/workflows/daily_upload_hi.yml` — Hindi, 6AM + 3PM IST
- `.github/workflows/daily_upload_fr.yml` — French, 8AM + 5PM IST

### Upload Schedule (staggered, 10 uploads/day total)
Each language runs 2x/day, staggered by 2 hours so GitHub runners never queue.
