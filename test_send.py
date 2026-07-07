"""
Test sending a DM using a proper requests.Session with domain-aware cookies.
This captures ALL cookies from Instagram's responses (not just sessionid).
"""
import requests
import uuid
import config
from urllib.parse import unquote

session_id = unquote(config.IG_SESSION_ID)
user_id = session_id.split(":")[0]

print(f"User ID: {user_id}")
print(f"Session ID: {session_id[:20]}...")
print()

# Create a proper session with domain-aware cookies
s = requests.Session()
s.cookies.set("sessionid", session_id, domain=".instagram.com", path="/")
s.cookies.set("ds_user_id", user_id, domain=".instagram.com", path="/")

s.headers.update({
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
    "Referer": "https://www.instagram.com/direct/inbox/",
})

# Step 1: Load the main page to establish all cookies
print("--- Step 1: Loading Instagram main page for cookies ---")
r1 = s.get("https://www.instagram.com/", allow_redirects=True, timeout=15)
print(f"  Status: {r1.status_code}")
print(f"  Cookies after page load: {list(s.cookies.keys())}")
print()

# Step 2: Fetch inbox
print("--- Step 2: Fetching DM inbox ---")
r2 = s.get(
    "https://www.instagram.com/api/v1/direct_v2/inbox/",
    params={"limit": "5", "thread_message_limit": "1"},
    timeout=15,
)
print(f"  Status: {r2.status_code}")
if r2.status_code != 200:
    print(f"  Error: {r2.text[:200]}")
    exit()

try:
    data = r2.json()
    threads = data.get("inbox", {}).get("threads", [])
    print(f"  Found {len(threads)} threads")
    print(f"  Cookies now: {list(s.cookies.keys())}")
except Exception as e:
    print(f"  ❌ Failed to parse JSON. Response was likely HTML.")
    print(f"  Preview: {r2.text[:500]}")
    exit()

csrf = s.cookies.get("csrftoken")
print(f"  CSRF token: {csrf[:15] if csrf else 'NOT FOUND'}...")
print()

if not threads:
    print("No threads to test with!")
    exit()

# Pick the first thread
thread = threads[0]
thread_id = thread.get("thread_id")
thread_title = thread.get("thread_title", "unknown")
print(f"  Target thread: {thread_title} (ID: {thread_id})")
print()

# Step 3: Try sending a message
print("--- Step 3: Sending test message ---")
test_msg = "Hello! This is a test from the bot 🤖"

send_resp = s.post(
    "https://www.instagram.com/api/v1/direct_v2/threads/broadcast/text/",
    headers={
        "X-CSRFToken": csrf,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"https://www.instagram.com/direct/t/{thread_id}/",
    },
    data={
        "action": "send_item",
        "thread_ids": f"[{thread_id}]",
        "client_context": str(uuid.uuid4()),
        "text": test_msg,
    },
    allow_redirects=False,
    timeout=15,
)

print(f"  Status: {send_resp.status_code}")
if send_resp.status_code == 200:
    print(f"  ✅ MESSAGE SENT SUCCESSFULLY!")
    print(f"  Response: {send_resp.json()}")
elif send_resp.status_code in (301, 302):
    print(f"  ❌ Redirected to: {send_resp.headers.get('Location')}")
    print(f"  All cookies sent: {dict(s.cookies)}")
else:
    try:
        print(f"  ❌ Error: {send_resp.json()}")
    except:
        print(f"  ❌ Raw: {send_resp.text[:300]}")

print()

# Step 4: Try alternative — use the GraphQL endpoint 
print("--- Step 4: Try GraphQL send ---")
import json

gql_resp = s.post(
    "https://www.instagram.com/api/graphql",
    headers={
        "X-CSRFToken": csrf,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"https://www.instagram.com/direct/t/{thread_id}/",
        "X-FB-Friendly-Name": "usePolarisIGDMSendDirectMsgMutation",
    },
    data={
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "usePolarisIGDMSendDirectMsgMutation",
        "variables": json.dumps({
            "input": {
                "text": test_msg,
                "thread_id": thread_id,
                "offline_threading_id": str(uuid.uuid4().int)[:19],
                "client_mutation_id": str(uuid.uuid4()),
            }
        }),
        "doc_id": "7242898289101966",
    },
    allow_redirects=False,
    timeout=15,
)

print(f"  Status: {gql_resp.status_code}")
if gql_resp.status_code == 200:
    print(f"  ✅ GraphQL SEND WORKED!")
    try:
        print(f"  Response: {gql_resp.json()}")
    except:
        print(f"  Raw: {gql_resp.text[:300]}")
elif gql_resp.status_code in (301, 302):
    print(f"  ❌ Redirected: {gql_resp.headers.get('Location')}")
else:
    try:
        print(f"  ❌ Error: {gql_resp.json()}")
    except:
        print(f"  ❌ Raw: {gql_resp.text[:300]}")
