from dotenv import load_dotenv
import os

import requests
from openai import OpenAI

# Load .env variables
load_dotenv()

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")  # Add this to .env to fix 401 errors
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-lite-001")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
) if api_key else None

print(f"=== Smart Retail OpenRouter Smoke Test ===")
print(f"Targeting Model: {model}")

# Setup headers for authenticated requests
headers = {}
if AUTH_TOKEN:
    headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

if client:
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print("✅ OpenRouter API connection successful!")
        print("Response:", completion.choices[0].message.content)
    except Exception as e:
        print("❌ OpenRouter API call failed:", e)
else:
    print("❌ No OPENROUTER_API_KEY found in .env")

for endpoint in [
    "/api/analytics/overview",
    "/api/analytics/dashboard-summary",
    "/api/analytics/alerts",
    "/api/analytics/test-openai",
]:
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=20)
        response.raise_for_status()
        print(f"✅ {endpoint} ->", response.json())
    except Exception as exc:
        print(f"❌ {endpoint} failed:", exc)

try:
    response = requests.post(
        f"{BASE_URL}/api/analytics/ask",
        json={"question": "What is happening in the store right now?"},
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    print("✅ /api/analytics/ask ->", response.json())
except Exception as exc:
    print("❌ /api/analytics/ask failed:", exc)