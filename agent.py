import os
import json
import datetime
import urllib.request
import urllib.error

# ---------- 1) خواندن کلید (با چند نام جایگزین) ----------
api_key = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("GOOGLE_API_KEY")
)

if not api_key:
    print("=" * 60)
    print("ERROR: کلید گوگل پیدا نشد!")
    print("لطفاً در Settings > Secrets and variables > Actions")
    print("یک Secret به نام دقیقِ GEMINI_API_KEY بسازید")
    print("و کلیدی که از aistudio.google.com گرفتید را در آن بگذارید.")
    print("=" * 60)
    raise SystemExit(1)

# ---------- 2) لیست مدل‌ها به ترتیب اولویت ----------
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-1.5-flash",
]

PROMPT = """
You are an expert in Civil Engineering, Lean Construction and Value Engineering.
Write a 600-word professional article on ONE random practical topic inside Lean Construction.
Return ONLY raw HTML, no markdown fences, no explanations.
Use exactly these tags: one <h1> title, two or three <h2> subtitles, several <p> paragraphs, and one <ul> with 3 bullet points.
"""

def call_gemini(model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {"temperature": 0.9},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["candidates"][0]["content"]["parts"][0]["text"]

# ---------- 3) امتحان مدل‌ها یکی یکی ----------
article_html = None
last_error = None
for model in MODELS:
    try:
        print(f"Trying model: {model} ...")
        raw = call_gemini(model)
        article_html = raw.replace("```html", "").replace("```", "").strip()
        print(f"OK with model: {model}")
        break
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        last_error = f"HTTP {e.code} on {model}: {detail}"
        print(last_error)
    except Exception as e:
        last_error = f"Error on {model}: {e}"
        print(last_error)

if not article_html:
    print("=" * 60)
    print("ERROR: هیچ مدلی پاسخ نداد. آخرین خطا:")
    print(last_error)
    print("=" * 60)
    raise SystemExit(1)

# ---------- 4) ساخت صفحه مقاله ----------
today = datetime.datetime.now().strftime("%Y-%m-%d")
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Article {today} - Lean Construction</title>
<link rel="stylesheet" href="../style.css?v=3">
</head>
<body style="padding:40px;max-width:800px;margin:auto;background:#F5F6F7;font-family:sans-serif;">
<a href="../index.html" style="color:#C99145;font-weight:bold;text-decoration:none;">&larr; Back to Home</a>
<div style="margin-top:30px;background:#fff;padding:34px;border-radius:9px;border-top:4px solid #C99145;box-shadow:0 8px 24px rgba(29,45,70,.07);">
{article_html}
</div>
</body>
</html>"""

os.makedirs("articles", exist_ok=True)
filename = f"articles/post-{today}.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"SUCCESS: {filename} created.")
