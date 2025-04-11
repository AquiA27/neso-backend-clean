from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# .env dosyasından anahtarı yükle
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Menü tanımı (kendi kafesinden)
MENU_LISTESI = [
    "Çay", "Fincan Çay", "Sahlep", "Bitki Çayları", "Türk Kahvesi",
    "Osmanlı Kahvesi", "Menengiç Kahvesi", "Süt", "Nescafe",
    "Nescafe Sütlü", "Esspresso", "Filtre Kahve", "Cappuccino",
    "Mocha", "White Mocha", "Classic Mocha", "Caramel Mocha",
    "Latte", "Sıcak Çikolata", "Macchiato"
]

# 🔹 Akıllı ve sınırlı Neso Asistanı
@app.post("/neso")
async def neso_asistan(req: Request):
    try:
        data = await req.json()
        user_text = data.get("text")
        masa = data.get("masa", "bilinmiyor")

        # Menü listesi metin olarak AI'ye gönderilecek şekilde
        menu_metni = ", ".join(MENU_LISTESI)

        system_prompt = {
            "role": "system",
            "content": (
                f"Sen Neso adında kibar, sevimli ve espirili bir restoran yapay zeka asistanısın. "
                f"Aşağıdaki ürünler kafenin menüsüdür. Sadece bu ürünler sipariş edilebilir:\n\n"
                f"{menu_metni}\n\n"
                "Kullanıcının mesajı eğer sipariş içeriyorsa, sadece şu JSON yapısında yanıt ver:\n"
                '{\n  "reply": "Tatlı ve espirili kısa onay mesajı",\n  "sepet": [ { "urun": "ürün adı", "adet": sayı } ]\n}\n\n'
                "Eğer müşteri sohbet ediyorsa (örneğin 'ne içmeliyim?', 'bugün ne önerirsin?'), "
                "sadece öneri ver, samimi ol, emoji kullan. JSON kullanma.\n\n"
                "Eğer müşteri menüde olmayan bir ürün isterse (örneğin 'menemen' veya 'pizza'), "
                "kibarca menüde olmadığını belirt. Sakın uydurma ürün ekleme veya tahminde bulunma."
            )
        }

        user_prompt = {"role": "user", "content": user_text}

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt, user_prompt],
            temperature=0.7
        )

        raw = chat_completion.choices[0].message.content
        print("🔍 OpenAI Yanıtı:", raw)

        # Eğer JSON formatındaysa -> sipariştir
        if raw.strip().startswith("{"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {
                    "reply": "Siparişinizi tam anlayamadım efendim. Menüdeki ürünlerden tekrar deneyebilir misiniz? 🥲",
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
        else:
            # Normal sohbet yanıtı
            return {"reply": raw}

    except Exception as e:
        print("💥 HATA:", e)
        return {"reply": f"Hata oluştu: {str(e)}"}


# 🔁 Eski endpoint alias
@app.post("/sesli-siparis")
async def eski_neso_asistani(req: Request):
    return await neso_asistan(req)


# 🔹 Sipariş geçmişi göster
@app.get("/siparisler")
def get_all_orders():
    try:
        with open("siparisler.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            orders = [json.loads(line) for line in lines]
            return {"orders": orders}
    except FileNotFoundError:
        return {"orders": []}
