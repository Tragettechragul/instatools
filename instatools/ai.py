"""Small wrapper around Claude: images + text in, JSON out."""
import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

from . import config


class NoApiKey(RuntimeError):
    pass


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def jpeg(path: Path, at: float | None = None, width: int = 1024) -> bytes | None:
    """A JPEG of an image, or of a video frame at `at` seconds."""
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "f.jpg"
        args = ["ffmpeg", "-y", "-loglevel", "error"]
        if at is not None:
            args += ["-ss", f"{at:.2f}"]
        args += ["-i", str(path), "-frames:v", "1", "-vf", f"scale='min({width},iw)':-2", str(out)]
        try:
            subprocess.run(args, check=True, timeout=120)
            return out.read_bytes()
        except Exception:
            return None


def image_block(data: bytes) -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                        "data": base64.b64encode(data).decode()}}


def ask_json(content: list[dict], max_tokens: int = 4000) -> dict:
    if not available():
        raise NoApiKey("Set ANTHROPIC_API_KEY to use AI features.")
    import anthropic

    msg = anthropic.Anthropic().messages.create(
        model=config.CLAUDE_MODEL, max_tokens=max_tokens, messages=[{"role": "user", "content": content}])
    raw = "".join(b.text for b in msg.content if b.type == "text")
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
