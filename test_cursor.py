from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",  # use your installed Google Chrome
        )
        page = browser.new_page()
        page.goto("https://example.com")
        print(page.title())
        input("Press Enter to close...")

if __name__ == "__main__":
    main()
