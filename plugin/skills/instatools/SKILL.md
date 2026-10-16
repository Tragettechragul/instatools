---
name: instatools
description: Analyse any Instagram post or Reel from just its link (reads caption, on-screen text, speech, comments; finds the tools and GitHub repos shown), download posts, edit photos, research how a community posts something, and post to Instagram — by running the local `instatools` CLI. Use whenever the user pastes an instagram.com link, or asks to analyse, pull, edit, research or post Instagram content.
---

# instatools

The user has the `instatools` CLI installed on this computer (https://github.com/Tragettechragul/instatools) and is logged in through it. Run it with Bash. All output is saved under `$INSTATOOLS_HOME` (default `./data`).

First check it is installed: `instatools whoami`. If the command is missing, tell the user to follow the README install steps. If it says not logged in, tell them to run `instatools login` themselves. Never ask for their password.

## User pastes an Instagram link

Run `instatools analyze "<url>"` (allow up to 10 minutes; transcription is slow on first use). It prints a Markdown report: summary, tools with matching GitHub repos, steps, commands, beats, on-screen text and claims to verify.

Then answer in chat:
1. What the post is, in 2–3 lines.
2. Each tool: what it does, plus the GitHub repo link. Say whether the repo was **stated in the post** or is a **search match** (search matches can be wrong; say so).
3. Steps or commands to try it, if shown.
4. Honest verdict: useful, or hype?
If the user asks for more, read `analysis.json` in the printed folder.

Then ask: "Want me to install any of these?" If the user says yes to a repo, run
`instatools install <owner/repo> -y`. It clones into `~/instatools-apps/<repo>` and runs the detected install
steps (virtualenv / npm / go / cargo, no sudo). Report the result and the run command it prints. Before
installing, flag anything from the README notes it prints (paid API keys, broad permissions). Only install a
**search match** after telling the user it wasn't named in the post.

## Other requests

| User wants | Run |
|---|---|
| Install a GitHub tool | `instatools install <owner/repo> -y` (only after the user says yes) |
| Download a profile's posts | `instatools pull <username> --limit N` |
| One post's media/audio/transcript | `instatools get "<url>" --transcribe` |
| Improve a photo | `instatools edit <file> [--story] [--brief "..."]` |
| How a community posts X | `instatools research <occasion> --community <name>` |
| Post now | `instatools post <files...> [--caption "..."]` |
| Post later / Story | write the files plus a note into `$INSTATOOLS_HOME/inbox/` (see note format below); the running `instatools watch` handles it |

Note file (same name as the media, `.txt`; or `caption.txt` in a folder):
```
type: story          # or post
community: tamil     # optional
brief: what it is    # Claude writes the caption from this
edit: auto           # or off

Optional exact caption here
```

## Stop conditions
If any command exits with code 2 or prints `STOPPED`, Instagram showed a captcha or a block. Tell the user exactly what it printed. Do not run any more instatools commands until they say it's cleared.
