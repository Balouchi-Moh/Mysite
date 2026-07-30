import os
import re
import json
import datetime
import urllib.request

# ---------- دریافت کلید ----------
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: API Key not found.")
    raise SystemExit(1)

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
PROMPT = """
You are an expert in Civil Engineering and Lean Construction.
Write a 600-word professional article on a practical topic related to Lean Construction in the Persian language.
Return ONLY raw HTML. No markdown formatting.
Use <h1> for the title, <h2> for sections, and <p> for paragraphs.
"""

def call_gemini(model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": PROMPT}]}], "generationConfig": {"temperature": 0.8}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["candidates"][0]["content"]["parts"][0]["text"]

# ---------- تولید مقاله ----------
article_html = None
for model in MODELS:
    try:
        raw = call_gemini(model)
        article_html = raw.replace("```html", "").replace("```", "").strip()
        break
    except Exception as e:
        print(f"Failed with {model}: {e}")

if not article_html:
    raise SystemExit(1)

today = datetime.datetime.now().strftime("%Y-%m-%d")

# استخراج عنوان برای استفاده در تب مرورگر
def get_title(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "Lean Construction Article"

def get_excerpt(html):
    m = re.search(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)
    s = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "Latest insights on Lean Construction."
    return (s[:150] + "...") if len(s) > 150 else s

title = get_title(article_html)
excerpt = get_excerpt(article_html)
filename = f"post-{today}.html"

# ---------- ساخت ظاهر صفحه مقاله (با هدر و فوتر) ----------
full_article_page = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Lean Construction</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="site-header">
  <nav class="nav">
    <a class="brand" href="../index.html">
      <span class="brand-mark">MB</span>
      <span class="brand-text"><b>محمد بلوچی</b></span>
    </a>
    <div class="nav-links">
      <a href="../index.html">خانه</a>
      <a href="../blog/index.html">مقالات</a>
    </div>
  </nav>
</header>

<section>
  <div class="wrap">
    <div class="card article" style="margin-top:20px;">
      <a href="../blog/index.html" style="color:#C99145;font-weight:bold;margin-bottom:20px;display:inline-block;">&larr; Back to all articles</a>
      <br>
      {article_html}
    </div>
  </div>
</section>
</body>
</html>"""

os.makedirs("articles", exist_ok=True)
with open(f"articles/{filename}", "w", encoding="utf-8") as f:
    f.write(full_article_page)

# ---------- اضافه کردن مقاله به صفحه اصلی وبلاگ شما (تزریق امن) ----------
new_card = f"""
<!-- AI_AGENT_HOOK -->
<a class="post-card" href="../articles/{filename}">
  <div class="post-body">
    <div class="post-meta">{today} &middot; AI Generated</div>
    <h3>{title}</h3>
    <p>{excerpt}</p>
    <span class="more">Read Article &rarr;</span>
  </div>
</a>
"""

blog_path = "blog/index.html"
if os.path.exists(blog_path):
    with open(blog_path, "r", encoding="utf-8") as f:
        blog_content = f.read()
        
    if "<!-- AI_AGENT_HOOK -->" in blog_content:
        updated_content = blog_content.replace("<!-- AI_AGENT_HOOK -->", new_card)
        with open(blog_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("Success! Article injected into blog/index.html safely.")
    else:
        print("WARNING: <!-- AI_AGENT_HOOK --> not found in blog/index.html. Could not add link.")
