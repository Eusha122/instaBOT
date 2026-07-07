"""
Instagram AI Auto-Responder Bot (Playwright Edition)
- Uses a real browser to bypass all bot detection.
- Allows you to MANUALLY log in the first time.
- Saves your session so it can run automatically next time.
"""
import time
import os
import json
import uuid
from playwright.sync_api import sync_playwright
import config

import argparse
from supabase import create_client, Client

# How often to check the inbox, in seconds. Too low gets the account
# rate-limited (HTTP 429) by Instagram, especially with several bots sharing
# one server IP. 12s is a good balance of speed vs. safety once you're not
# double-running bots; raise it back toward 20 if 429s return.
POLL_INTERVAL = 12

# Initialize Supabase client
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def mark_session_invalid(account_id):
    """Flag this user's row so the dashboard can show the session needs refreshing."""
    try:
        supabase.table('users').update({'status': 'session_invalid'}).eq('id', account_id).execute()
        print("🚩 Marked this account's session as invalid in the database.")
    except Exception as e:
        # A missing 'status' column shouldn't crash the bot; just log it.
        print(f"⚠️ Could not update status in database: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run Instagram Bot for a specific account")
    parser.add_argument("--account-id", type=str, required=True, help="Unique ID for this account (e.g., username or UUID)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (required for VPS)")
    return parser.parse_args()

def get_processed_msgs_file(account_id):
    return f"{account_id}_processed_messages.json"

def get_state_file(account_id):
    return f"{account_id}_state.json"

def load_processed_messages(account_id):
    msgs_file = get_processed_msgs_file(account_id)
    if os.path.exists(msgs_file):
        with open(msgs_file, "r") as f:
            return set(json.load(f))
    return set()

def save_processed(msg_id, processed_messages, account_id):
    processed_messages.add(msg_id)
    msgs_file = get_processed_msgs_file(account_id)
    with open(msgs_file, "w") as f:
        json.dump(list(processed_messages), f)

def get_ai_response(user_message, bio, assistant_name, sender_name="", sender_username=""):
    import requests
    url = config.DO_AI_ENDPOINT
    headers = {
        "Authorization": f"Bearer {config.DO_AI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Give the AI the person's name so it can address them naturally.
    # Prefer their first name; fall back to the @username.
    first_name = sender_name.split()[0] if sender_name else ""
    who_line = ""
    if first_name or sender_username:
        label = first_name or sender_username
        handle = f" (@{sender_username})" if sender_username else ""
        who_line = (
            f"- Their name is {label}{handle}. You can address them by their first name "
            f"now and then to feel personal, but don't force it into every message.\n"
        )

    prompt_wrapper = (
        f"You are {assistant_name}, a personal AI assistant that replies to Instagram DMs on behalf "
        f"of your owner. Reply like a real, friendly person texting — warm and easygoing, not stiff "
        f"or one-word, but not over-the-top either.\n\n"
        f"Background about your OWNER (the person you represent):\n{bio}\n\n"
        f"Who you are talking to — READ CAREFULLY:\n"
        f"- The person messaging you is a stranger or friend reaching out. They are NOT your owner.\n"
        f"{who_line}"
        f"- Never assume the person texting is your owner, even if they mention your owner's name.\n"
        f"- If they ask 'who are you' / 'what's your name', say you are {assistant_name}, your owner's "
        f"assistant. Do NOT tell them they are the owner.\n\n"
        f"Rules:\n"
        f"1. Keep it short and natural — usually one sentence, at most one emoji.\n"
        f"2. Be friendly and personable, not dry or robotic. Sound like a real person, not a form.\n"
        f"3. If asked who made or built you, credit ONLY your owner. Do NOT invent or name any other "
        f"people, friends, or collaborators.\n"
        f"4. Don't gush or over-compliment your owner. Mention facts about them only when asked, "
        f"briefly and matter-of-factly.\n"
        f"5. Don't make up facts. If you don't know something, stay casual and vague.\n"
        f"6. Never mention STEM, physics, math, or OneShot AI.\n"
        f"7. Output ONLY the reply text — no quotes, no labels.\n\n"
        f"Their message: '{user_message}'"
    )
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt_wrapper}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling DO_AI API: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. 🤖"

