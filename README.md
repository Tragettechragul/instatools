# instatools

A Claude skill that runs your Instagram account **through your own Chrome**, where you're already logged in, using the Claude in Chrome extension. No API, no password, no third-party tools.

It covers five jobs:

1. **Pull my data:** reach, views, profile visits and follower change; stats for each post; audience details. It then tells you which format and posting times win, and which way the trend is going.
2. **Niche research:** finds 5–10 UK IT support, cyber security, PC build and data recovery accounts. For each it records the bio, how often they post, their format mix, their top 3 posts, full captions, caption structure and audio.
3. **Reel breakdown:** goes through a Reel beat by beat, explains why it works, and turns it into a script you can film yourself.
4. **Caption research:** analyses your captions and competitors' captions, then gives you 5 caption templates based on what performs.
5. **Posting:** drafts the post, shows it to you in full, and publishes only after your **yes**. It then confirms the post is live and gives you the link.

Everything it collects is saved under `instagram-data/` with dates in the file names, so nothing is lost between sessions. This folder is git-ignored, so it stays private.

## Install

You need Claude Code (or the Claude desktop app) **on your own computer**, plus the [Claude in Chrome](https://claude.ai/chrome) extension installed and connected. A cloud session can't reach your browser, so this won't work from claude.ai/code.

```
/plugin marketplace add Tragettechragul/instatools
/plugin install instatools@instatools
```

Then just ask, for example:

- "Pull my Instagram insights"
- "Research UK IT support accounts on Instagram"
- "Break down this reel: https://www.instagram.com/reel/…"
- "Give me caption templates"
- "Draft an Instagram post about recovering data from a failed SSD"

## Safety rules built in

- Nothing gets posted, liked, followed, commented on or messaged without your yes on that exact item.
- It never asks for or types a password.
- It works at human speed, one action at a time.
- It **stops immediately** if it hits a captcha, a login challenge, a rate limit or "action blocked", and doesn't retry.
- It records numbers exactly as Instagram shows them. Anything it couldn't collect is marked as missing, never guessed.

You can read all the rules in `plugins/instatools/skills/instagram-manager/references/safety-rules.md`.

## Known limits

| Want | Reality |
|---|---|
| Full insights for 7, 30 and 90 days, plus demographics | The instagram.com dashboard shows less than the phone app. Missing fields are marked `NOT AVAILABLE ON WEB`. |
| Whether an audio is "rising or peaked" | Instagram mostly shows this only in the app. On the web you get the number of Reels using the audio. |
| Transcribing a Reel | It can read on-screen text and visible auto-captions. It can't hear audio. |
| Competitors' saves and shares | Only the account owner can see these. |
| Uploading files | The file picker is your computer's own dialog. You may need to select the file yourself. |
| Instagram changing its layout | The skill finds things by what's on the page, not fixed links, but large redesigns may need updates. |

## Customise

Edit `plugins/instatools/skills/instagram-manager/references/profile.md`. It holds your bio facts, the claims you're allowed to make in public, your tone and your content pillars.
