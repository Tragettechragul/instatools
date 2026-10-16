"""Publishes a post through instagram.com's own "Create" flow."""
import logging
from pathlib import Path

from playwright.sync_api import Page

from .browser import IG, goto, logged_in_username
from .captioner import VIDEO_EXT, PostText
from .guards import HardStop, check, pause

log = logging.getLogger("instatools")


class PostFailed(RuntimeError):
    pass


def _click(page: Page, *names: str, timeout: int = 15000) -> None:
    """Click the first visible button/link/menu item matching any of the names."""
    for _ in range(timeout // 500):
        for name in names:
            for role in ("button", "link", "menuitem"):
                loc = page.get_by_role(role, name=name, exact=True)
                if loc.count() and loc.first.is_visible():
                    loc.first.click()
                    pause(1.5, 3)
                    check(page)
                    return
            loc = page.locator(f"svg[aria-label='{name}']")
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                pause(1.5, 3)
                check(page)
                return
        page.wait_for_timeout(500)
    raise PostFailed(f"Couldn't find '{names[0]}' on the page — Instagram's layout may have changed.")


def publish(page: Page, media: list[Path], text: PostText) -> str:
    username = logged_in_username(page)
    before = _grid_links(page, username)  # pinned posts sit first, so find the *new* link afterwards
    goto(page, IG)

    _click(page, "New post", "Create")
    # Newer layouts show a small menu: Post / Live video / Ad
    sub = page.get_by_role("link", name="Post", exact=True)
    if sub.count() and sub.first.is_visible():
        sub.first.click()
        pause()

    file_input = page.locator("input[type='file']").first
    file_input.wait_for(state="attached", timeout=20000)
    file_input.set_input_files([str(p) for p in media])
    pause(4, 7)
    check(page)

    # Reels notice ("Video posts are now shared as reels")
    ok = page.get_by_role("button", name="OK", exact=True)
    if ok.count() and ok.first.is_visible():
        ok.first.click()
        pause()

    _click(page, "Next")  # crop
    _click(page, "Next")  # filters / edit

    box = page.locator("div[aria-label^='Write a caption'][contenteditable='true']").first
    box.wait_for(timeout=20000)
    box.click()
    pause(0.5, 1)
    page.keyboard.insert_text(text.caption)
    pause(1, 2)

    if text.alt_texts and not any(p.suffix.lower() in VIDEO_EXT for p in media):
        _set_alt_texts(page, text.alt_texts)

    _click(page, "Share")
    _wait_shared(page)
    return _new_post_url(page, username, before)


def _set_alt_texts(page: Page, alts: list[str]) -> None:
    try:
        _click(page, "Accessibility", timeout=5000)
    except PostFailed:
        log.warning("Accessibility section not found; posting without alt text")
        return
    fields = page.locator("input[placeholder^='Write alt text']")
    for i in range(min(fields.count(), len(alts))):
        fields.nth(i).fill(alts[i])
        pause(0.5, 1.2)


def _wait_shared(page: Page) -> None:
    for _ in range(240):  # up to ~2 minutes for video processing
        check(page)
        body = page.locator("body").inner_text().lower()
        if "has been shared" in body or "reel shared" in body or "post shared" in body:
            pause(2, 3)
            close = page.locator("svg[aria-label='Close']")
            if close.count():
                close.first.click()
            return
        if "couldn't be shared" in body or "something went wrong" in body:
            raise PostFailed("Instagram said the post couldn't be shared.")
        page.wait_for_timeout(500)
    raise PostFailed("No 'shared' confirmation after 2 minutes — check the profile manually before retrying.")


def _grid_links(page: Page, username: str) -> list[str]:
    goto(page, f"{IG}{username}/")
    page.wait_for_timeout(2000)
    hrefs = page.locator("a[href*='/p/'], a[href*='/reel/']").evaluate_all("els => els.map(e => e.href)")
    return list(dict.fromkeys(hrefs))[:24]


def _new_post_url(page: Page, username: str, before: list[str]) -> str:
    for _ in range(3):
        new = [h for h in _grid_links(page, username) if h not in before]
        if new:
            return new[0]
        pause(5, 8)
    raise PostFailed("Instagram confirmed the share, but the new post isn't on the profile grid yet.")
