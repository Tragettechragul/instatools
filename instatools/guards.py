"""Human pacing and hard stops. A hard stop is never retried: it halts the tool until a person clears it."""
import random
import time

from playwright.sync_api import Page

BLOCK_PHRASES = (
    "try again later",
    "action blocked",
    "we restrict certain activity",
    "temporarily blocked",
    "suspicious login attempt",
    "confirm it's you",
    "help us confirm",
    "enter the code we sent",
    "we suspect automated behavior",
    "please wait a few minutes",
)
BLOCK_URL_PARTS = ("/challenge", "/accounts/suspended", "/checkpoint", "/two_factor")


class HardStop(RuntimeError):
    """Captcha, login challenge, rate limit or block. Do not retry."""


class NotLoggedIn(RuntimeError):
    pass


def pause(lo: float = 2.0, hi: float = 5.0) -> None:
    time.sleep(random.uniform(lo, hi))


def check(page: Page) -> None:
    url = page.url.lower()
    if any(part in url for part in BLOCK_URL_PARTS):
        raise HardStop(f"Instagram challenge page: {page.url}")
    if "/accounts/login" in url:
        raise NotLoggedIn("Session expired — run `instatools login`.")
    try:
        text = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        return
    for phrase in BLOCK_PHRASES:
        if phrase in text:
            raise HardStop(f'Instagram says: "{phrase}" ({page.url})')
    if page.locator("iframe[src*='captcha'], iframe[title*='captcha' i]").count():
        raise HardStop(f"Captcha shown ({page.url})")
