
import requests
import json
import resend  # ← new: Resend Python SDK

# ── YOUR SETTINGS ──────────────────────────────────────────
GEMINI_API_KEY = "YOUR_GEMINI_KEY"
GNEWS_API_KEY  = "YOUR_GNEWS_KEY"
RESEND_API_KEY = "YOUR_RESEND_KEY"
YOUR_EMAIL     = "csclab51@gmail.com"
SENDER_EMAIL   = "onboarding@resend.dev" # ← Resend's default test sender
CITY           = "CDMX"
LATITUDE       = 19.4326
LONGITUDE      = -99.1332
# ───────────────────────────────────────────────────────────

# 1) Fetch weather (Open-Meteo – no key needed)
def get_weather(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast"
           f"?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
           f"&timezone=auto&forecast_days=1")
    r = requests.get(url, timeout=10).json()
    d = r["daily"]
    return {
        "high_f": round(d["temperature_2m_max"][0] * 9/5 + 32, 1),
        "low_f":  round(d["temperature_2m_min"][0] * 9/5 + 32, 1),
        "rain_chance": d["precipitation_probability_max"][0],
        "code": d["weather_code"][0]
    }

# 2) Fetch top US news headlines (GNews)
def get_news():
    url = (f"https://gnews.io/api/v4/top-headlines"
           f"?category=general&lang=en&country=us"
           f"&max=5&apikey={GNEWS_API_KEY}")
    r = requests.get(url, timeout=10).json()
    return [a["title"] for a in r.get("articles", [])]

# 3) Ask Gemini to write the briefing
def get_briefing(weather, headlines):
    prompt = (
        f"Write a short, friendly morning briefing (in bullets format with max 5 lines) for a resident of {CITY}. "
        f"Today's weather: high {weather['high_f']}°F, low {weather['low_f']}°F, "
        f"rain chance {weather['rain_chance']}%. "
        f"Top news headlines in politics and entertainment for today {DATE} : {json.dumps(headlines)}. "
        f"Be concise, warm, and practical. No preamble."
    )
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
#           f"gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}")
           f"gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=body, timeout=30)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

# 4) Send the email via Resend  ← REPLACED Brevo function
def send_email(subject, body):
    resend.api_key = RESEND_API_KEY
    params = {
        "from": SENDER_EMAIL,
        "to": [YOUR_EMAIL],
        "subject": subject,
        "html": f"<pre>{body}</pre>",
    }
    result = resend.Emails.send(params)
    return result  # returns {"id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"}


# ── MAIN ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching weather…")
    weather = get_weather(LATITUDE, LONGITUDE)
    print(f"  High {weather['high_f']}°F / Low {weather['low_f']}°F")

    print("Fetching news…")
    headlines = get_news()
    print(f"  Got {len(headlines)} headlines")

    print("Generating briefing with Gemini…")
    briefing = get_briefing(weather, headlines)
    print(f"  Done: {briefing[:80]}…")

    print("Sending email…")
    status = send_email("☀️ MY AI Morning Briefing for CDMX", briefing)
    print(f"  Email sent (HTTP {status})")

