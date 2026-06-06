from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from .config import BrowserConfig


class BrowserSession:
    def __init__(self, config: BrowserConfig):
        self._config = config
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def launch(self) -> Page:
        user_data = Path(self._config.user_data_dir).resolve()
        user_data.mkdir(parents=True, exist_ok=True)

        self._pw = sync_playwright().start()
        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            headless=self._config.headless,
            viewport={"width": 1280, "height": 900},
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        return self._page

    def ensure_logged_in(self, page: Page) -> None:
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        if "/login" in page.url or "/authwall" in page.url:
            print("\n⏸  Not logged in. Please log into LinkedIn in the browser window.")
            print("   Press Enter here once you're logged in...")
            input()
            page.wait_for_url("**/feed/**", timeout=120000)
        print("✓ Logged into LinkedIn")

    def close(self) -> None:
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
