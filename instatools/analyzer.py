"""Give it a link, get everything: caption, on-screen text, speech, comments, tools, GitHub repos, steps."""
import json
import logging
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import Page

from . import ai, config, puller

log = logging.getLogger("instatools")
GITHUB_URL = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def _duration(video: Path) -> float:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(video)], capture_output=True, text=True, timeout=60).stdout
        return float(out.strip())
    except Exception:
        return 0.0


def _frames(video: Path, max_frames: int = 16) -> list[tuple[float, bytes]]:
    dur = _duration(video) or 30.0
    step = max(dur / max_frames, 1.0)
    out, t = [], 0.3
    while t < dur and len(out) < max_frames:
        data = ai.jpeg(video, at=t, width=768)
        if data:
            out.append((round(t, 1), data))
        t += step
    return out


def _page_text(page: Page) -> str:
    """Visible text of the post page — includes the top comments and the creator's replies."""
    try:
        for _ in range(2):  # open a couple of comment pages
            more = page.locator("svg[aria-label='Load more comments']")
            if more.count():
                more.first.click()
                page.wait_for_timeout(2000)
        return page.locator("main, article, body").first.inner_text(timeout=5000)[:15000]
    except Exception:
        return ""


def github_lookup(name: str) -> list[dict]:
    """Top public GitHub repos for a tool name (unauthenticated search API, 10 req/min)."""
    q = urllib.parse.quote(name)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "instatools"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=3",
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            items = json.load(r).get("items", [])
    except Exception as e:
        log.warning("GitHub lookup failed for %s: %s", name, e)
        return []
    return [{"repo": i["full_name"], "url": i["html_url"], "stars": i["stargazers_count"],
             "description": i.get("description") or ""} for i in items]


PROMPT = """You are analysing an Instagram post so the user never has to watch it.
Inputs: the caption, a timestamped speech transcript (may be empty), visible page text including comments,
and frames from the video (timestamps given) or the post images. Read ALL on-screen text in the frames.

Reply with JSON only:
{
 "summary": "3-5 sentences: what the post shows and claims",
 "type": "tool showcase | tutorial | news | opinion | other",
 "on_screen_text": [{"t": seconds, "text": "verbatim"}],
 "beats": [{"t": seconds, "what": "what happens / is said"}],
 "tools": [{"name": "exact name", "what_it_does": "...", "github": "owner/repo if visible or stated, else null",
            "links": ["any URL seen or said"], "search_query": "best GitHub search query to find it"}],
 "steps": ["concrete steps to reproduce / install, if any were shown"],
 "commands_or_code": ["verbatim commands or code visible"],
 "cta": "what the creator asks viewers to do (e.g. comment a keyword for the link)",
 "hook": "first 2 seconds: words + visuals",
 "claims_to_verify": ["claims that sound too good / need checking"],
 "useful_for_me": "how this could be used, honestly; say if it's hype"
}
Never invent tools, links or commands that are not in the inputs. Use null / [] when unknown."""


def analyze(page: Page, cfg: config.Config, url: str) -> Path:
    folder = puller.pull_post(page, cfg, url, do_transcribe=True)
    page_text = _page_text(page)
    record = json.loads((folder / "post.json").read_text(encoding="utf-8"))

    transcript = ""
    content: list[dict] = []
    for f in record["files"]:
        path = folder / f["file"]
        if f["kind"] == "video":
            if f.get("transcript"):
                transcript += Path(f["transcript"]).read_text(encoding="utf-8") + "\n"
            for t, data in _frames(path):
                content += [{"type": "text", "text": f"[frame {f['file']} @ {t}s]"}, ai.image_block(data)]
        else:
            data = ai.jpeg(path)
            if data:
                content += [{"type": "text", "text": f"[image {f['file']}]"}, ai.image_block(data)]

    content.append({"type": "text", "text": (
        f"{PROMPT}\n\nURL: {url}\nCAPTION:\n{record.get('caption', '')}\n\n"
        f"TRANSCRIPT:\n{transcript or '(no speech transcript available)'}\n\nPAGE TEXT:\n{page_text}")})
    result = ai.ask_json(content[-100:], max_tokens=6000)

    # Resolve tools to real GitHub repos: explicit links first, then search.
    blob = " ".join([record.get("caption", ""), transcript, page_text, json.dumps(result)])
    seen = {f"{o}/{r}".rstrip(".") for o, r in GITHUB_URL.findall(blob)}
    for tool in result.get("tools", []):
        if tool.get("github"):
            seen.add(tool["github"])
        tool["github_matches"] = github_lookup(tool.get("search_query") or tool["name"])
    result["github_links_found"] = sorted(seen)
    result["stats"] = {k: record.get(k) for k in ("like_count", "comment_count", "play_count", "view_count")}
    result["url"] = url

    (folder / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "analysis.md").write_text(to_markdown(result, record), encoding="utf-8")
    return folder


def to_markdown(a: dict, record: dict) -> str:
    L = [f"# Analysis — {a['url']}", "", a.get("summary", ""), "",
         f"**Type:** {a.get('type','')}  ", f"**Hook:** {a.get('hook','')}  ", f"**CTA:** {a.get('cta','')}", ""]
    if a.get("tools"):
        L += ["## Tools", ""]
        for t in a["tools"]:
            L.append(f"### {t['name']}")
            L.append(t.get("what_it_does", ""))
            if t.get("github"):
                L.append(f"- Stated repo: https://github.com/{t['github']}")
            for link in t.get("links") or []:
                L.append(f"- Link: {link}")
            for m in t.get("github_matches", []):
                L.append(f"- GitHub match: [{m['repo']}]({m['url']}) ★{m['stars']} — {m['description']}")
            L.append("")
    if a.get("github_links_found"):
        L += ["## GitHub links seen in the post", ""] + [f"- https://github.com/{g}" for g in a["github_links_found"]] + [""]
    for title, key in (("Steps", "steps"), ("Commands / code", "commands_or_code"),
                       ("Claims to verify", "claims_to_verify")):
        if a.get(key):
            L += [f"## {title}", ""] + [f"- {x}" for x in a[key]] + [""]
    if a.get("beats"):
        L += ["## Beat by beat", "", "| t | what |", "|---|---|"]
        L += [f"| {b.get('t')}s | {str(b.get('what','')).replace('|','/')} |" for b in a["beats"]] + [""]
    if a.get("on_screen_text"):
        L += ["## On-screen text", ""] + [f"- {o.get('t')}s: {o.get('text')}" for o in a["on_screen_text"]] + [""]
    L += ["## Is it useful?", "", a.get("useful_for_me", ""), "", "## Caption", "", "```", record.get("caption", ""), "```"]
    return "\n".join(L)
