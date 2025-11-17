"""
Browser-based HTML fetching using Playwright.

This module handles fetching Google Travel Explore pages by:
1. Launching a headless browser
2. Navigating to the URL
3. Waiting for destination cards to render
4. Extracting the fully-rendered HTML
"""

from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def fetch_html_browser(
    url: str,
    proxy: Optional[str] = None,
    timeout: float = 30.0,
    headless: bool = True,
) -> str:
    """
    Fetch HTML using Playwright browser automation.
    
    Args:
        url: URL to fetch
        proxy: Optional proxy server (format: http://host:port or http://user:pass@host:port)
        timeout: Maximum time to wait for page load (seconds)
        headless: Whether to run browser in headless mode
        
    Returns:
        Fully-rendered HTML content
        
    Raises:
        PlaywrightTimeoutError: If page doesn't load in time
        Exception: For other browser-related errors
    """
    async with async_playwright() as p:
        # Configure browser launch options
        launch_kwargs = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        }
        
        # Configure proxy if provided
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
        
        # Launch browser
        browser = await p.chromium.launch(**launch_kwargs)
        
        try:
            # Create context with realistic settings
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            
            # Create page
            page = await context.new_page()
            
            # Set longer timeout for initial navigation
            page.set_default_timeout(timeout * 1000)  # Convert to milliseconds
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle")
            
            # Wait for destination cards to appear
            # We look for the card container class that we know from parsing
            try:
                await page.wait_for_selector(".SwQ5Be", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                # If cards don't appear, still return the HTML for debugging
                pass
            
            # Give it a moment for any final rendering
            await page.wait_for_timeout(2000)
            
            # Extract the fully-rendered HTML
            html = await page.content()
            
            await context.close()
            
            return html
            
        finally:
            await browser.close()

