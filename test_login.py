"""
Diagnostic script: Tests Instagram session cookie validity using raw HTTP requests.
This bypasses instagrapi entirely to isolate whether the session itself is valid.
Run with: python test_login.py
"""
import requests
import json
import config
from urllib.parse import unquote

print("--- Credential Check ---")
print("Username :", config.IG_USERNAME)
print("Session ID set:", bool(config.IG_SESSION_ID))
print()

session_id = unquote(config.IG_SESSION_ID)
user_id    = session_id.split(":")[0]

print(f"Decoded session ID (first 20 chars): {session_id[:20]} ...")
print(f"Extracted user ID from session: {user_id}")
print()

# --- Test 1: Web API (same as browser) ---
print("--- Test 1: Web API (browser-style request) ---")
web_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "Referer": "https://www.instagram.com/",
}
cookies = {
    "sessionid": session_id,
    "ds_user_id": user_id,
}

resp = requests.get(
    "https://www.instagram.com/api/v1/accounts/current_user/?edit=true",
    headers=web_headers,
    cookies=cookies,
    timeout=15,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    try:
        data = resp.json()
        user = data.get("user", {})
        print(f"✅ Session is VALID!")
        print(f"   Logged in as: {user.get('username', 'N/A')}")
        print(f"   Full name   : {user.get('full_name', 'N/A')}")
        print(f"   User ID     : {user.get('pk', 'N/A')}")
    except Exception:
        print("✅ Got 200 but could not parse JSON:", resp.text[:200])
else:
    print(f"❌ Failed. Response: {resp.text[:300]}")

print()

# --- Test 2: Mobile API (what instagrapi uses) ---
print("--- Test 2: Mobile private API (what instagrapi uses) ---")
import uuid

# --- Test 2 / Test 3 shared headers ---
mobile_headers = {
    "User-Agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A6003; OnePlus6; qcom; en_US; 314665256)",
    "X-IG-App-ID": "567067343352427",
    "X-IG-Device-ID": str(uuid.uuid4()),
    "X-IG-Android-ID": f"android-{uuid.uuid4().hex[:16]}",
    "X-IG-Capabilities": "3brTvwE=",
    "X-IG-Connection-Type": "WIFI",
    "Accept-Language": "en-US",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# --- Test 2: User info endpoint (same as before) ---
print("--- Test 2: Mobile API — user info endpoint ---")
resp2 = requests.get(
    f"https://i.instagram.com/api/v1/users/{user_id}/info/",
    headers=mobile_headers,
    cookies=cookies,
    timeout=15,
)
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    print("✅ User info endpoint works!")
else:
    print(f"❌ Status {resp2.status_code}: {resp2.text[:200]}")

print()

# --- Test 3: DM Inbox endpoint ---
print("--- Test 3: Mobile API — DM inbox endpoint ---")
resp3 = requests.get(
    "https://i.instagram.com/api/v1/direct_v2/inbox/",
    params={
        "visual_message_return_type": "unseen",
        "thread_message_limit": "10",
        "persistentBadging": "true",
        "limit": "20",
    },
    headers=mobile_headers,
    cookies=cookies,
    timeout=15,
)
print(f"Status: {resp3.status_code}")
if resp3.status_code == 200:
    try:
        data = resp3.json()
        threads = data.get("inbox", {}).get("threads", [])
        print(f"✅ DM Inbox accessible! Found {len(threads)} thread(s).")
        if threads:
            last = threads[0].get("items", [{}])[0]
            print(f"   Last message: {last.get('text', '(non-text)')}")
    except Exception as e:
        print("✅ Got 200 but parse error:", e)
else:
    print(f"❌ Inbox blocked (status {resp3.status_code})")
    try:
        print(f"   Error: {resp3.json()}")
    except Exception:
        print(f"   Raw: {resp3.text[:300]}")
