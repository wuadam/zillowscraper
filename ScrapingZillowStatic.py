import json
import os
import subprocess
import time
from bs4 import BeautifulSoup
from langchain.tools import tool
from playwright.sync_api import sync_playwright


def launch_authenticated_chrome_internally():
    """Launches an isolated desktop Chrome instance directly via process arguments, bypassing CMD string parsing."""
    print("[RPA Launcher] Spawning Chrome directly via native process execution...")

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Isolate the automation profile entirely inside your git project directory
    project_root = r"C:\GIT\ZillowScraper"
    profile_dir = os.path.join(project_root, "AutomationProfile")

    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir, exist_ok=True)

    # By passing these as a list, Python automatically manages the spaces and quotes perfectly for Windows
    arguments = [
        chrome_path,
        "https://www.zillow.com",
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ]

    # Launch the process directly without shell=True to avoid string mangling
    subprocess.Popen(
        arguments,
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[RPA Launcher] Giving Chrome 4 seconds to boot up and initialize port 9222...")
    time.sleep(4)


@tool
def fetch_zillow_raw_html(url: str) -> str:
    """Launches Chrome via CMD, harvests property cards across ALL pages using pagination logic."""

    launch_authenticated_chrome_internally()

    print("\n[RPA Monitor] Attaching Playwright to your active Chrome window...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]

            page = context.pages[0] if context.pages else context.new_page()
            print(
                f"[RPA Monitor] Connected! Currently watching tab: '{page.title()}'"
            )

            # --- FIXED: FORCE NAVIGATION IF WE ARE NOT ON THE EXACT LISTINGS SEARCH TARGET ---
            if page.url.rstrip('/') != url.rstrip('/'):
                print(f"[RPA Monitor] Tab is not on search results target. Navigating to: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            else:
                print("[RPA Monitor] Tab is already resting on target search results. Proceeding with execution...")

            print(
                "[RPA Monitor] Siphoning visual state. Resolve any popups on your screen now..."
            )
            page.wait_for_timeout(3000)

            # --- PAGINATION & INCREMENTAL HARVESTER LOOP ---
            scroll_container = "#search-page-list-container"
            all_collected_cards_html = []

            page_number = 1
            has_next_page = True

            while has_next_page:
                # --- NEW FEATURE: LIVE ANTI-BOT INTERCEPT PATROL ---
                captcha_selector = "iframe[id*='px-captcha'], #px-captcha-modal"
                if page.locator(captcha_selector).count() > 0 or "denied" in page.title().lower():
                    print("\n[🚨 ANTIBOT ALERT] Zillow dropped a security check challenge on your screen!")
                    print(
                        "[RPA Action Required] Please focus the active Chrome browser window and solve the CAPTCHA manually.")
                    print("[RPA Monitor] System idling. Waiting for human override clearance...")

                    # Stall execution loops seamlessly until you click and clear the CAPTCHA check layout
                    while page.locator(captcha_selector).count() > 0 or "denied" in page.title().lower():
                        page.wait_for_timeout(2000)

                    print("[🎉 Clearance Granted] Bot block successfully bypassed. Resuming automation harvest...")
                    page.wait_for_timeout(2000)

                print(f"\n[RPA Pagination] Starting deep harvest on Page {page_number}...")

                # Safety Anchor: Force Playwright to wait until the container actually exists and holds visible text
                page.locator(scroll_container).wait_for(state="visible", timeout=10000)
                page.wait_for_timeout(1500)  # Quick breather for the DOM to settle

                if page.locator(scroll_container).count() > 0:
                    # Capture the absolute top card text on this page to use as a transition anchor
                    initial_panel_text = page.locator(scroll_container).inner_text()[:300]

                    # Iterate down the side-panel to defeat virtual DOM recycling
                    for step in range(1, 16):
                        scroll_depth = step * 650
                        page.evaluate(
                            f"document.querySelector('{scroll_container}').scrollTo(0, {scroll_depth});"
                        )
                        page.wait_for_timeout(1000)

                        # Grab live snapshot at this step
                        panel_html = page.locator(scroll_container).inner_html()
                        mini_soup = BeautifulSoup(panel_html, "html.parser")
                        visible_cards = mini_soup.find_all(
                            ["article", "div"],
                            class_=lambda c: c and ("property-card" in c or "StyledCard" in c or "ListItem" in c)
                        )

                        for card in visible_cards:
                            card_str = str(card)
                            if card_str not in all_collected_cards_html:
                                all_collected_cards_html.append(card_str)
                else:
                    print("[Warning] Split-panel layout missing on this page option.")
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    page.wait_for_timeout(2000)
                    all_collected_cards_html.append(page.content())

                print(
                    f"[RPA Pagination] Page {page_number} harvest complete. Cache size: {len(all_collected_cards_html)} cards.")

                # --- PAGINATION NAVIGATOR: Look for the 'Next Page' button ---
                next_button_selector = 'a[rel="next"]'

                if page.locator(next_button_selector).count() > 0:
                    next_button = page.locator(next_button_selector).first

                    is_disabled = next_button.get_attribute("aria-disabled") == "true" or "disabled" in (
                            next_button.get_attribute("class") or "").lower()

                    if not is_disabled:
                        print("[RPA Pagination] 'Next Page' button found. Navigating to the next batch...")

                        # Smooth scroll to bottom of the container to bring pagination controls into view
                        page.evaluate(
                            f"document.querySelector('{scroll_container}').scrollTo(0, document.querySelector('{scroll_container}').scrollHeight);")
                        page.wait_for_timeout(500)

                        # Quick structural defense check right before clicking
                        if page.locator(captcha_selector).count() > 0:
                            continue

                        next_button.click()
                        page_number += 1

                        # HARD TRANSITION WAIT: Wait until the text inside the container physically updates
                        try:
                            page.wait_for_function(
                                f"document.querySelector('{scroll_container}').innerText.substring(0, 300) !== '{initial_panel_text}'",
                                timeout=8000
                            )
                        except Exception:
                            print("[RPA Pagination] Timeout waiting for listing data change. Proceeding anyway...")

                        page.wait_for_timeout(2000)
                    else:
                        print("[RPA Pagination] 'Next' button is disabled. Reached the absolute end of the listings.")
                        has_next_page = False
                else:
                    print("[RPA Pagination] No 'Next Page' navigation link located on this DOM structure. Stopping.")
                    has_next_page = False
            # ---------------------------------------------------------------------

        except Exception as conn_err:
            return f"Could not connect to Chrome port or navigate. Error: {str(conn_err)}"

        # --- DEDUPLICATION AND FIELD EXTRACTION FROM HARVESTED STORAGE ---
        extracted_properties = []

        for card_html in all_collected_cards_html:
            card_soup = BeautifulSoup(card_html, "html.parser")
            card_text = card_soup.get_text(separator=" ", strip=True)

            link_element = card_soup.find("a", href=True)
            link_url = link_element["href"] if link_element else ""
            if link_url and link_url.startswith("/"):
                link_url = "https://www.zillow.com" + link_url

            if card_text and len(card_text) > 20:
                if not any(p["url"] == link_url for p in extracted_properties if link_url):
                    extracted_properties.append(
                        {"raw_card_data": card_text, "url": link_url}
                    )

        if not extracted_properties:
            print("[Warning] Class selectors missed. Pulling raw body content fallback.")
            soup = BeautifulSoup(all_collected_cards_html[0], "html.parser")
            body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
            return json.dumps([{"raw_card_data": body_text[:200000]}])

        print(f"[Success] Bundled {len(extracted_properties)} total unique property cards across all pages.")
        return json.dumps(extracted_properties)