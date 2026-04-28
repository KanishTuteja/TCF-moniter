"""
TCF Canada Exam Slot Monitor
Sends a push notification via ntfy.sh when a new slot appears.

SETUP:
    1. Download the ntfy app on your phone
    2. Subscribe to channel: tcf-kanish
    3. Deploy this script on Railway
"""

import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# ── CONFIG ─────────────────────────────────────────────────────────────────
URL = "https://www.alliance-francaise.ca/en/exams/tests/informations-about-tcf-canada/tcf-canada"
NTFY_CHANNEL = "tcf-kanish"
CHECK_EVERY_MINUTES = 1
# ───────────────────────────────────────────────────────────────────────────


def get_slots(page):
    """Grab only the registration/slot section of the page."""
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(5000)

    # Try to get just the registrations section
    try:
        slots = page.locator("text=Registrations").locator("..").inner_text(timeout=10000)
        return slots
    except:
        # Fallback — look for date tables
        try:
            slots = page.locator("table").all_inner_texts()
            return " | ".join(slots)
        except:
            return ""


def send_notification(message):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_CHANNEL}",
            data=message.encode("utf-8"),
            headers={
                "Title": "TCF Canada Slot Available!",
                "Priority": "urgent",
                "Tags": "rotating_light"
            },
            timeout=10
        )
        print(f"[{now()}] ✅ Notification sent!")
    except Exception as e:
        print(f"[{now()}] Failed to send notification: {e}")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    print(f"[{now()}] Starting TCF Canada slot monitor...")
    print(f"Checking every {CHECK_EVERY_MINUTES} minutes. Press Ctrl+C to stop.\n")

    last_snapshot = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            try:
                print(f"[{now()}] Checking page...")
                current = get_slots(page)

                if not current:
                    print(f"[{now()}] Could not read slot section — will retry next cycle.\n")

                elif last_snapshot is None:
                    last_snapshot = current
                    print(f"[{now()}] Baseline saved. Monitoring for changes...\n")
                    print(f"Current slots: {current[:200]}\n")

                elif current != last_snapshot:
                    print(f"[{now()}] ⚠️ CHANGE DETECTED — sending notification!")
                    send_notification(
                        f"A slot change was detected on the TCF Canada page! Check now: {URL}"
                    )
                    last_snapshot = current

                else:
                    print(f"[{now()}] No change. Next check in {CHECK_EVERY_MINUTES} min.\n")

            except Exception as e:
                print(f"[{now()}] Error: {e} — will retry next cycle.")

            time.sleep(CHECK_EVERY_MINUTES * 60)

        browser.close()


if __name__ == "__main__":
    main()
