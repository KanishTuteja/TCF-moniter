"""
TCF Canada Exam Slot Monitor
Checks the Alliance Française Toronto page every 10 minutes
and emails you when a new slot appears.

SETUP (run once):
    pip install playwright
    playwright install chromium

Fill in your Gmail details below before running.
"""

import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from playwright.sync_api import sync_playwright

# ── CONFIG ─────────────────────────────────────────────────────────────────
URL = "https://www.alliance-francaise.ca/en/exams/tests/informations-about-tcf-canada/tcf-canada"

YOUR_EMAIL    = "your_email@gmail.com"       # where to SEND the alert
GMAIL_ADDRESS = "your_email@gmail.com"       # your Gmail account
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password (not your regular password)
                                              # Get one at: myaccount.google.com/apppasswords

CHECK_EVERY_MINUTES = 1
# ───────────────────────────────────────────────────────────────────────────


def get_slots(page):
    """Return the text content of the TCF Canada slot sections."""
    page.goto(URL, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)

    # Grab both E-TCF and P-TCF sections
    content = page.locator("text=E-TCF Canada, text=P-TCF Canada").all_text_contents()

    # Broader fallback — grab the whole exam section
    full_text = page.locator("main, #main, .content, article").first.inner_text()
    return full_text


def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = YOUR_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print(f"[{now()}] ✅ Email sent!")


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

                if last_snapshot is None:
                    # First run — just save the baseline
                    last_snapshot = current
                    print(f"[{now()}] Baseline saved. Monitoring for changes...\n")

                elif current != last_snapshot:
                    print(f"[{now()}] ⚠️  PAGE CHANGED — sending notification!")
                    send_email(
                        subject="🗓️ TCF Canada Slot Available!",
                        body=(
                            "A change was detected on the TCF Canada booking page.\n\n"
                            "Check it now before it fills up:\n"
                            f"{URL}\n\n"
                            f"Detected at: {now()}"
                        )
                    )
                    last_snapshot = current  # update so you don't get spammed

                else:
                    print(f"[{now()}] No change. Next check in {CHECK_EVERY_MINUTES} min.\n")

            except Exception as e:
                print(f"[{now()}] Error: {e} — will retry next cycle.")

            time.sleep(CHECK_EVERY_MINUTES * 60)

        browser.close()


if __name__ == "__main__":
    main()
