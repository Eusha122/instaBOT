import os
import sys
import time
import subprocess
from supabase import create_client, Client
import config

POLL_INTERVAL = 15  # Check for new users every 15 seconds

# Hard cap on simultaneous bots. Each bot is a headless Chromium (~300-400 MB),
# so on a 2 GB server 3 is about the safe ceiling before it runs out of memory
# and freezes. Override with the MAX_BOTS env var if you size up the server.
MAX_BOTS = int(os.getenv("MAX_BOTS", "3"))

# Initialize Supabase client
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Keep track of running subprocesses, keyed by the user's unique DB id (UUID).
# We key on id, not name, so two users with the same display name never collide.
active_bots = {}
# Remember each user's display name (for readable logs) by id.
bot_labels = {}


def cleanup_orphaned_bots():
    """Kill any bot.py processes left over from a previous manager run.

    active_bots lives only in this process's memory, so if the manager was
    restarted, the old bots keep running and we'd spawn duplicates that answer
    the same inbox. Sweep them before we start tracking fresh ones.
    """
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil not installed; skipping orphan cleanup. "
              "Run 'pip install psutil' to enable it.")
        return

    me = psutil.Process().pid
    killed = 0
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if proc.info["pid"] == me:
            continue
        cmdline = proc.info.get("cmdline") or []
        if any("bot.py" in part for part in cmdline) and "--account-id" in cmdline:
            try:
                proc.terminate()
                killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    if killed:
        print(f"🧹 Cleaned up {killed} orphaned bot process(es) from a previous run.")


def start_bot(account_id, account_name):
    print(f"🚀 Launching bot for {account_name} ({account_id})...")
    # Spawn the bot.py script as a background process in headless mode.
    # We pass the UUID as the account id so the bot fetches the exact row.
    process = subprocess.Popen(
        [sys.executable, "bot.py", "--account-id", str(account_id), "--headless"]
    )
    active_bots[account_id] = process
    bot_labels[account_id] = account_name


def main():
    print("👔 Manager started! Watching Supabase for users...")
    print("Press Ctrl+C to stop the manager and all running bots.\n")

    cleanup_orphaned_bots()

    try:
        while True:
            try:
                # 1. Fetch all users from Supabase (id is the stable key; name is for logs)
                response = supabase.table('users').select('id, name').execute()

                if response.data:
                    current_ids = set()

                    # 2. Check each user in the database
                    for user in response.data:
                        user_id = user.get('id')
                        user_name = user.get('name') or '(unnamed)'
                        # Skip rows without an id (should not happen)
                        if not user_id:
                            continue

                        current_ids.add(user_id)

                        if user_id not in active_bots:
                            # Refuse to start more bots than the server can hold.
                            if len(active_bots) >= MAX_BOTS:
                                print(f"\n⚠️ Reached MAX_BOTS ({MAX_BOTS}). NOT starting a bot "
                                      f"for {user_name} ({user_id}) to protect the server's memory. "
                                      f"Raise MAX_BOTS or use a bigger server to run more.")
                                continue
                            # We found a new user! Start a bot for them.
                            print(f"\n✨ New user detected in database: {user_name} ({user_id})")
                            start_bot(user_id, user_name)
                        else:
                            # We already know this user. Let's check if their bot crashed.
                            process = active_bots[user_id]
                            if process.poll() is not None:
                                print(f"\n⚠️ Bot for {user_name} crashed or stopped "
                                      f"(exit code {process.returncode}). Restarting...")
                                start_bot(user_id, user_name)

                    # 3. Check for deleted users (running bots no longer in the DB)
                    bots_to_remove = []
                    for running_id in list(active_bots.keys()):
                        if running_id not in current_ids:
                            label = bot_labels.get(running_id, running_id)
                            print(f"\n🗑️ User '{label}' was deleted from the database. "
                                  f"Stopping their bot...")
                            process = active_bots[running_id]
                            if process.poll() is None:
                                process.terminate()
                            bots_to_remove.append(running_id)

                    for deleted_id in bots_to_remove:
                        del active_bots[deleted_id]
                        bot_labels.pop(deleted_id, None)

            except Exception as e:
                print(f"⚠️ Error polling database: {e}")

            # Wait before checking again
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n👋 Stopping manager...")
        # Terminate all running bots before exiting
        for user_id, process in active_bots.items():
            if process.poll() is None:
                label = bot_labels.get(user_id, user_id)
                print(f"🛑 Terminating bot for {label}...")
                process.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
