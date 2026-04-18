import asyncio
import uuid
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI(title="Hotmail Token Extractor")

# ==========================================
# 1. ফ্রন্টএন্ড (ওয়েবসাইটের ইউজার ইন্টারফেস)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotmail Extractor</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 50px; background-color: #f4f4f9; }
        .container { max-width: 500px; margin: auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #0078D4; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #005a9e; }
        .result { margin-top: 20px; padding: 15px; background: #e7f3fe; border-left: 6px solid #2196F3; word-wrap: break-word; font-family: monospace; display: none; border-radius: 4px; }
        .loader { display: none; margin-top: 15px; color: #0078D4; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Hotmail Token Extractor</h2>
        <input type="email" id="email" placeholder="ইমেইল (Hotmail/Outlook)" required>
        <input type="password" id="password" placeholder="পাসওয়ার্ড" required>
        <button onclick="generateToken()">Extract Token</button>
        
        <div class="loader" id="loader">অপেক্ষা করুন, ব্যাকগ্রাউন্ডে লগইন হচ্ছে... ⏳</div>
        <div class="result" id="resultBox"></div>
    </div>

    <script>
        async function generateToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const resultBox = document.getElementById('resultBox');
            const loader = document.getElementById('loader');

            if(!email || !password) {
                alert("দয়া করে ইমেইল এবং পাসওয়ার্ড দিন!");
                return;
            }

            // আগের রেজাল্ট লুকিয়ে লোডার দেখানো
            resultBox.style.display = 'none';
            loader.style.display = 'block';

            try {
                // পাইথন ব্যাকএন্ডে ডেটা পাঠানো
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                loader.style.display = 'none';
                
                if(data.status === 'success') {
                    resultBox.innerText = data.data; // সফল হলে শুধু ডেটা দেখাবে
                    resultBox.style.display = 'block';
                    resultBox.style.background = '#e7f3fe';
                    resultBox.style.borderLeftColor = '#2196F3';
                } else {
                    resultBox.innerText = "❌ এরর: " + data.detail;
                    resultBox.style.display = 'block';
                    resultBox.style.background = '#ffebee';
                    resultBox.style.borderLeftColor = '#f44336';
                }
            } catch (err) {
                loader.style.display = 'none';
                resultBox.innerText = "❌ সার্ভার এরর! স্ক্রিপ্ট ঠিকমতো রান হচ্ছে কিনা চেক করুন।";
                resultBox.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 2. ব্যাকএন্ড (অটোমেশন লজিক)
# ==========================================
class UserData(BaseModel):
    email: str
    password: str

@app.get("/")
async def get_ui():
    # ইউজার ওয়েবসাইট ভিজিট করলে উপরের HTML ডিজাইনটি দেখাবে
    return HTMLResponse(content=HTML_PAGE)

@app.post("/generate")
async def generate_token(data: UserData):
    email = data.email
    password = data.password
    
    async with async_playwright() as p:
        # ব্রাউজার ব্যাকগ্রাউন্ডে চলবে (headless=True)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://login.live.com/")
            
            # ইমেইল দেওয়া
            await page.fill('input[type="email"]', email)
            await page.click('input[type="submit"]')
            await page.wait_for_timeout(2000) # ২ সেকেন্ড অপেক্ষা
            
            # পাসওয়ার্ড দেওয়া
            await page.fill('input[type="password"]', password)
            await page.click('input[type="submit"]')
            
            # ইনবক্সে যাওয়ার জন্য অপেক্ষা (সর্বোচ্চ ১৫ সেকেন্ড)
            await page.wait_for_url("**/mail/**", timeout=15000)
            
            # কুকি সংগ্রহ করা
            cookies = await context.cookies()
            token = ""
            for cookie in cookies:
                token += f"{cookie['name']}={cookie['value']}; "
                
            await browser.close()
            
            # আইডি জেনারেট এবং আপনার নির্দিষ্ট ফরম্যাটে সাজানো
            unique_id = str(uuid.uuid4())
            formatted_data = f"{email}|{password}|{token.strip()}|{unique_id}"
            
            return {"status": "success", "data": formatted_data}
            
        except Exception as e:
            await browser.close()
            return {"status": "error", "detail": "লগইন ফেইল হয়েছে বা সিকিউরিটি চেক চেয়েছে।"}
