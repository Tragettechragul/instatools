# Module 3 — Reel breakdown

Read-only. Input: a Reel URL from the user. Output: `instagram-data/reels/YYYY-MM-DD-<handle>-<shortcode>.md` from `templates/reel-breakdown.md`.

## What can and can't be captured
- **Can:** on-screen text overlays, burned-in captions, Instagram's auto-captions **if** visible on the web player, the posted caption, audio name, view/like/comment counts.
- **Can't:** hear audio. Speech that isn't captioned on screen is marked `[speech not captioned — not transcribed]`. Never guess what was said.
- Timestamps are approximate (to ~1 s), read from the player's progress. Say so in the file.

## Steps
1. Open the Reel. Record handle, URL, date, views, likes, comments, audio name, full caption.
2. Turn on captions if the player offers a CC control.
3. Step through the Reel: pause at the start, then advance in ~1-second steps (pause → screenshot → read). At each step record: timestamp, on-screen text (verbatim), caption text (verbatim), what is shown (shot type, e.g. "close-up of hands on SSD", "face to camera", "screen recording").
4. Note cuts: each time the shot changes, mark it. Count cuts in the first 5 s and overall.

## Breakdown (why it worked)
- **Hook (0–2 s):** exact first words/text, what's on screen, which hook type (question, bold claim, mistake warning, result-first, "POV", list promise).
- **Pacing:** total length, number of cuts, average shot length, where the payoff lands.
- **Text overlay style:** position, size, colour/outline, words per card, whether it duplicates speech.
- **CTA:** wording, timing (on screen vs caption), type (follow, comment keyword, save, DM, link in bio).
- **Fit for Rocky:** what's reusable under a professional tone, what isn't.

## Script template
End the file with a fill-in-the-blanks script the user can film themselves, in this shape:

| Time | Shot | On-screen text | Say | Notes |
|---|---|---|---|---|
| 0–2 s | … | [HOOK — ≤7 words] | … | … |

Plus: suggested length, shot list, props, and a caption draft using a module 4 template if one exists.
