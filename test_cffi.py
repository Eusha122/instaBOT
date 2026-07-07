"""
Test sending a DM using curl_cffi to spoof a real Chrome browser's TLS fingerprint.
Instagram is likely detecting the default Python 'requests' TLS fingerprint and 
killing the session when you try to POST a message.
"""
from curl_cffi import requests
import uuid
import config
import json
from urllib.parse import unquote
import sys

if not config.IG_SESSION_ID:
    print("❌ No IG_SESSION_ID set in .env")
    sys.exit(1)

session_id = unquote(config.IG_SESSION_ID)
user_id = session_id.split(":")[0]

cookies = {
    "sessionid": session_id,
    "ds_user_id": user_id,
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.instagram.com",
}

print(f"User ID: {user_id}")
print(f"Session ID: {session_id[:20]}...")
print()

# Use curl_cffi to impersonate Chrome 120
s = requests.Session(impersonate="chrome120")
s.cookies.update(cookies)
s.headers.update(headers)

# 1. Fetch CSRF Token
print("--- Step 1: Getting CSRF token ---")
r1 = s.get("https://www.instagram.com/data/shared_data/", allow_redirects=False)
csrf = s.cookies.get("csrftoken")
if not csrf:
    r1 = s.get("https://www.instagram.com/direct/inbox/", allow_redirects=False)
    csrf = s.cookies.get("csrftoken")

print(f"CSRF Token: {csrf}")
if not csrf:
    print("❌ Failed to get CSRF token.")
    sys.exit(1)

s.headers.update({"X-CSRFToken": csrf})
print()

# 2. Get inbox to find a thread ID
print("--- Step 2: Fetching inbox ---")
r2 = s.get(
    "https://www.instagram.com/api/v1/direct_v2/inbox/",
    params={"limit": "5"},
    allow_redirects=False
)

if r2.status_code in (301, 302):
    print("❌ Session is INVALID (Redirected to login). You need a fresh sessionid cookie!")
    sys.exit(1)

try:
    data = r2.json()
except Exception:
    print("❌ Failed to parse JSON (Response was HTML). Session likely dead.")
    sys.exit(1)

threads = data.get("inbox", {}).get("threads", [])
if not threads:
    print("❌ No threads found in inbox.")
    sys.exit(1)

thread_id = threads[0].get("thread_id")
print(f"✅ Found thread ID: {thread_id}")
print()

# 3. Send message using Web REST API (which works in curl_cffi usually)
print("--- Step 3: Sending message ---")
test_msg = "Hello! This is a test from the stealth bot 🤖"
s.headers.update({
    "Referer": f"https://www.instagram.com/direct/t/{thread_id}/",
    "Content-Type": "application/x-www-form-urlencoded",
})

r3 = s.post(
    "https://www.instagram.com/api/v1/direct_v2/threads/broadcast/text/",
    data={
        "action": "send_item",
        "thread_ids": f"[{thread_id}]",
        "client_context": str(uuid.uuid4()),
        "text": test_msg,
    },
    allow_redirects=False
)

print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    print("✅ Request Succeeded! Message Sent.")
    try:
        print(r3.json())
    except:
        print(r3.text[:300])
else:
    print(f"❌ Failed! Status: {r3.status_code}")
    try:
        print(r3.json())
    except:
        print(r3.text[:500])
