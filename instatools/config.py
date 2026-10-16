"""Paths and settings. Everything lives under one data directory (default ./data)."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path

    @property
    def profile_dir(self) -> Path:  # persistent browser profile: holds the login session
        return self.root / "browser-profile"

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def posted(self) -> Path:
        return self.root / "posted"

    @property
    def failed(self) -> Path:
        return self.root / "failed"

    @property
    def library(self) -> Path:  # pulled posts
        return self.root / "library"

    @property
    def stop_file(self) -> Path:  # written on captcha / block; watcher refuses to run while it exists
        return self.root / "STOPPED.txt"

    @property
    def log_file(self) -> Path:
        return self.root / "instatools.log"

    def ensure(self) -> "Config":
        for p in (self.root, self.inbox, self.posted, self.failed, self.library):
            p.mkdir(parents=True, exist_ok=True)
        return self


def load(root: str | None = None) -> Config:
    return Config(Path(root or os.environ.get("INSTATOOLS_HOME", "data")).resolve()).ensure()


HEADLESS = os.environ.get("INSTATOOLS_HEADLESS", "0") == "1"
CLAUDE_MODEL = os.environ.get("INSTATOOLS_MODEL", "claude-sonnet-5-5")