def try_click_by_text(page, texts, timeout=2500):
    """Click the first visible element matching any of the given texts.

    Instagram renders 'Accept', 'Not Now', etc. as div[role=button] or plain
    text, and the exact accessible name varies, so we try both role and text
    matching and accept a substring hit.
    """
    for text in texts:
        for locator in (
            page.get_by_role("button", name=text, exact=True),
            page.get_by_role("button", name=text),
            page.get_by_text(text, exact=True),
        ):
            try:
                if locator.count() > 0 and locator.first.is_visible():
                    locator.first.click(timeout=timeout)
                    return True
            except Exception:
                continue
    return False


def handle_thread_blockers(page):
    """Clear anything covering / replacing the message composer.

    On accounts that receive DMs from people they don't follow, those chats are
    'message requests': Instagram shows Accept/Delete buttons and NO composer at
    all until you accept. Other times a 'Turn on Notifications' popup floats over
    the page. Both stop us from typing a reply.

    Returns True if we accepted a message request (caller should reload the
    composer), False otherwise.
    """
    accepted = False

    # 1. Accept a pending message request. The buttons can take a moment to
    #    render, so retry a few times before giving up.
    for _ in range(3):
        if try_click_by_text(page, ["Accept", "Accept request", "Accept and continue"]):
            print("  [UI] Message request detected — accepting it...")
            accepted = True
            time.sleep(2)
            # Some flows pop a confirmation dialog with a second Accept button.
            try_click_by_text(page, ["Accept", "Confirm"])
            time.sleep(1)
            break
        time.sleep(1)

    # 2. Dismiss common popups that float over the page.
    try_click_by_text(page, ["Not Now", "Not now", "Cancel"])

    return accepted


def try_reply_to_message(page, message_text):
    """Hover the person's message and click Instagram's 'Reply' action so our
    reply is threaded/quoted to that specific message (the 'X replied to your
    message' style). Best-effort — returns False if the UI won't cooperate, and
    the caller then just sends a normal message.
    """
    if not message_text:
        return False
    snippet = message_text[:40]  # long/emoji text can be hard to match in full
    try:
        bubble = page.get_by_text(snippet, exact=False).last
        bubble.scroll_into_view_if_needed()
        bubble.hover()
        time.sleep(0.6)  # let the hover action icons appear
        # Instagram shows a curved-arrow 'Reply' icon on hover. Try a few ways
        # to find it since the markup/labels vary.
        for locator in (
            page.locator('div[role="button"][aria-label="Reply"]'),
            page.locator('[aria-label="Reply"]'),
            page.locator('svg[aria-label="Reply"]'),
            page.get_by_role("button", name="Reply"),
        ):
            try:
                if locator.count() > 0 and locator.last.is_visible():
                    locator.last.click(timeout=2500)
                    time.sleep(0.4)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def send_reply(page, thread_id, text, account_id, reply_to_text=None):
    """Navigate to a chat thread and send one reply. Returns True on success.

    If reply_to_text is given, tries to thread the reply to that specific
    message (Instagram's quote-reply), falling back to a plain message.
    """
    try:
        print(f"  [UI] Navigating to thread {thread_id}...")
        page.goto(f"https://www.instagram.com/direct/t/{thread_id}/", wait_until="networkidle")

        # networkidle already waits for the page to settle;
        # a short pause is enough for the composer to mount.
        time.sleep(1)

        # Clear message-request overlays / popups covering the composer
        handle_thread_blockers(page)

        # Message requests have NO composer until accepted, so if it isn't there,
        # try accepting once more and wait again before giving up.
        message_box = page.locator("div[contenteditable='true'][role='textbox']").first
        try:
            message_box.wait_for(state="visible", timeout=10000)
        except Exception:
            handle_thread_blockers(page)
            message_box.wait_for(state="visible", timeout=8000)

        # Try to quote-reply to their specific message first.
        if reply_to_text and try_reply_to_message(page, reply_to_text):
            print("  [UI] Threaded reply to their message.")

        try:
            message_box.click(timeout=5000)
        except Exception:
            print("  [UI] Composer click intercepted — forcing focus...")
            message_box.click(force=True)
        message_box.fill(text)
        message_box.press("Enter")

        print("✅ Reply sent successfully via UI!")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"⚠️ Failed to send reply via UI: {e}")
        # Save a screenshot so we can see what's actually on screen.
        try:
            shot = f"debug_{account_id}_{thread_id}.png"
            page.screenshot(path=shot)
            print(f"  [debug] Saved screenshot to {shot}")
        except Exception:
            pass
        return False


