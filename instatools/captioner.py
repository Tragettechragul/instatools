"""Builds caption, hashtags and alt text.

Priority: a sidecar note file next to the media (exact text is used as-is unless it starts with
"brief:"), then Claude if ANTHROPIC_API_KEY is set, then a bare fallback.
"""
import base64
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import config

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}


@dataclass
class PostText:
    caption: str
    alt_texts: list[str] = field(default_factory=list)


def _read_note(note: Path | None) -> str:
    return note.read_text(encoding="utf-8").strip() if note and note.exists() else ""


def _preview_jpeg(path: Path) -> bytes | None:
    """A JPEG Claude can look at: the image itself, or a frame 1 s into a video."""
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return path.read_bytes()
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "f.jpg"
        args = ["ffmpeg", "-y", "-loglevel", "error"]
        if path.suffix.lower() in VIDEO_EXT:
            args += ["-ss", "1"]
        args += ["-i", str(path), "-frames:v", "1", "-vf", "scale=1024:-2", str(out)]
        try:
            subprocess.run(args, check=True, timeout=60)
            return out.read_bytes()
        except Exception:
            return None


def _style_examples(cfg: config.Config, n: int = 5) -> str:
    """Your own recent captions (from `instatools pull`), so generated captions match your voice."""
    caps = []
    for meta in sorted(cfg.library.glob("*/*/post.json"), reverse=True)[:n]:
        try:
            c = json.loads(meta.read_text()).get("caption", "")
            if c:
                caps.append(c)
        except Exception:
            pass
    return "\n---\n".join(caps)


def _claude(cfg: config.Config, media: list[Path], brief: str) -> PostText:
    import anthropic

    content: list[dict] = []
    for m in media[:10]:
        jpg = _preview_jpeg(m)
        if jpg:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                          "data": base64.b64encode(jpg).decode()}})
    examples = _style_examples(cfg)
    content.append({"type": "text", "text": (
        "Write an Instagram caption for the media above.\n"
        f"Brief from the account owner: {brief or '(none — describe what is shown)'}\n"
        + (f"Match the voice of these recent captions from the same account:\n{examples}\n" if examples else "")
        + "Rules: hook in the first line (under 125 characters); short body; one clear call to action; "
          "3-8 relevant hashtags on the last line; no invented facts, numbers or claims. "
          f"Also write one alt text per image ({len(media)} total), plain description, under 100 words each.\n"
          'Reply with JSON only: {"caption": "...", "alt_texts": ["..."]}'
    )})
    client = anthropic.Anthropic()
    msg = client.messages.create(model=config.CLAUDE_MODEL, max_tokens=1500,
                                 messages=[{"role": "user", "content": content}])
    raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = raw[raw.find("{"): raw.rfind("}") + 1]
    data = json.loads(raw)
    return PostText(caption=data["caption"].strip(), alt_texts=[a.strip() for a in data.get("alt_texts", [])])


def build(cfg: config.Config, media: list[Path], note: Path | None) -> PostText:
    text = _read_note(note)
    if text and not text.lower().startswith("brief:"):
        return PostText(caption=text)  # your exact caption
    brief = text[6:].strip() if text else ""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _claude(cfg, media, brief)
    return PostText(caption=brief)
