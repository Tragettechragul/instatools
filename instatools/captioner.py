"""Caption, hashtags and alt text: your exact caption if given, otherwise written by Claude."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import ai, config
from .notes import Note

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}


@dataclass
class PostText:
    caption: str
    alt_texts: list[str] = field(default_factory=list)


def _style_examples(cfg: config.Config, n: int = 5) -> str:
    caps = []
    for meta in sorted(cfg.library.glob("*/*/post.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]:
        try:
            if c := json.loads(meta.read_text(encoding="utf-8")).get("caption"):
                caps.append(c)
        except Exception:
            pass
    return "\n---\n".join(caps)


def build(cfg: config.Config, media: list[Path], note: Note, advice: dict | None = None) -> PostText:
    if note.caption:
        return PostText(note.caption)
    if not ai.available():
        return PostText(note.brief)
    content: list[dict] = []
    for m in media[:10]:
        if data := ai.jpeg(m, at=1.0 if m.suffix.lower() in VIDEO_EXT else None):
            content.append(ai.image_block(data))
    examples = _style_examples(cfg)
    content.append({"type": "text", "text": (
        f"Write an Instagram {note.type} caption for the media above.\n"
        f"Owner's brief: {note.brief or '(none — describe what is shown)'}\n"
        + (f"Language: {note.language}\n" if note.language else "")
        + (f"Community: {note.community}. Style seen in that community: {json.dumps(advice, ensure_ascii=False)}\n"
           if advice else (f"Community: {note.community}\n" if note.community else ""))
        + (f"Match the voice of the owner's recent captions:\n{examples}\n" if examples else "")
        + "Rules: hook in the first line (under 125 characters); short; warm and natural; "
          "3-8 relevant hashtags on the last line; never invent names, places or facts not given or visible. "
          f"Also one alt text per item ({len(media)} total), plain description, under 100 words each.\n"
          'Reply with JSON only: {"caption": "...", "alt_texts": ["..."]}'
    )})
    data = ai.ask_json(content, max_tokens=1500)
    return PostText(data["caption"].strip(), [a.strip() for a in data.get("alt_texts", [])])
