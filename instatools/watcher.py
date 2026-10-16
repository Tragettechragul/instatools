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

from . import captioner, config, poster
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
    text = captioner.build(cfg, item.media, item.note)
    with session(cfg) as page:
        url = poster.publish(page, item.media, text)
    return {"status": "published", "url": url, "caption": text.caption, "alt_texts": text.alt_texts,
            "media": [p.name for p in item.media], "time": datetime.now().isoformat(timespec="seconds")}


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
