# instatools

An Instagram tool that runs on your own computer. It does three jobs:

1. **Analyse any link (the main feature):** paste an Instagram post or Reel link. It opens the post, downloads it, reads the caption, the on-screen text in every frame, what's said (speech-to-text) and the comments. It then tells you which tools or GitHub projects are being shown, with links, the steps to try them, and whether the post is hype.
2. **Autopost:** drop photos or videos into a folder and it posts them, as a feed post, Reel, carousel or **Story**. Before posting, it looks at each photo, decides how to edit it, and fixes it (light, colour, crop). It can also check how your community posts that kind of moment, to borrow caption style and song ideas.
3. **Pull:** downloads posts, captions, stats, videos and audio from your profile or any public profile.

You can use it from the **command line**, from **chat with Claude** (Claude Code / desktop app, via the included skill), or **hands-off** with the drop folder.

> **Risk:** it drives a real browser through instagram.com while logged in as you. That goes against Instagram's Terms of Use, and Instagram can block actions or ask you to verify your account. The tool waits 10 minutes between posts, moves at human speed, and **stops completely** on any captcha, checkpoint or "action blocked" (it writes `data/STOPPED.txt` and doesn't retry).

## Setup (once)

You need Python 3.10+ and ffmpeg (`winget install ffmpeg` / `brew install ffmpeg` / `apt install ffmpeg`).

```bash
git clone https://github.com/Tragettechragul/instatools
cd instatools
pip install -e ".[transcribe]"     # transcribe = speech-to-text, needed to read what's said in Reels
playwright install chromium
instatools login                   # a browser opens: log in to Instagram yourself, then press Enter
```

Set your Anthropic API key. It's needed for analysis, photo editing and captions:

```bash
export ANTHROPIC_API_KEY=sk-ant-...          # Windows: setx ANTHROPIC_API_KEY sk-ant-...
export GITHUB_TOKEN=ghp_...                  # optional: more GitHub searches per minute
```

### Use it from chat with Claude
```
/plugin marketplace add Tragettechragul/instatools
/plugin install instatools@instatools
```
Then paste any Instagram link into Claude Code and ask "what's this?". Claude runs the analysis and answers in chat.

## 1. Analyse a link

```bash
instatools analyze https://www.instagram.com/reel/XXXXXXXX/
```

It prints a report and saves it to `data/library/<account>/<post-id>/`. The report covers:
- a summary and the type of post (tool showcase, tutorial, news…)
- **each tool**: what it does, any GitHub repo stated in the post, and the top GitHub search matches (with stars)
- every GitHub link seen in the caption, speech, on-screen text or comments
- steps to reproduce it, and any commands or code shown on screen
- a beat-by-beat timeline, every piece of on-screen text, and the hook and call to action
- claims that need checking, and an honest "is this useful?"

The folder also keeps the video, the audio (`.m4a`), the timestamped transcript, the caption and the raw `analysis.json`.

## 2. Autopost from a folder

```bash
instatools watch            # leave it running; checks the inbox every 30 s, posts at most once per 10 min
```

Drop files into `data/inbox/`. Add a note file with the **same name** (`photo.jpg` → `photo.txt`), or `caption.txt` inside a folder:

```
type: story            # story or post (default post)
community: tamil       # optional: research how this community posts this kind of moment
brief: my sister's wedding, family photos, keep it warm
edit: auto             # auto (default) or off

(optional) anything below the header lines is used as the exact caption
```

| You drop | What happens |
|---|---|
| `photo.jpg` | Claude works out what's in the photo, edits it for a 4:5 feed post, writes the caption and alt text, and posts it |
| `photo.jpg` + note `type: story` | The photo is edited to 9:16 and posted as a **Story** |
| `clip.mp4` | Posted as a Reel |
| A folder of 2–10 files | Posted as a carousel, in file-name order |
| Note with `community: tamil` | It first reads popular posts under related hashtags (e.g. `#tamilwedding`), then uses their caption style, editing style and **songs** |

After each post:
- The files move to `data/posted/`, with `result.json` holding the post link, the caption, the edits made and any suggested songs.
- The edited copies are in `data/work/`. Your originals are never changed.
- Errors move to `data/failed/`. A block or captcha writes `data/STOPPED.txt` and stops the tool. Delete that file once you've sorted it out in the app.

Settings: `INSTATOOLS_MIN_GAP_MINUTES=10`, `INSTATOOLS_HEADLESS=1` (no window), `instatools watch --once` (for cron / Task Scheduler).

## 3. Other commands

| Command | What it does |
|---|---|
| `instatools pull [user] [--limit N] [--transcribe]` | Download posts: media, audio, caption, likes, comments, views, audio name |
| `instatools get URL [--transcribe]` | Download one post or Reel |
| `instatools edit photo.jpg [--story] [--brief "..."]` | Make an edited copy of a photo, without posting it |
| `instatools research wedding --community tamil` | See how a community posts that occasion: captions, songs, hashtags |
| `instatools post FILES... [--caption "..."]` | Post now |
| `instatools whoami` | Check which account is logged in |

## What it can't do (honestly)

| Want | Reality |
|---|---|
| Add music to a post or Story | instagram.com has no music picker. The tool **suggests** songs (taken from the community research) in `result.json`; add them in the app. |
| Video Stories | Only photo Stories. Video Stories need the app. |
| Story posting reliability | Uses Instagram's mobile web layout, which changes often. It's the least stable part of the tool. |
| Read private accounts | Only posts your logged-in account can see. |
| Insights / demographics | Not included yet. |
| Layout changes | Buttons are found by their labels. If Instagram renames them, the post fails safely into `data/failed/` and the code needs a small update. |
| Speech in a Reel | Needs the `transcribe` extra (runs locally). The first run downloads a speech model (~500 MB). |

`data/browser-profile/` is your logged-in session. **Treat it like a password and never share it.** It's git-ignored.

## Tests

```bash
pip install pytest && pytest -q
```
The offline tests cover post parsing, inbox and note handling, photo editing, frame and audio extraction, the report format and hard-stop detection.
