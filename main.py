from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# .env dosyasındaki anahtarı yükle
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI istemcisi
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# CORS ayarı: frontend ile backend konuşabilsin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Neso AI Asistan Endpoint'i
@app.post("/neso")
async def neso_asistan(req: Request):
    try:
        data = await req.json()
        user_text = data.get("text")
        masa = data.get("masa", "bilinmiyor")

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen Neso adında bir restoran sipariş asistanısın. "
                        "Kullanıcının Türkçe siparişini al ve sadece aşağıdaki JSON yapısında cevap ver:\n\n"
                        "{\n"
                        '  "reply": "Müşteriye kısa yanıt",\n'
                        '  "sepet": [\n'
                        '    { "urun": "ürün adı", "adet": sayı }\n'
                        "  ]\n"
                        "}\n\n"
                        "Sadece bu yapıyı üret. Açıklama ekleme."
                    )
                },
                {"role": "user", "content": user_text}
            ]
        )

        raw = chat_completion.choices[0].message.content

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"reply": "Siparişiniz alındı ama ürünleri anlayamadım.", "sepet": []}

        siparis = {
            "masa": masa,
            "istek": user_text,
            "yanit": parsed.get("reply", ""),
            "sepet": parsed.get("sepet", []),
            "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open("siparisler.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(siparis, ensure_ascii=False) + "\n")

        return {"reply": parsed.get("reply", "")}

    except Exception as e:
        return {"reply": f"Hata oluştu: {str(e)}"}

# 🔹 Sipariş listesini döndür
@app.get("/siparisler")
def get_all_orders():
    try:
        with open("siparisler.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            orders = [json.loads(line) for line in lines]
            return {"orders": orders}
    except FileNotFoundError:
        return {"orders": []}