def parse_proxy(proxy_str):
    """Convert a proxy string into Playwright's proxy dict, or None if empty.

    Accepts the common formats providers hand out:
      http://user:pass@host:port
      socks5://host:port
      host:port:user:pass
      host:port
    """
    if not proxy_str or not str(proxy_str).strip():
        return None
    p = str(proxy_str).strip()

    if "://" in p:
        from urllib.parse import urlparse
        u = urlparse(p)
        cfg = {"server": f"{u.scheme}://{u.hostname}:{u.port}"}
        if u.username:
            cfg["username"] = u.username
        if u.password:
            cfg["password"] = u.password
        return cfg

    parts = p.split(":")
    if len(parts) == 2:
        return {"server": f"http://{parts[0]}:{parts[1]}"}
    if len(parts) == 4:
        host, port, user, pw = parts
        return {"server": f"http://{host}:{port}", "username": user, "password": pw}
    # Unknown shape — assume it's already a usable server string.
    return {"server": p}


def main():
    args = parse_args()
    account_id = args.account_id
    
    print(f"🤖 Fetching data for account: {account_id} from Supabase...")
    # Look up by unique id (UUID), not name, so we always get the exact row.
    response = supabase.table('users').select('*').eq('id', account_id).execute()
    if not response.data:
        print(f"❌ User '{account_id}' not found in Supabase. Exiting.")
        return

    user_data = response.data[0]
    db_session_id = user_data.get('session_id')
    db_bio = user_data.get('bio', '')
    db_assistant_name = user_data.get('assistant_name', 'Assistant')
    account_name = user_data.get('name') or account_id
    proxy_cfg = parse_proxy(user_data.get('proxy'))
    
    print(f"✅ Found user! Starting Playwright Bot for {account_id}...")
    
    processed_messages = load_processed_messages(account_id)
    state_file = get_state_file(account_id)
    
    with sync_playwright() as p:
        # Launch browser (headless for VPS, visible for local debugging).
        # On a small server these flags cut Chromium's memory use a lot and
        # avoid /dev/shm crashes; only applied in headless (VPS) mode.
        launch_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--no-first-run",
            "--mute-audio",
            "--js-flags=--max-old-space-size=256",
        ] if args.headless else []

        launch_kwargs = {"headless": args.headless, "args": launch_args}
        # Route this account's whole browser (page + API calls) through its own
        # proxy, so each account looks like a different IP and they stop sharing
        # one rate-limit bucket. No proxy set = runs direct, like before.
        if proxy_cfg:
            launch_kwargs["proxy"] = proxy_cfg
            print(f"🌐 Using proxy for this account: {proxy_cfg['server']}")

        browser = p.chromium.launch(**launch_kwargs)
        
        # Load saved session if it exists
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1280, "height": 800}
        }
        if os.path.exists(state_file):
            context_args["storage_state"] = state_file
            
        context = browser.new_context(**context_args)
        
        # If no state file, inject cookies from Supabase
        if not os.path.exists(state_file) and db_session_id:
            from urllib.parse import unquote
            session_id = unquote(db_session_id)
            user_id = session_id.split(":")[0]
            context.add_cookies([
                {"name": "sessionid", "value": session_id, "domain": ".instagram.com", "path": "/"},
                {"name": "ds_user_id", "value": user_id, "domain": ".instagram.com", "path": "/"}
            ])
            print("💉 Injected session cookies from Supabase database to bypass login screen.")

        page = context.new_page()

        print("--- Checking Login Status ---")
        page.goto("https://www.instagram.com/direct/inbox/", wait_until="networkidle")

        # Check if we need to log in
        if "accounts/login" in page.url or page.locator("input[name='username']").is_visible():
            if args.headless:
                # On a headless VPS there is no window for the user to log into.
                # A bad/expired session id lands here, so bail out instead of
                # spinning forever and holding a Chromium instance hostage.
                print("\n========================================================")
                print(f"❌ Session for '{account_name}' is invalid or expired.")
                print("   The provided session ID no longer works. Exiting so the")
                print("   user can submit a fresh one.")
                print("========================================================\n")
                mark_session_invalid(account_id)
                context.close()
                browser.close()
                return

            print("\n========================================================")
            print("🛑 YOU NEED TO LOG IN MANUALLY.")
            print("1. Go to the browser window that just opened.")
            print("2. Log in to your Instagram account.")
            print("3. Dismiss any popups (Save Info, Turn on Notifications, etc).")
            print("4. Go to your DM inbox.")
            print("========================================================\n")
            print("Waiting for you to log in...")

            # Wait until the URL changes to the inbox
            while "direct/inbox" not in page.url:
                time.sleep(2)

            print("✅ Detected login! Saving session...")
            context.storage_state(path=state_file)
            print(f"✅ Session saved to {state_file}. You won't have to login next time.")

        print("\n✅ Bot is ACTIVE and monitoring inbox...")

        bot_enabled = True
        # Threads the OTHER person has paused with !stop. The bot stays quiet in
        # these chats until they send !start. Tracked per thread, in memory.
        disabled_threads = set()
        consecutive_html = 0  # count of API calls that returned HTML instead of JSON
        rate_limit_backoff = 0  # grows each time we hit a 429, resets on success
        # On the first successful inbox read we mark everything already there as
        # "seen" without replying, so the bot doesn't answer old chat history.
        # After that, every new message gets a reply — including bursts.
        primed = False

        while True:
            try:
                # 1. Fetch inbox using the browser's own API client
                # This perfectly mimics the website and uses the real TLS fingerprint
                inbox_resp = context.request.get(
                    "https://www.instagram.com/api/v1/direct_v2/inbox/?limit=10",
                    headers={"X-IG-App-ID": "936619743392459"}
                )

                if inbox_resp.status == 429:
                    # Rate limited. Hammering makes it worse, so back off
                    # exponentially: 60s, 120s, 240s ... capped at 15 minutes.
                    rate_limit_backoff = min(rate_limit_backoff + 1, 4)
                    wait = 60 * (2 ** (rate_limit_backoff - 1))
                    wait = min(wait, 900)
                    print(f"⏳ Rate limited by Instagram (429). Backing off for {wait}s. "
                          f"Too many requests from this account/IP.")
                    time.sleep(wait)
                    continue

                if inbox_resp.status != 200:
                    print(f"⚠️ Inbox fetch failed: {inbox_resp.status}")
                    time.sleep(15)
                    continue

                # Reached a good response — reset the backoff.
                rate_limit_backoff = 0

                try:
                    data = inbox_resp.json()
                    consecutive_html = 0
                except Exception:
                    # A 200 with a non-JSON body means Instagram served a web page
                    # (login / challenge / checkpoint) instead of the API response.
                    # Log what it actually is so we can tell why this account fails.
                    consecutive_html += 1
                    body = ""
                    try:
                        body = inbox_resp.text()[:300].replace("\n", " ")
                    except Exception:
                        pass
                    hint = ""
                    low = body.lower()
                    if "login" in low or "loginform" in low:
                        hint = " (looks like a LOGIN page — session is not valid for the API)"
                    elif "challenge" in low or "checkpoint" in low:
                        hint = " (looks like a CHALLENGE/CHECKPOINT — account needs manual verification)"
                    print(f"⚠️ Inbox returned HTML, not JSON [{consecutive_html}]{hint}")
                    print(f"   url={inbox_resp.url}")
                    print(f"   body preview: {body[:180]}")

                    # If it keeps happening, this session simply doesn't work here.
                    if consecutive_html >= 6:
                        print(f"❌ '{account_name}' inbox failed {consecutive_html} times in a row. "
                              f"Marking session invalid and exiting.")
                        mark_session_invalid(account_id)
                        context.close()
                        browser.close()
                        return

                    time.sleep(10)
                    continue
                threads = data.get("inbox", {}).get("threads", [])
                
                my_user_id = data.get("viewer", {}).get("pk")
                if my_user_id:
                    my_user_id = str(my_user_id)
                else:
                    print("⚠️ Could not read your own account id (viewer.pk missing) — "
                          "self-commands like !disablebot may not register this loop.")

                for thread in threads:
                    items = thread.get("items", [])
                    if not items:
                        continue

                    thread_id = thread.get("thread_id", "")

                    # Map each participant's numeric id to their username/name so
                    # we can address the sender by name in replies.
                    thread_users = {
                        str(u.get("pk")): u
                        for u in thread.get("users", [])
                        if u.get("pk")
                    }

                    # Go oldest -> newest so we reply in the order messages arrived.
                    # The inbox returns items newest-first, hence reversed().
                    for item in reversed(items):
                        msg_id = item.get("item_id", "")
                        if not msg_id or msg_id in processed_messages:
                            continue

                        # First successful poll: mark everything as seen without
                        # replying, so we don't answer old backlog on startup.
                        if not primed:
                            save_processed(msg_id, processed_messages, account_id)
                            continue

                        sender_id = str(item.get("user_id", ""))
                        item_type = item.get("item_type", "")

                        # Only text messages can be replied to; mark the rest seen.
                        if item_type != "text":
                            save_processed(msg_id, processed_messages, account_id)
                            continue

                        msg_text = item.get("text", "").strip()

                        # Commands from your own account (global on/off).
                        # Normalize hard: phone keyboards auto-capitalize and may
                        # add stray spaces/punctuation.
                        if sender_id == my_user_id:
                            cmd = "".join(c for c in msg_text.lower() if c.isalnum() or c == "!")
                            if cmd.startswith("!"):
                                print(f"  [cmd] Detected command from your account: '{msg_text}' -> parsed '{cmd}'")
                            if cmd in ("!disablebot", "!disable", "!stopbot", "!stop"):
                                bot_enabled = False
                                print("🔴 Bot DISABLED via command.")
                            elif cmd in ("!enablebot", "!enable", "!startbot", "!start"):
                                bot_enabled = True
                                print("🟢 Bot ENABLED via command.")
                            save_processed(msg_id, processed_messages, account_id)
                            continue

                        # The person you're chatting with can pause/resume the bot
                        # for THIS conversation only by sending !stop / !start.
                        other_cmd = "".join(c for c in msg_text.lower() if c.isalnum() or c == "!")
                        if other_cmd in ("!stop", "!stopbot", "!disable", "!disablebot"):
                            disabled_threads.add(thread_id)
                            print(f"🔕 {sender_id} sent !stop — pausing bot for this chat only.")
                            save_processed(msg_id, processed_messages, account_id)
                            continue
                        if other_cmd in ("!start", "!startbot", "!enable", "!enablebot"):
                            disabled_threads.discard(thread_id)
                            print(f"🔔 {sender_id} sent !start — resuming bot for this chat.")
                            save_processed(msg_id, processed_messages, account_id)
                            continue

                        # Stay quiet if globally disabled or this chat is paused.
                        if not bot_enabled or thread_id in disabled_threads:
                            save_processed(msg_id, processed_messages, account_id)
                            continue

                        # Reply to this message. Each message gets its own reply,
                        # so a burst of 2-3 messages gets 2-3 answers in order.
                        sender_info = thread_users.get(sender_id, {})
                        sender_username = sender_info.get("username", "")
                        sender_name = sender_info.get("full_name", "")
                        who = sender_name or sender_username or sender_id
                        print(f"\n📨 New message from {who}: {msg_text}")
                        ai_reply = get_ai_response(
                            msg_text, db_bio, db_assistant_name,
                            sender_name=sender_name, sender_username=sender_username,
                        )
                        print(f"🤖 Replying: {ai_reply[:100]}...")

                        if send_reply(page, thread_id, ai_reply, account_id, reply_to_text=msg_text):
                            save_processed(msg_id, processed_messages, account_id)

                # After the first full pass, start replying to genuinely new messages.
                if not primed:
                    primed = True
                    print("✅ Primed: existing messages marked as seen. Now replying to new ones.")

                # Sleep before checking again
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                print("\n\n👋 Bot stopped by user. Goodbye!")
                break
            except Exception as e:
                print(f"⚠️ Error in polling loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    main()
