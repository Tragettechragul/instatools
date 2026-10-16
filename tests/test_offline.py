"""Offline tests: parsing, inbox detection, hard-stop detection. No Instagram access needed."""
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from instatools import config, puller, watcher
from instatools.guards import HardStop, check

HTML = ('<meta property="og:description" content="5 likes - x: &quot;hi&quot;">'
        '<script>{"caption":{"text":"Fixing a dead SSD #datarecovery"},"like_count":42,"comment_count":3,'
        '"video_versions":[{"width":480,"height":854,"url":"https://cdn/low.mp4"},'
        '{"width":1080,"height":1920,"url":"https://cdn/hi.mp4"}]}</script>')
CAROUSEL = json.dumps({"carousel_media": [
    {"image_versions2": {"candidates": [{"width": 1080, "height": 1350, "url": "https://cdn/a.jpg"}]}},
    {"video_versions": [{"width": 720, "height": 1280, "url": "https://cdn/b.mp4"}]}]})


def test_video_post_parsing():
    assert puller._media_urls(HTML) == [("video", "https://cdn/hi.mp4")]
    assert puller._caption(HTML) == "Fixing a dead SSD #datarecovery"
    assert puller._stats(HTML)["like_count"] == 42


def test_carousel_parsing():
    assert puller._media_urls(CAROUSEL) == [("image", "https://cdn/a.jpg"), ("video", "https://cdn/b.mp4")]


def test_inbox_detection(tmp_path):
    cfg = config.load(str(tmp_path))
    (cfg.inbox / "clip.mp4").write_bytes(b"x")
    (cfg.inbox / "clip.txt").write_text("caption")
    (cfg.inbox / "set").mkdir()
    for n in ("2.jpg", "1.jpg", "caption.txt"):
        (cfg.inbox / "set" / n).write_text("x")
    items = {i.source.name: i for i in watcher.find_items(cfg)}
    assert items["clip.mp4"].note.name == "clip.txt"
    assert [m.name for m in items["set"].media] == ["1.jpg", "2.jpg"]
    assert items["set"].note.name == "caption.txt"


@pytest.mark.parametrize("body,stops", [("<p>Try Again Later</p>", True), ("<p>Action Blocked</p>", True),
                                         ("<p>Your feed</p>", False)])
def test_hard_stop(body, stops):
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        page = b.new_page()
        page.set_content(body)
        if stops:
            with pytest.raises(HardStop):
                check(page)
        else:
            check(page)
        b.close()
