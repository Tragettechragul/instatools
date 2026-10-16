# instatools

Runs your Instagram account from a folder. You drop a video or image into `data/inbox/`, and it gets posted automatically. It can also download posts, captions, stats, videos and audio from your profile or any public profile.

It drives a real Chromium browser through the normal instagram.com website, logged in as you. You log in by hand once. The tool never sees or stores your password.

> **Risk:** automating a browser goes against Instagram's Terms of Use. Instagram can respond with "action blocked", login checkpoints, or in the worst case a ban. The tool posts slowly, at most one post per 10 minutes by default, and **stops completely** the moment Instagram shows a captcha, a challenge or a block. Use it on an account you're prepared to take that risk with.

## Setup (once)

You need Python 3.10+ and ffmpeg (`winget install ffmpeg` / `brew install ffmpeg` / `apt install ffmpeg`).

```bash
git clone https://github.com/Tragettechragul/instatools
cd instatools
pip install -e ".[ai]"        # add ,transcribe for speech-to-text: ".[ai,transcribe]"
playwright install chromium
instatools login              # a browser opens: log in to Instagram yourself, then press Enter
```

For automatic captions, set an Anthropic API key: `export ANTHROPIC_API_KEY=sk-ant-...` (on Windows: `setx ANTHROPIC_API_KEY ...`). Without a key, captions come only from your note files.

## Posting automatically

Start the watcher and leave it running:

```bash
instatools watch
```

Then drop files into `data/inbox/`:

| You drop | It posts |
|---|---|
| `clip.mp4` | A Reel |
| `photo.jpg` | A single image post |
| `clip.mp4` + `clip.txt` | The `.txt` is used as the **exact** caption |
| `clip.mp4` + `clip.txt` starting with `brief: ...` | Claude writes the caption from your brief |
| `clip.mp4` alone, with an API key set | Claude looks at the media and writes the caption, hashtags and alt text in the style of your recent posts |
| A folder with 2–10 images or videos (+ `caption.txt`) | A carousel, in file-name order |

After each post:
- The files move to `data/posted/<time>-<name>/`, along with `result.json` holding the **live post link**, the caption and the alt text.
- Anything that fails moves to `data/failed/`, with the error.
- If Instagram shows a captcha, checkpoint, "Try again later" or "Action blocked", the tool writes `data/STOPPED.txt` and exits. **It doesn't retry.** Sort it out in the Instagram app, then delete `STOPPED.txt` to start again.
- A log of everything is kept in `data/instatools.log`.

To run it with no window, set `INSTATOOLS_HEADLESS=1`. To change the gap between posts, set `INSTATOOLS_MIN_GAP_MINUTES=10`. To run it from cron or Windows Task Scheduler instead of leaving it running, use `instatools watch --once`.

## Pulling content

```bash
instatools pull                       # your latest 12 posts
instatools pull someaccount --limit 20
instatools get https://www.instagram.com/reel/XXXX/ --transcribe
```

Each post is saved to `data/library/<account>/<post-id>/`:
- `01.mp4` / `01.jpg` … — the full-size media (every slide of a carousel)
- `01.m4a` — the audio track pulled out of each video
- `01.transcript.txt` — timestamped speech-to-text (with `--transcribe`)
- `caption.txt` and `post.json` — caption, likes, comments, plays/views, post time, audio name

When captions are generated automatically, your own pulled captions are used as style examples.

## Commands

| Command | What it does |
|---|---|
| `instatools login` | Log in by hand once; the session is saved in `data/browser-profile/` |
| `instatools whoami` | Check which account the saved session is logged in as |
| `instatools watch [--once]` | Post everything dropped into the inbox |
| `instatools post FILE... [--caption "..."]` | Post now, without using the inbox |
| `instatools pull [USER] [--limit N] [--transcribe]` | Download a profile's posts |
| `instatools get URL [--transcribe]` | Download one post or Reel |

## Limits

- **Insights** (reach, demographics, best times) aren't included yet. instagram.com shows only part of them, and the layout changes often.
- **Layout changes:** buttons are found by their visible labels ("New post", "Next", "Share"). If Instagram renames them, posting fails safely to `data/failed/`, and the selector in `instatools/poster.py` needs updating.
- **Other people's content:** downloading it is for your own research. Don't repost it without permission.
- **`data/browser-profile/` is your logged-in session.** Treat it like a password. It's git-ignored, so never commit or share it.

## Tests

```bash
pip install pytest && pytest -q
```
The offline tests check post parsing, inbox detection and hard-stop detection. They don't touch Instagram.
