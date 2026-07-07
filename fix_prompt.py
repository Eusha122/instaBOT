"""
Attempt to clear the 4415001 'Prompt has contribution' blocker
and access the DM inbox via alternative methods.
"""
import requests
import uuid
import json
import config
from urllib.parse import unquote

session_id = unquote(config.IG_SESSION_ID)
user_id = session_id.split(":")[0]

device_uuid = str(uuid.uuid4())
android_id = f"android-{uuid.uuid4().hex[:16]}"

cookies = {
    "sessionid": session_id,
    "ds_user_id": user_id,
}

mobile_headers = {
    "User-Agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A6003; OnePlus6; qcom; en_US; 314665256)",
    "X-IG-App-ID": "567067343352427",
    "X-IG-Device-ID": device_uuid,
    "X-IG-Android-ID": android_id,
    "X-IG-Capabilities": "3brTvwE=",
    "X-IG-Connection-Type": "WIFI",
    "Accept-Language": "en-US",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

print("=" * 50)
print("Attempt 1: Dismiss inbox prompts via API")
print("=" * 50)

# Try to acknowledge/dismiss the inbox prompt
dismiss_endpoints = [
    ("POST", "https://i.instagram.com/api/v1/direct_v2/inbox_prompts/dismiss/"),
    ("POST", "https://i.instagram.com/api/v1/direct_v2/dismiss_inbox_contribution/"),
    ("POST", "https://i.instagram.com/api/v1/direct_v2/inbox_prompts/"),
]

for method, url in dismiss_endpoints:
    try:
        if method == "POST":
            r = requests.post(url, headers=mobile_headers, cookies=cookies, timeout=10,
                              data={"_uuid": device_uuid})
        else:
            r = requests.get(url, headers=mobile_headers, cookies=cookies, timeout=10)
        print(f"  {method} {url.split('/')[-2]}/  => {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  {method} {url.split('/')[-2]}/  => ERROR: {e}")

print()
print("=" * 50)
print("Attempt 2: Fetch inbox with different params")
print("=" * 50)

# Try inbox with minimal params
param_sets = [
    {"limit": "1"},
    {"visual_message_return_type": "unseen", "limit": "1"},
    {"persistentBadging": "false", "limit": "1"},
    {},
]

for i, params in enumerate(param_sets):
    r = requests.get(
        "https://i.instagram.com/api/v1/direct_v2/inbox/",
        params=params,
        headers=mobile_headers,
        cookies=cookies,
        timeout=15,
    )
    print(f"  Params {params}  => Status: {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            threads = data.get("inbox", {}).get("threads", [])
            print(f"  ✅ WORKS! Found {len(threads)} threads.")
            break
        except:
            print(f"  ✅ Got 200: {r.text[:100]}")
            break
    else:
        try:
            err = r.json()
            print(f"     Error: {err.get('content', {}).get('error_code', 'unknown')}: {err.get('content', {}).get('status', '')}")
        except:
            print(f"     Raw: {r.text[:100]}")

print()
print("=" * 50)
print("Attempt 3: Use direct_v2/threads/ endpoint")
print("=" * 50)

# Try the threads endpoint directly (different from inbox)
r = requests.get(
    "https://i.instagram.com/api/v1/direct_v2/get_presence/",
    headers=mobile_headers,
    cookies=cookies,
    timeout=15,
)
print(f"  get_presence => Status: {r.status_code}")
if r.status_code == 200:
    print(f"  ✅ Presence works: {r.text[:150]}")

# Try pending inbox
r2 = requests.get(
    "https://i.instagram.com/api/v1/direct_v2/pending_inbox/",
    params={"limit": "5"},
    headers=mobile_headers,
    cookies=cookies,
    timeout=15,
)
print(f"  pending_inbox => Status: {r2.status_code}")
if r2.status_code == 200:
    print(f"  ✅ Pending inbox works: {r2.text[:150]}")

print()
print("=" * 50)
print("Attempt 4: Web GraphQL inbox endpoint")
print("=" * 50)

web_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instagram.com/direct/inbox/",
    "X-CSRFToken": "missing",
}

# Try the web-based inbox GraphQL
r3 = requests.get(
    "https://www.instagram.com/api/v1/direct_v2/inbox/",
    params={"limit": "5", "thread_message_limit": "1"},
    headers=web_headers,
    cookies=cookies,
    timeout=15,
)
print(f"  Web inbox => Status: {r3.status_code}")
if r3.status_code == 200:
    try:
        data = r3.json()
        threads = data.get("inbox", {}).get("threads", [])
        print(f"  ✅ WEB INBOX WORKS! Found {len(threads)} threads.")
        if threads:
            t = threads[0]
            print(f"     Thread: {t.get('thread_title', 'N/A')}")
            items = t.get("items", [])
            if items:
                print(f"     Last msg: {items[0].get('text', '(non-text)')}")
    except Exception as e:
        print(f"  Parse error: {e} — raw: {r3.text[:200]}")
else:
    try:
        print(f"  Error: {r3.json()}")
    except:
        print(f"  Raw: {r3.text[:300]}")
