"""
Test sending a DM using the Instagram Web GraphQL API.
This is exactly what the modern Instagram website uses in the browser.
"""
import requests
import uuid
import config
import json
from urllib.parse import unquote

if not config.IG_SESSION_ID:
    print("❌ No IG_SESSION_ID set in .env")
    exit()

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

# 1. Fetch CSRF Token
print("--- Step 1: Getting CSRF token ---")
r1 = requests.get(
    "https://www.instagram.com/data/shared_data/",
    headers=headers,
    cookies=cookies,
    allow_redirects=False,
    timeout=15,
)
csrf = r1.cookies.get("csrftoken")
if not csrf:
    r1 = requests.get(
        "https://www.instagram.com/direct/inbox/",
        headers=headers,
        cookies=cookies,
        allow_redirects=False,
        timeout=15,
    )
    csrf = r1.cookies.get("csrftoken")

print(f"CSRF Token: {csrf}")
if not csrf:
    print("❌ Failed to get CSRF token.")
    exit()

cookies["csrftoken"] = csrf
headers["X-CSRFToken"] = csrf
print()

# 2. Get inbox to find a thread ID
print("--- Step 2: Fetching inbox ---")
r2 = requests.get(
    "https://www.instagram.com/api/v1/direct_v2/inbox/",
    params={"limit": "5"},
    headers=headers,
    cookies=cookies,
    allow_redirects=False,
    timeout=15,
)

if r2.status_code in (301, 302):
    print("❌ Session is INVALID (Redirected to login). You need a fresh sessionid cookie!")
    exit()

if r2.status_code != 200:
    print(f"❌ Failed to fetch inbox: {r2.status_code}")
    exit()

try:
    data = r2.json()
except Exception:
    print("❌ Failed to parse JSON (Response was HTML)")
    exit()

threads = data.get("inbox", {}).get("threads", [])
if not threads:
    print("❌ No threads found in inbox.")
    exit()

thread_id = threads[0].get("thread_id")
print(f"✅ Found thread ID: {thread_id}")
print()

# 3. Send message using GraphQL
print("--- Step 3: Sending message via GraphQL ---")
test_msg = "Hello! This is a test from the GraphQL bot 🤖"
headers["Referer"] = f"https://www.instagram.com/direct/t/{thread_id}/"
headers["X-FB-Friendly-Name"] = "usePolarisIGDMSendDirectMsgMutation"
headers["X-Bloks-Version-Id"] = "9876fa521f73602d3824edbbfdb54f767a6d8fc532edef12f9166f3fb8fdb7ba" # Hardcoded known version or can be omitted

variables = {
    "input": {
        "text": test_msg,
        "thread_id": thread_id,
        "offline_threading_id": str(uuid.uuid4().int)[:19],
        "client_mutation_id": str(uuid.uuid4()),
    }
}

r3 = requests.post(
    "https://www.instagram.com/api/graphql",
    headers=headers,
    cookies=cookies,
    data={
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "usePolarisIGDMSendDirectMsgMutation",
        "variables": json.dumps(variables),
        "doc_id": "7242898289101966",
    },
    allow_redirects=False,
    timeout=15,
)

print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    print("✅ GraphQL Request Succeeded!")
    try:
        print(r3.json())
    except:
        print(r3.text[:300])
else:
    print(f"❌ Failed! Headers: {r3.headers}")
    try:
        print(r3.json())
    except:
        print(r3.text[:500])
