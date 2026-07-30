import os
import datetime
from openai import OpenAI

# دریافت کلید API از تنظیمات مخفی گیت‌هاب
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_article():
    prompt = """
    You are an expert in Civil Engineering, Lean Construction, and Value Engineering.
    Write a 600-word professional article on a random topic related to Lean Construction.
    Format the output ONLY in pure HTML. 
    Include:
    - <h1> for the main title
    - <h2> for subtitles
    - <p> for paragraphs
    Do not use markdown like ```html, just return the raw HTML code.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# دریافت مقاله و تاریخ امروز
today = datetime.datetime.now().strftime("%Y-%m-%d")
article_html = generate_article()

# قالب‌بندی مقاله به عنوان یک صفحه وب کامل
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article {today} - Lean Construction</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body style="padding: 40px; max-width: 800px; margin: auto; font-family: sans-serif;">
    <a href="../index.html" style="color: #C99145; text-decoration: none;">&larr; Back to Home</a>
    <div style="margin-top: 30px;">
        {article_html}
    </div>
</body>
</html>"""

# ساخت پوشه articles (اگر وجود نداشت) و ذخیره فایل
os.makedirs("articles", exist_ok=True)
filename = f"articles/post-{today}.html"

with open(filename, "w", encoding="utf-8") as file:
    file.write(html_content)

print(f"Success! Article {filename} has been created.")
