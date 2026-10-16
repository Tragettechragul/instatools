"""Drop-folder automation.

    data/inbox/clip.mp4  (+ clip.txt)        → one post / Reel
    data/inbox/holiday/  (1-10 images/videos, + caption.txt) → carousel, files in name order

Done items move to data/posted/ (with result.json holding the post link); errors to data/failed/.
A captcha / block writes data/STOPPED.txt and the watcher exits; it won't start again until you delete it.
"""
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import ai, captioner, community, config, editor, notes, poster
from .browser import session
from .guards import HardStop, NotLoggedIn

log = logging.getLogger("instatools")
MEDIA_EXT = captioner.IMAGE_EXT | captioner.VIDEO_EXT
MIN_GAP = int(os.environ.get("INSTATOOLS_MIN_GAP_MINUTES", "10")) * 60


@dataclass
class Item:
    source: Path          # file or folder in the inbox
    media: list[Path]
    note: Path | None


def _stable(path: Path, wait: float = 3.0) -> bool:
    """True once the file/folder has stopped growing (so half-copied files aren't posted)."""
    def size(p: Path) -> int:
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
    a = size(path)
    time.sleep(wait)
    return a == size(path) and a > 0


def find_items(cfg: config.Config) -> list[Item]:
    items = []
    for entry in sorted(cfg.inbox.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            media = sorted(p for p in entry.iterdir() if p.suffix.lower() in MEDIA_EXT)
            if media:
                note = next((entry / n for n in ("caption.txt", "note.txt") if (entry / n).exists()), None)
                items.append(Item(entry, media[:10], note))
        elif entry.suffix.lower() in MEDIA_EXT:
            note = entry.with_suffix(".txt")
            items.append(Item(entry, [entry], note if note.exists() else None))
    return items


def _archive(item: Item, dest_root: Path, record: dict) -> Path:
    dest = dest_root / f"{datetime.now():%Y%m%d-%H%M%S}-{item.source.stem}"
    dest.mkdir(parents=True)
    shutil.move(str(item.source), dest / item.source.name)
    if item.note and item.note.exists() and item.note.parent == item.source.parent and not item.source.is_dir():
        shutil.move(str(item.note), dest / item.note.name)
    (dest / "result.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return dest


def process(cfg: config.Config, item: Item) -> dict:
    note = notes.parse(item.note)
    work = cfg.root / "work" / f"{datetime.now():%Y%m%d-%H%M%S}-{item.source.stem}"
    work.mkdir(parents=True, exist_ok=True)
    images = [m for m in item.media if m.suffix.lower() in captioner.IMAGE_EXT]
    record: dict = {"type": note.type, "community": note.community}

    # 1. What is this photo? (decides the occasion used for community research)
    first_plan = editor.plan(images[0], note.type, note.brief, note.community) if images and ai.available() else {}
    occasion = first_plan.get("occasion") or note.brief.split(",")[0] or "memories"

    with session(cfg) as page:
        # 2. How does this community post this kind of moment? (songs, caption style)
        advice = None
        if note.community:
            research = community.research(page, cfg, occasion, note.community, note.type)
            advice = research.get("advice")
            record["community_research"] = {"references": len(research["references"]), "advice": advice}
        # 3. Edit photos (originals untouched)
        media = []
        for m in item.media:
            if m in images and note.edit != "off":
                refs = json.dumps(advice.get("visual_style", ""), ensure_ascii=False) if advice else ""
                edited, plan = editor.auto_edit(m, work, note.type, note.brief, note.community, refs)
                media.append(edited)
                record.setdefault("edits", {})[m.name] = plan
            else:
                media.append(m)
        # 4. Caption + alt text
        text = captioner.build(cfg, media, note, advice) if note.type == "post" else captioner.PostText("")
        # 5. Publish
        if note.type == "post":
            url = poster.publish(page, media, text)
    if note.type == "story":
        if not images:
            raise poster.PostFailed("Stories from this tool support photos only.")
        with session(cfg, mobile=True) as page:
            for m in (m for m in media if m.suffix.lower() in captioner.IMAGE_EXT):
                url = poster.publish_story(page, m)
    record.update({"status": "published", "url": url, "caption": text.caption, "alt_texts": text.alt_texts,
                   "media": [p.name for p in item.media], "time": datetime.now().isoformat(timespec="seconds")})
    if advice and advice.get("songs"):
        record["suggested_songs"] = advice["songs"]  # Instagram web can't attach music; add it in the app
    return record


def run(cfg: config.Config, once: bool = False, poll: int = 30) -> None:
    last_post = 0.0
    log.info("watching %s", cfg.inbox)
    while True:
        if cfg.stop_file.exists():
            log.error("STOPPED: %s — read it, sort it out in Instagram yourself, then delete the file.",
                      cfg.stop_file.read_text().strip())
            return
        for item in find_items(cfg):
            if not _stable(item.source):
                continue
            wait = MIN_GAP - (time.time() - last_post)
            if last_post and wait > 0:
                log.info("spacing posts: next in %d min", wait // 60 + 1)
                break
            log.info("posting %s", item.source.name)
            try:
                record = process(cfg, item)
                dest = _archive(item, cfg.posted, record)
                log.info("LIVE: %s  (archived to %s)", record["url"], dest)
                last_post = time.time()
            except (HardStop, NotLoggedIn) as e:
                cfg.stop_file.write_text(f"{datetime.now():%Y-%m-%d %H:%M} {type(e).__name__}: {e}\n")
                log.error("STOPPED — %s. Not retrying. %s left in the inbox.", e, item.source.name)
                return
            except Exception as e:
                dest = _archive(item, cfg.failed, {"status": "failed", "error": f"{type(e).__name__}: {e}"})
                log.exception("failed: %s → %s", item.source.name, dest)
                last_post = time.time()  # don't hammer Instagram after a failure either
            break  # one post per cycle
        if once:
            return
        time.sleep(poll)
