import os
import re
import glob
import json
import datetime
import urllib.request
import urllib.error

# ---------- 1) کلید گوگل ----------
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY در Secrets پیدا نشد.")
    raise SystemExit(1)

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]

PROMPT = """
You are an expert in Civil Engineering, Lean Construction and Value Engineering.
Write a 600-word professional article on ONE random practical topic inside Lean Construction.
Return ONLY raw HTML, no markdown fences, no explanations.
Use exactly: one <h1> title, two or three <h2> subtitles, several <p> paragraphs, and one <ul> with 3 bullet points.
"""

def call_gemini(model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": PROMPT}]}], "generationConfig": {"temperature": 0.9}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["candidates"][0]["content"]["parts"][0]["text"]

# ---------- 2) تولید مقالهٔ امروز ----------
article_html, last_error = None, None
for model in MODELS:
    try:
        print("Trying model:", model)
        raw = call_gemini(model)
        article_html = raw.replace("```html", "").replace("```", "").strip()
        print("OK with model:", model)
        break
    except Exception as e:
        last_error = str(e)
        print("Failed:", last_error)

if not article_html:
    print("ERROR: no model responded. Last error:", last_error)
    raise SystemExit(1)

today = datetime.datetime.now().strftime("%Y-%m-%d")

# ساختار صفحه مقاله (لینک برگشت به فولدر blog آپدیت شد)
article_page = (
    "<!DOCTYPE html>\n<html lang=\"en\" dir=\"ltr\">\n<head>\n"
    "<meta charset=\"UTF-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    "<title>Article " + today + " - Lean Construction</title>\n"
    "<link rel=\"stylesheet\" href=\"../style.css?v=5\">\n</head>\n"
    "<body style=\"padding:40px 20px;background:#F5F6F7;\">\n"
    "<div class=\"article\" style=\"margin:0 auto;\">\n"
    "<a href=\"../blog/index.html\" style=\"color:#C99145;font-weight:700;\">&larr; All Articles</a>\n"
    + article_html +
    "\n</div>\n</body>\n</html>"
)

# ذخیره مقاله در پوشه articles
os.makedirs("articles", exist_ok=True)
article_path = "articles/post-" + today + ".html"
with open(article_path, "w", encoding="utf-8") as f:
    f.write(article_page)
print("Saved article:", article_path)

# ---------- 3) ابزارهای استخراج عنوان و چکیده ----------
def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    return re.sub(r"\s+", " ", t).strip()

def get_title(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    return clean(m.group(1)) if m else "Lean Construction Insight"

def get_excerpt(html):
    m = re.search(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)
    s = clean(m.group(1)) if m else "Read the latest AI-generated insight on Lean Construction and Value Engineering."
    return (s[:170] + "…") if len(s) > 170 else s

def pretty(ymd):
    try:
        return datetime.datetime.strptime(ymd, "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return ymd

# ---------- 4) ساخت کارت‌ها از مقاله‌های موجود ----------
files = sorted(glob.glob("articles/post-*.html"), reverse=True)
cards = ""
for fp in files:
    base = os.path.basename(fp)            
    ymd = base.replace("post-", "").replace(".html", "")
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    title = get_title(html)
    excerpt = get_excerpt(html)
    date_pretty = pretty(ymd)
    # آدرس‌دهی از پوشه blog به پوشه articles
    href = "../articles/" + base
    cards += (
        "\n<a class=\"post-card\" href=\"" + href + "\">\n"
        "  <div class=\"post-thumb\"></div>\n"
        "  <div class=\"post-body\">\n"
        "    <div class=\"post-meta\">" + date_pretty + " &middot; AI Generated</div>\n"
        "    <h3>" + title + "</h3>\n"
        "    <p>" + excerpt + "</p>\n"
        "    <span class=\"more\">Read Article &rarr;</span>\n"
        "  </div>\n</a>\n"
    )

# ---------- 5) بازسازی index.html داخل فولدر blog ----------
blog_template = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>مقالات | محمد بلوچی - ساخت ناب</title>
<!-- بازگشت به مسیر اصلی برای لود استایل -->
<link rel="stylesheet" href="../style.css?v=5">
<style>
@media(max-width:860px){
  .nav-links{display:flex !important;position:static;flex-direction:row;flex-wrap:wrap;
    background:transparent;border:0;box-shadow:none;padding:0;gap:4px;}
  .nav-toggle{display:none !important;}
}
</style>
</head>
<body>
<header class="site-header">
  <nav class="nav">
    <a class="brand" href="../index.html">
      <span class="brand-mark">MB</span>
      <span class="brand-text"><b>محمد بلوچی</b><span>Lean Construction Consultant</span></span>
    </a>
    <div class="nav-links">
      <a href="../index.html">خانه</a>
      <a href="../services.html">خدمات</a>
      <a href="../resume.html">رزومه</a>
      <a href="index.html" class="active">مقالات</a>
    </div>
  </nav>
</header>

<section>
  <div class="wrap">
    <div class="section-head">
      <div class="eyebrow">AI KNOWLEDGE BASE</div>
      <h1 class="section-title">مقالات روزانهٔ ساخت ناب و مهندسی ارزش</h1>
      <p class="section-sub">این فهرست هر روز به‌صورت خودکار توسط یک عامل هوش مصنوعی به‌روزرسانی می‌شود. جدیدترین مقاله در صدر قرار دارد.</p>
    </div>
    <div class="grid-3">__CARDS__</div>
  </div>
</section>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <a class="brand" href="../index.html">
        <span class="brand-mark">MB</span>
        <span class="brand-text"><b>محمد بلوچی</b><span>Lean Construction Consultant</span></span>
      </a>
      <div class="footer-links">
        <a href="../index.html">خانه</a>
        <a href="../services.html">خدمات</a>
        <a href="../resume.html">رزومه</a>
        <a href="index.html">مقالات</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; __YEAR__ Lean Construction</span>
      <span>Auto-published by AI Agent</span>
    </div>
  </div>
</footer>
</body>
</html>"""

year = datetime.datetime.now().strftime("%Y")
blog_html = blog_template.replace("__CARDS__", cards).replace("__YEAR__", year)

# ایجاد فولدر blog (در صورت عدم وجود) و ذخیره index.html داخل آن
os.makedirs("blog", exist_ok=True)
with open("blog/index.html", "w", encoding="utf-8") as f:
    f.write(blog_html)
print("Rebuilt blog/index.html with", len(files), "article(s).")
