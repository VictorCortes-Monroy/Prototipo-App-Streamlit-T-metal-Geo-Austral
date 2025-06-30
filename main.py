from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
import httpx

load_dotenv()


app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
print("SUPABASE_URL ->", SUPABASE_URL)
print("API_KEY ->", SUPABASE_API_KEY)

SUPABASE_TABLE = "eventos_gps"
@app.post("/webhook")
async def recibir_datos(request: Request):
    data = await request.json()

    payload = {
        "event_time": data.get("event_time"),
        "system_time": data.get("system_time"),
        "imei": data.get("imei"),
        "vid": data.get("vid"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "velocidad": data.get("velocidad")
    }

    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "prefer": "return=minimal"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/eventos_gps",
            headers=headers,
            json=payload,
            timeout=10
        )

    return {"status": "ok", "supabase_status": response.status_code, "text": response.text}

