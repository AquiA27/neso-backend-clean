from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

# Ortam değişkeni yükleme
from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

# CORS ayarları (gerekirse frontend adresinle sınırlandır)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# İstek modeli
class Siparis(BaseModel):
    mesaj: str

@app.post("/sesli-siparis")
async def sesli_siparis(siparis: Siparis):
    kullanici_mesaji = siparis.mesaj

    # NESO'nun kişiliği burada tanımlanıyor:
    system_message = {
        "role": "system",
        "content": """
        Sen Neso adında bir yapay zeka restorant asistanısın. Kibar, espirili, insana güven veren bir tarzda konuşursun.
        Her siparişe emoji ile tatlı bir yorum yapar, müşteriye değerli olduğunu hissettirirsin.
        Siparişleri tekrar ederek onaylarsın, bazen kısaca "Afiyet olsun!" veya "Nefis bir seçim!" gibi yorumlar yaparsın.
        Sipariş dışı sorulara sadece restoran hakkında bilgi verirsin.
        """
    }

    user_message = {"role": "user", "content": kullanici_mesaji}

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.8
        )
        cevap = completion.choices[0].message.content.strip()
        return {"yanit": cevap}

    except Exception as e:
        return {"yanit": f"Bir hata oluştu: {str(e)}"}
