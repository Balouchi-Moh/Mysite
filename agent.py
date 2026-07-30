import os
import datetime
import google.generativeai as genai

# دریافت کلید گوگل از گیت‌هاب
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate_article():
    # تنظیمات مدل هوش مصنوعی گوگل
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    You are an expert in Civil Engineering, Lean Construction, and Value Engineering.
    Write a 600-word professional article on a random topic related to Lean Construction.
    Format the output ONLY in pure HTML. 
    Include:
    - <h1> for the main title
    - <h2> for subtitles
    - <p> for paragraphs
    Do not use markdown like ```html, just return the raw HTML code without any wrappers.
    """
    
    response = model.generate_content(prompt)
    
    # پاک کردن مارک‌داون‌های احتمالی از جواب گوگل
    html_text = response.text.replace("```html", "").replace("```", "")
    return html_text

today = datetime.datetime.now().strftime("%Y-%m-%d")
article_html = generate_article()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article {today} - Lean Construction</title>
    <link rel="stylesheet" href="../style.css?v=2">
</head>
<body style="padding: 40px; max-width: 800px; margin: auto; font-family: sans-serif; background-color: #F8F9FA;">
    <a href="../index.html" style="color: #C49A6C; text-decoration: none; font-weight: bold;">&larr; Back to Home</a>
    <div style="margin-top: 30px; background: white; padding: 30px; border-radius: 8px; border-top: 4px solid #C49A6C; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        {article_html}
    </div>
</body>
</html>"""

os.makedirs("articles", exist_ok=True)
filename = f"articles/post-{today}.html"

with open(filename, "w", encoding="utf-8") as file:
    file.write(html_content)

print(f"Success! Article {filename} has been created using Google Gemini.")
