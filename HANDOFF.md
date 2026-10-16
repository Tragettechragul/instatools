# Handoff — instatools

Paste this into a Claude session **running on Rocky's Windows PC** (Cowork / Claude desktop / Claude Code), opened in:
`C:\Users\Ragul\Downloads\instatools-claude-new-repo-setup-kauzex\instatools-claude-new-repo-setup-kauzex`

## Goal
A local tool that:
1. **(Main)** Takes an Instagram post/Reel link → opens it in a logged-in browser → reads caption, on-screen text (video frames), speech (transcript), comments → reports the tools / GitHub repos shown, steps, commands, honest verdict → on "yes", installs the chosen GitHub tool on this PC.
2. Autoposts from a drop folder (`data/inbox/`): photos/videos/carousels/Stories, with AI photo edit, community-style research (e.g. Tamil hashtags → caption style, songs), AI caption + alt text.
3. Pulls posts/media/audio from any profile.

Repo: https://github.com/Tragettechragul/instatools (branch `claude/new-repo-setup-kauzex`). Python + Playwright (browser automation of instagram.com, user chose this over the official API and accepted the ToS/ban risk). Claude API (`ANTHROPIC_API_KEY`) for analysis/edit/captions; faster-whisper for speech.

## Code map
- `instatools/cli.py` — commands: login, whoami, watch, post, pull, get, analyze, install, edit, research
- `browser.py` persistent Chromium profile in `data/browser-profile` (user logs in by hand once) · `guards.py` hard stops on captcha/challenge/"action blocked" (never retry)
- `analyzer.py` link → report (`analysis.md/json`) · `installer.py` clone to `~/instatools-apps/<repo>` + detected install steps
- `poster.py` feed post + Story (mobile emulation) · `watcher.py` drop folder · `editor.py` Pillow edits from Claude plan · `community.py` hashtag research · `captioner.py`, `notes.py`, `puller.py`, `ai.py`
- `tests/` 12 offline tests pass (`pytest -q`)

## Status on this PC
- `.venv` created, pip upgraded, package + transcribe installed, Chromium installed (done by Rocky).
- `instatools login` crashed: Instagram redirected to `/accounts/onetap/` mid-navigation. **Fixed in commit after f236338** (`browser.goto` retries + handles the "Save login info" page). Pull the latest code (re-download ZIP or `git pull`) before continuing.
- Never tested against live Instagram yet — selectors in `poster.py` (New post / Next / Share, caption box, Story upload) and parsing in `puller.py` (`video_versions`, `carousel_media`, `caption`) are best guesses and may need adjusting on first real run.

## Next steps
1. Update code, then `.\.venv\Scripts\instatools.exe login` → log in → Enter → expect "Logged in as @…".
2. `.\.venv\Scripts\instatools.exe whoami`
3. `.\.venv\Scripts\instatools.exe analyze "https://www.instagram.com/p/DeGpq1zFFXi/"` — fix whatever breaks (likely media/caption parsing), until the report is correct.
4. Then test `post` with one throwaway image, `pull`, and `watch`.
5. Push fixes to the same branch.

## Rules from Rocky
- Never ask for / type his Instagram password; he logs in himself.
- Stop immediately on captcha, login challenge, rate limit, "action blocked" — don't retry.
- Keep personal details (certifications etc.) out of the tool.
- Be honest about what didn't work; don't fake results.
