"""Researches how a community posts a given kind of moment: top posts under its hashtags,
their caption style and the songs/audio they use. Read-only; nothing is liked or followed."""
import json
import logging
import re

from playwright.sync_api import Page

from . import ai, config, puller
from .browser import IG, goto
from .guards import HardStop, NotLoggedIn, pause

log = logging.getLogger("instatools")


def hashtags_for(occasion: str, community: str) -> list[str]:
    occ = re.sub(r"[^a-z0-9]", "", occasion.lower()) or "memories"
    com = re.sub(r"[^a-z0-9]", "", community.lower())
    tags = [f"{com}{occ}", f"{com}memories", f"{com}{'reels'}", f"{occ}{com}"] if com else []
    return list(dict.fromkeys(tags + [occ, f"{occ}memories"]))[:5]


def read_tag(page: Page, tag: str, n: int = 6) -> list[dict]:
    goto(page, f"{IG}explore/tags/{tag}/")
    links = page.locator("a[href*='/p/'], a[href*='/reel/']").evaluate_all("els => els.map(e => e.href)")
    out = []
    for url in list(dict.fromkeys(links))[:n]:
        goto(page, url)
        html = page.content()
        stats = puller._stats(html)
        out.append({"url": url, "caption": puller._caption(html)[:600], "likes": stats.get("like_count"),
                    "audio": stats.get("audio")})
        pause(3, 6)
    return out


def research(page: Page, cfg: config.Config, occasion: str, community: str, kind: str = "post") -> dict:
    refs = []
    for tag in hashtags_for(occasion, community):
        try:
            posts = read_tag(page, tag)
        except (HardStop, NotLoggedIn):
            raise
        except Exception as e:  # a missing / empty hashtag just gets skipped
            log.warning("tag #%s skipped: %s", tag, e)
            continue
        refs += [dict(p, tag=tag) for p in posts]
        if len(refs) >= 18:
            break
    summary = {"occasion": occasion, "community": community, "references": refs}
    if ai.available() and refs:
        summary["advice"] = ai.ask_json([{"type": "text", "text": (
            f"These are popular Instagram posts for '{occasion}' in the {community or 'general'} community:\n"
            f"{json.dumps(refs, ensure_ascii=False)[:12000]}\n\n"
            f"For a new {kind} of this kind, reply JSON only: "
            '{"caption_style": "language mix, length, emoji use, typical phrases", '
            '"songs": [{"title": "", "artist": "", "seen_in": "url"}], '
            '"hashtags": ["..."], "visual_style": "editing/colour trends seen"}. '
            "Only list songs that actually appear in the audio fields above.")}], max_tokens=1500)
    path = cfg.library / "community" / f"{re.sub(r'[^a-z0-9]+', '-', (community + '-' + occasion).lower()).strip('-')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
