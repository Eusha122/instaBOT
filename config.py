import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Instagram Credentials
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_SESSION_ID = os.getenv("IG_SESSION_ID")  # Preferred: avoids password-based login

# DO_AI Credentials
DO_AI_ENDPOINT = os.getenv("DO_AI_ENDPOINT")
DO_AI_API_KEY = os.getenv("DO_AI_API_KEY")
# Which model to send in the API request. Leave EMPTY for DigitalOcean GenAI
# agents — they use the model configured in the DO dashboard and reject an
# unknown model name. Only set this if your endpoint expects an explicit model.
DO_AI_MODEL = os.getenv("DO_AI_MODEL", "")

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

