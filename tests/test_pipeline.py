"""Offline tests for notes, photo editing, frame/audio extraction and report formatting."""
import subprocess

import pytest
from PIL import Image

from instatools import analyzer, community, editor, notes, puller


def test_note_parsing(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("type: story\ncommunity: Tamil\nbrief: wedding with family\n\nOur big day")
    n = notes.parse(p)
    assert (n.type, n.community, n.brief, n.caption) == ("story", "Tamil", "wedding with family", "Our big day")
    assert notes.parse(None).type == "post"
    p.write_text("Just a caption: with a colon")
    assert notes.parse(p).caption == "Just a caption: with a colon"


def test_photo_edit_story_and_post(tmp_path):
    src = tmp_path / "p.jpg"
    Image.new("RGB", (3000, 2000), (90, 100, 140)).save(src)
    story = editor.apply(src, tmp_path / "s.jpg", {"brightness": 1.2, "warmth": 0.1, "focus_x": 0.3}, "story")
    post = editor.apply(src, tmp_path / "f.jpg", {"brightness": 9, "saturation": "bad"}, "post")  # clamped / ignored
    assert Image.open(story).size == (1080, 1920)
    assert Image.open(post).size == (1080, 1350)
    r, g, b = Image.open(story).getpixel((540, 960))
    assert r > 90 * 1.2 and b < 140 * 1.2  # brighter and warmer
    assert src.stat().st_size > 0  # original kept


@pytest.fixture
def clip(tmp_path):
    v = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=4:size=320x568:rate=25",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", str(v)], check=True)
    return v


def test_frames_and_audio(clip):
    frames = analyzer._frames(clip, max_frames=4)
    assert 2 <= len(frames) <= 4 and frames[0][1][:2] == b"\xff\xd8"
    audio = puller.extract_audio(clip)
    assert audio and audio.stat().st_size > 0


def test_markdown_report():
    md = analyzer.to_markdown({"url": "u", "summary": "s", "tools": [
        {"name": "n8n", "what_it_does": "workflows", "github": "n8n-io/n8n", "links": [],
         "github_matches": [{"repo": "n8n-io/n8n", "url": "https://github.com/n8n-io/n8n", "stars": 1, "description": "d"}]}],
        "github_links_found": ["n8n-io/n8n"], "steps": ["install"]}, {"caption": "c"})
    assert "### n8n" in md and "https://github.com/n8n-io/n8n" in md and "- install" in md


def test_community_hashtags():
    assert community.hashtags_for("Wedding", "Tamil")[:2] == ["tamilwedding", "tamilmemories"]
    assert community.hashtags_for("trip", "") == ["trip", "tripmemories"]


def test_install_plan(tmp_path):
    from instatools import installer
    (tmp_path / "requirements.txt").write_text("rich")
    (tmp_path / "package.json").write_text('{"scripts": {"build": "tsc"}}')
    steps = installer.plan(tmp_path)
    assert steps[0][1:] == ["-m", "venv", ".venv"] and steps[1][-2:] == ["-r", "requirements.txt"]
    assert ["npm", "install"] in steps and ["npm", "run", "build"] in steps
