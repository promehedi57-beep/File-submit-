import asyncio
import uuid
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI(title="Advanced Hotmail Extractor")

# ==========================================
# 1. ফ্রন্টএন্ড (Advanced UI with Proxy Support)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Hotmail Extractor</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #1e1e2f; color: #fff; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .container { background: #2a2a40; padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.5); width: 100%; max-width: 450px; }
        h2 { text-align: center; color: #00d2ff; margin-bottom: 25px; font-size: 24px; }
        label { font-size: 14px; color: #aaa; margin-bottom: 5px; display: block; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; background: #1e1e2f; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; }
        input:focus { outline: none; border-color: #00d2ff; }
        button { width: 100%; padding: 14px; background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        .result { margin-top: 20px; padding: 15px; background: #1e1e2f; border-left: 4px solid #00d2ff; word-wrap: break-word; font-family: monospace; display: none; border-radius: 4px; font-size: 13px; color: #00ffcc; }
        .loader { display: none; margin-top: 15px; color: #00d2ff; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Advanced Extractor Pro</h2>
        
        <label>Hotmail Email</label>
        <input type="email" id="email" placeholder="example@hotmail.com" required>
        
        <label>Password</label>
        <input type="password" id="password" placeholder="Enter password" required>
        
        <label>Proxy (Optional for testing, Required for Bulk)</label>
        <input type="text" id="proxy" placeholder="http://user:pass@ip:port">
        
        <button onclick="generateToken()">Initialize Extraction</button>
        
        <div class="loader" id="loader">Bypassing Security & Logging in... ⏳</div>
        <div class="result" id="resultBox"></div>
    </div>

    <script>
        async function generateToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const proxy = document.getElementById('proxy').value;
            const resultBox = document.getElementById('resultBox');
            const loader = document.getElementById('loader');

            if(!email || !password) return alert("Email and Password are required!");

            resultBox.style.display = 'none';
            loader.style.display = 'block';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, proxy })
                });
                
                const data = await response.json();
                loader.style.display = 'none';
                
                if(data.status === 'success') {
                    resultBox.innerText = data.data;
                    resultBox.style.display = 'block';
                    resultBox.style.borderLeftColor = '#00ffcc';
                } else {
                    resultBox.innerText = "❌ Error: " + data.detail;
                    resultBox.style.display = 'block';
                    resultBox.style.borderLeftColor = '#ff4d4d';
                    resultBox.style.color = '#ff4d4d';
                }
            } catch (err) {
                loader.style.display = 'none';
                resultBox.innerText = "❌ Connection Failed!";
                resultBox.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 2. ব্যাকএন্ড (Stealth & Proxy Logic)
# ==========================================
class UserData(BaseModel):
    email: str
    password: str
    proxy: str = None

@app.get("/")
async def get_ui():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/generate")
async def generate_token(data: UserData):
    async with async_playwright() as p:
        # ব্রাউজারকে আসল মানুষের মতো দেখানোর জন্য Stealth Arguments
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
        
        # প্রক্সি সেটআপ (যদি ইউজার প্রক্সি দেয়)
        proxy_settings = None
        if data.proxy:
            proxy_settings = {"server": data.proxy}

        try:
            # Headless True রেখেই অ্যান্টি-বট বাইপাসের চেষ্টা
            browser = await p.chromium.launch(
                headless=True,
                args=browser_args,
                proxy=proxy_settings
            )
            
            # রিয়েল ডিভাইসের User-Agent ব্যবহার করা
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            # মাইক্রোসফট যেন বুঝতে না পারে যে এটি বট, তাই কিছু জাভাস্ক্রিপ্ট ইনজেক্ট করা
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = await context.new_page()

            await page.goto("https://login.live.com/")
            await page.fill('input[name="loginfmt"]', data.email)
            await page.click('input[type="submit"]')
            
            # মানুষের মতো রিয়েলিস্টিক ডিলে (Delay) দেওয়া
            await page.wait_for_timeout(3000) 
            
            await page.fill('input[name="passwd"]', data.password)
            await page.click('input[type="submit"]')
            
            # সফল লগইন যাচাই
            await page.wait_for_url("**/mail/**", timeout=20000)
            
            cookies = await context.cookies()
            token = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                
            await browser.close()
            
            unique_id = str(uuid.uuid4())
            formatted_data = f"{data.email}|{data.password}|{token.strip()}|{unique_id}"
            
            return {"status": "success", "data": formatted_data}
            
        except Exception as e:
            if 'browser' in locals():
                await browser.close()
            return {"status": "error", "detail": "সিকিউরিটি ব্লক করেছে বা প্রক্সি কাজ করছে না।"}
