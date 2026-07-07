"""
Test sending a DM using Playwright Browser Automation.
This bypasses ALL API bot detection by physically driving a real browser.
"""
from playwright.sync_api import sync_playwright
import time
import config
from urllib.parse import unquote
import sys

if not config.IG_SESSION_ID:
    print("❌ No IG_SESSION_ID set in .env")
    sys.exit(1)

session_id = unquote(config.IG_SESSION_ID)
user_id = session_id.split(":")[0]

print("Starting Playwright Browser...")
with sync_playwright() as p:
    # Launch browser (set headless=False to watch it work!)
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )

    # Inject the session cookie
    context.add_cookies([
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".instagram.com",
            "path": "/"
        },
        {
            "name": "ds_user_id",
            "value": user_id,
            "domain": ".instagram.com",
            "path": "/"
        }
    ])

    page = context.new_page()
    
    print("--- Step 1: Navigating to Inbox ---")
    page.goto("https://www.instagram.com/direct/inbox/", wait_until="networkidle")
    
    # Check if we were redirected to login
    if "accounts/login" in page.url:
        print("❌ Session is INVALID (Redirected to login). You need a fresh sessionid cookie!")
        browser.close()
        sys.exit(1)
        
    print("✅ Logged in successfully!")

    # Wait for the first thread to load and click it
    print("--- Step 2: Opening first chat ---")
    
    # Handle the "Turn on Notifications" popup if it appears
    try:
        not_now_button = page.locator("button:has-text('Not Now')").first
        if not_now_button.is_visible(timeout=3000):
            not_now_button.click()
            print("  Dismissed notifications popup")
    except Exception:
        pass

    try:
        # Click the first message thread using its link href
        thread_link = page.locator("a[href^='/direct/t/']").first
        thread_link.wait_for(state="visible", timeout=10000)
        thread_link.click()
        print("✅ Clicked first thread")
    except Exception as e:
        print(f"❌ Failed to find or click a thread: {e}")
        page.screenshot(path="debug_inbox.png")
        print("Saved debug_inbox.png so we can see what went wrong.")
        browser.close()
        sys.exit(1)

    # Wait a moment for the chat to load
    time.sleep(2)

    print("--- Step 3: Sending message ---")
    test_msg = "Hello! This is a test from the Playwright bot 🤖"
    
    try:
        # Locate the message input box
        message_box = page.locator("div[contenteditable='true'][role='textbox']").first
        message_box.wait_for(state="visible", timeout=5000)
        message_box.click()
        message_box.fill(test_msg)
        
        # Press Enter to send
        message_box.press("Enter")
        print("✅ Message typed and sent!")
        
        # Wait a couple seconds to ensure it went through
        time.sleep(3)
        page.screenshot(path="debug_success.png")
        print("Saved debug_success.png showing the sent message.")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        page.screenshot(path="debug_send.png")
        print("Saved debug_send.png so we can see what went wrong.")

    browser.close()
