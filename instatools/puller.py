"""Pulls posts from a profile (yours or any public one): media files, caption, stats, audio."""
import json
import logging
import re
import subprocess
from pathlib import Path

from playwright.sync_api import Page

from . import config
from .browser import IG, goto
from .guards import pause

log = logging.getLogger("instatools")
SHORTCODE = re.compile(r"/(?:p|reel|reels)/([A-Za-z0-9_-]+)")


def _json_after(html: str, key: str):
    """Parse the JSON value that follows "key": in the page's embedded data."""
    i = html.find(f'"{key}":')
    if i < 0:
        return None
    j = i + len(key) + 3
    while j < len(html) and html[j].isspace():
        j += 1
    try:
        return json.JSONDecoder().raw_decode(html, j)[0]
    except Exception:
        return None


def _best(candidates) -> str | None:
    if not candidates:
        return None
    best = max(candidates, key=lambda c: (c.get("width") or 0) * (c.get("height") or 0))
    return best.get("url")


def _media_urls(html: str) -> list[tuple[str, str]]:
    """[(kind, url)] for the post — handles single image, video and carousels."""
    out: list[tuple[str, str]] = []
    carousel = _json_after(html, "carousel_media")
    items = carousel if isinstance(carousel, list) and carousel else [None]
    if items == [None]:
        v = _best(_json_after(html, "video_versions"))
        if v:
            return [("video", v)]
        img = _json_after(html, "image_versions2")
        u = _best((img or {}).get("candidates")) if isinstance(img, dict) else None
        if u:
            out.append(("image", u))
        else:
            m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if m:
                out.append(("image", m.group(1).replace("&amp;", "&")))
        return out
    for it in items:
        if it.get("video_versions"):
            out.append(("video", _best(it["video_versions"])))
        elif it.get("image_versions2"):
            out.append(("image", _best(it["image_versions2"].get("candidates"))))
    return [(k, u) for k, u in out if u]


def _meta(html: str, prop: str) -> str:
    m = re.search(rf'<meta (?:property|name)="{prop}" content="([^"]*)"', html)
    return m.group(1).replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'") if m else ""


def _caption(html: str) -> str:
    cap = _json_after(html, "caption")
    if isinstance(cap, dict) and cap.get("text"):
        return cap["text"]
    desc = _meta(html, "og:description")  # '123 likes, 4 comments - user on Date: "caption"'
    m = re.search(r':\s*"(.*)"\s*\.?$', desc, re.S)
    return m.group(1) if m else desc


def _stats(html: str) -> dict:
    stats = {}
    for key in ("like_count", "comment_count", "play_count", "view_count", "taken_at"):
        m = re.search(rf'"{key}":(\d+)', html)
        if m:
            stats[key] = int(m.group(1))
    audio = _json_after(html, "music_metadata") or _json_after(html, "clips_metadata")
    if isinstance(audio, dict):
        info = (audio.get("music_info") or {}).get("music_asset_info") or audio.get("original_sound_info") or {}
        stats["audio"] = {k: info.get(k) for k in ("title", "display_artist", "original_audio_title") if info.get(k)}
    return stats


def extract_audio(video: Path) -> Path | None:
    out = video.with_suffix(".m4a")
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-c:a", "copy", str(out)],
                       check=True, timeout=300)
        return out
    except Exception as e:
        log.warning("audio extraction failed for %s: %s", video, e)
        return None


def transcribe(audio: Path) -> str | None:
    """Speech-to-text with faster-whisper, if installed (`pip install instatools[transcribe]`)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(str(audio))
    lines = [f"[{s.start:6.1f}s – {s.end:6.1f}s] {s.text.strip()}" for s in segments]
    out = audio.with_suffix(".transcript.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def pull_post(page: Page, cfg: config.Config, url: str, owner: str = "", do_transcribe: bool = False) -> Path:
    code = SHORTCODE.search(url).group(1)
    goto(page, url)
    html = page.content()
    owner = owner or _meta(html, "instapp:owner_user_id") or "unknown"
    folder = cfg.library / owner / code
    folder.mkdir(parents=True, exist_ok=True)

    files = []
    for i, (kind, media_url) in enumerate(_media_urls(html), 1):
        ext = "mp4" if kind == "video" else "jpg"
        target = folder / f"{i:02d}.{ext}"
        if not target.exists():
            resp = page.request.get(media_url)
            if not resp.ok:
                log.warning("download failed (%s) %s", resp.status, media_url[:80])
                continue
            target.write_bytes(resp.body())
            pause(1, 2)
        entry = {"file": target.name, "kind": kind}
        if kind == "video":
            audio = extract_audio(target)
            if audio:
                entry["audio"] = audio.name
                if do_transcribe:
                    entry["transcript"] = transcribe(audio)
        files.append(entry)

    record = {"url": url, "shortcode": code, "owner": owner, "caption": _caption(html), **_stats(html), "files": files}
    (folder / "post.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "caption.txt").write_text(record["caption"], encoding="utf-8")
    log.info("pulled %s → %s (%d files)", url, folder, len(files))
    return folder


def pull_profile(page: Page, cfg: config.Config, username: str, limit: int = 12, do_transcribe: bool = False) -> list[Path]:
    goto(page, f"{IG}{username}/")
    links: list[str] = []
    for _ in range(10):
        hrefs = page.locator("a[href*='/p/'], a[href*='/reel/']").evaluate_all("els => els.map(e => e.href)")
        links = list(dict.fromkeys(links + hrefs))
        if len(links) >= limit:
            break
        page.mouse.wheel(0, 1500)
        pause(2, 4)
    out = []
    for url in links[:limit]:
        out.append(pull_post(page, cfg, url, owner=username, do_transcribe=do_transcribe))
        pause(3, 7)
    return out
