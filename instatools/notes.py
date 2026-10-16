"""Note files that travel with dropped media.

Optional `key: value` header lines, then free text:

    type: story            # post (default) | story
    community: tamil       # whose music / caption style to reference
    edit: auto             # auto (default) | off
    brief: wedding memories with family, keep it warm

    Anything after the headers is used as the exact caption.
"""
from dataclasses import dataclass
from pathlib import Path

KEYS = {"type", "community", "edit", "brief", "language"}


@dataclass
class Note:
    type: str = "post"
    community: str = ""
    edit: str = "auto"
    brief: str = ""
    language: str = ""
    caption: str = ""


def parse(path: Path | None) -> Note:
    note = Note()
    if not path or not path.exists():
        return note
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        key, sep, val = lines[i].partition(":")
        if sep and key.strip().lower() in KEYS:
            setattr(note, key.strip().lower(), val.strip())
            i += 1
        elif not lines[i].strip() and i == 0:
            i += 1
        else:
            break
    note.caption = "\n".join(lines[i:]).strip()
    note.type = "story" if note.type.lower().startswith("stor") else "post"
    return note
