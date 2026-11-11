from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()
        page.goto("https://example.com")

        print("Browser launched successfully!")
        print("Page title:", page.title())

        browser.close()


if __name__ == "__main__":
    main()