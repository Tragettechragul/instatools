"""One persistent Chromium profile. You log in by hand once; the tool never sees your password."""
from contextlib import contextmanager

from playwright.sync_api import BrowserContext, Page, sync_playwright

from . import config
from .guards import NotLoggedIn, check, pause

IG = "https://www.instagram.com/"


@contextmanager
def session(cfg: config.Config, headless: bool | None = None, mobile: bool = False):
    """mobile=True emulates a phone: instagram.com only offers Story upload on mobile web."""
    with sync_playwright() as pw:
        device = dict(pw.devices["Pixel 7"]) if mobile else {"viewport": {"width": 1280, "height": 900}}
        device.pop("default_browser_type", None)
        ctx: BrowserContext = pw.chromium.launch_persistent_context(
            str(cfg.profile_dir),
            headless=config.HEADLESS if headless is None else headless,
            locale="en-GB",
            **device,
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            yield page
        finally:
            ctx.close()


def goto(page: Page, url: str) -> None:
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded")
            break
        except Exception as e:  # Instagram redirects mid-load (e.g. /accounts/onetap/ "save login info")
            if "interrupted by another navigation" not in str(e) or attempt == 2:
                raise
            page.wait_for_load_state("domcontentloaded")
            pause(1, 2)
            dismiss_popups(page)
    pause(2, 4)
    dismiss_popups(page)
    check(page)


def dismiss_popups(page: Page) -> None:
    if "/accounts/onetap" in page.url:  # "Save your login info?" — saving keeps the session alive
        for name in ("Save info", "Save Info", "Not now", "Not Now"):
            btn = page.get_by_role("button", name=name, exact=True)
            if btn.count():
                btn.first.click(timeout=3000)
                page.wait_for_load_state("domcontentloaded")
                pause(1, 2)
                break
    for name in ("Not now", "Not Now", "Decline optional cookies", "Allow all cookies"):
        btn = page.get_by_role("button", name=name, exact=True)
        if btn.count():
            try:
                btn.first.click(timeout=2000)
                pause(1, 2)
            except Exception:
                pass


def logged_in_username(page: Page) -> str:
    goto(page, IG)
    if page.locator("input[name='password']").count():
        raise NotLoggedIn("Not logged in — run `instatools login`.")
    # The profile link in the side nav points to /<username>/
    for link in page.locator("a[href^='/'][role='link']").all():
        if (link.get_attribute("aria-label") or "").lower().startswith("profile") or link.locator("img[alt*='profile picture']").count():
            href = (link.get_attribute("href") or "").strip("/")
            if href and "/" not in href:
                return href
    raise NotLoggedIn("Could not find your profile link — are you logged in?")


def interactive_login(cfg: config.Config) -> None:
    with session(cfg, headless=False) as page:
        page.goto(IG)
        print("A browser window is open. Log in to Instagram there yourself (including any 2FA).")
        input("When you can see your feed, press Enter here… ")
        print(f"Logged in as @{logged_in_username(page)}. Session saved in {cfg.profile_dir}")
