from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# .env dosyasından API anahtarını yükle
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# Frontend ile backend iletişimi için CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Ana Neso Asistan Endpoint'i
@app.post("/neso")
async def neso_asistan(req: Request):
    try:
        data = await req.json()
        user_text = data.get("text")
        masa = data.get("masa", "bilinmiyor")

        # Neso'nun karakter tanımı ve JSON zorlaması
  system_prompt = {
    "role": "system",
    "content": (
        "Sen Neso adında bir restoran yapay zeka asistanısın. Müşteri sana yazılı olarak hem sohbet edebilir, hem sipariş verebilir. Gelen mesaja göre davran:\n\n"
        "Eğer mesaj sipariş içeriyorsa, aşağıdaki JSON yapısını kesinlikle kullanarak yanıt ver:\n"
        '{\n  "reply": "Tatlı ve espirili onay mesajı",\n  "sepet": [ { "urun": "ürün adı", "adet": sayı } ]\n}\n\n'
        "Eğer mesaj sadece sohbet, tavsiye veya öneri içeriyorsa (örneğin 'Ne önerirsin?', 'Bugün ne var?', 'Hoş geldin'), o zaman JSON kullanma ve sadece sevecen, emoji içeren tatlı bir cümle döndür.\n"
        "Açıklama, etiket veya format dışında herhangi bir ek metin kullanma. Gereksiz bilgi verme. Sipariş dışı yanıtlar sadece kısa, karakterli cümlelerden oluşsun."
    )
}


        user_prompt = {"role": "user", "content": user_text}

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt, user_prompt],
            temperature=0.8
        )

        raw = chat_completion.choices[0].message.content
        print("🔍 OpenAI Yanıtı:", raw)

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            json_text = raw[start:end]
            parsed = json.loads(json_text)
        except json.JSONDecodeError as e:
            print("❌ JSON Parse Hatası:", e)
            parsed = {
                "reply": "Siparişiniz alındı ama ürünleri anlayamadım.",
                "sepet": []
            }

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
        print("💥 Genel Hata:", e)
        return {"reply": f"Hata oluştu: {str(e)}"}


# 🔁 Eski endpoint için alias (önceki frontend ile uyumluluk)
@app.post("/sesli-siparis")
async def eski_neso_asistani(req: Request):
    return await neso_asistan(req)


# 🔹 Sipariş geçmişi endpoint'i
@app.get("/siparisler")
def get_all_orders():
    try:
        with open("siparisler.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            orders = [json.loads(line) for line in lines]
            return {"orders": orders}
    except FileNotFoundError:
        return {"orders": []}
