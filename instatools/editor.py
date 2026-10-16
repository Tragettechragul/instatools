"""Looks at a photo, decides how to improve it, and applies the edit (Pillow). The original is never changed."""
import json
import logging
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from . import ai

log = logging.getLogger("instatools")
TARGETS = {"story": (1080, 1920), "post": (1080, 1350)}

PROMPT = """You are a photo editor preparing this image for an Instagram {kind}.
Context from the owner: {brief}
Community / audience style to respect: {community}
Reference posts from that community (captions/descriptions), if any:
{refs}

Look at the photo: subject, lighting, colour cast, exposure, faces, occasion, mood.
Decide a tasteful, natural edit (no heavy filters; skin tones must stay true).
Reply with JSON only:
{{
 "what_it_is": "one sentence",
 "occasion": "e.g. wedding, birthday, temple visit, trip, food, everyday",
 "mood": "e.g. warm, festive, calm",
 "issues": ["e.g. underexposed, blue cast"],
 "edit": {{
   "brightness": 1.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0,
   "warmth": 0.0,
   "focus_x": 0.5, "focus_y": 0.5
 }},
 "why": "short reason for the edit"
}}
Ranges: brightness/contrast/saturation 0.8-1.3, sharpness 1.0-1.6, warmth -0.15..0.15 (positive = warmer),
focus_x/focus_y = centre of the main subject (0-1) used for cropping."""


def _warmth(img: Image.Image, w: float) -> Image.Image:
    if abs(w) < 0.005:
        return img
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * (1 + w))))
    b = b.point(lambda v: min(255, int(v * (1 - w))))
    return Image.merge("RGB", (r, g, b))


def _clamp(v, lo, hi, default):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


def apply(src: Path, dest: Path, edit: dict, kind: str = "post") -> Path:
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(_clamp(edit.get("brightness"), 0.8, 1.3, 1.0))
    img = ImageEnhance.Contrast(img).enhance(_clamp(edit.get("contrast"), 0.8, 1.3, 1.0))
    img = ImageEnhance.Color(img).enhance(_clamp(edit.get("saturation"), 0.8, 1.3, 1.0))
    img = _warmth(img, _clamp(edit.get("warmth"), -0.15, 0.15, 0.0))
    sharp = _clamp(edit.get("sharpness"), 1.0, 1.6, 1.0)
    if sharp > 1.0:
        img = ImageEnhance.Sharpness(img).enhance(sharp)
    w, h = TARGETS[kind]
    centre = (_clamp(edit.get("focus_x"), 0, 1, 0.5), _clamp(edit.get("focus_y"), 0, 1, 0.5))
    img = ImageOps.fit(img, (w, h), Image.LANCZOS, centering=centre)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=40, threshold=3))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=92)
    return dest


def plan(src: Path, kind: str, brief: str = "", community: str = "", refs: str = "") -> dict:
    data = ai.jpeg(src)
    return ai.ask_json([ai.image_block(data), {"type": "text", "text": PROMPT.format(
        kind=kind, brief=brief or "(none)", community=community or "(none)", refs=refs or "(none)")}],
        max_tokens=1200)


def auto_edit(src: Path, out_dir: Path, kind: str, brief: str = "", community: str = "", refs: str = "") -> tuple[Path, dict]:
    """Returns (edited file, plan). Without an API key: only crops/resizes for the format."""
    p = plan(src, kind, brief, community, refs) if ai.available() else {"edit": {}, "why": "no API key: crop only"}
    out = apply(src, out_dir / f"{src.stem}-edited.jpg", p.get("edit", {}), kind)
    (out_dir / f"{src.stem}-edit.json").write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("edited %s → %s (%s)", src.name, out.name, p.get("why", ""))
    return out, p
