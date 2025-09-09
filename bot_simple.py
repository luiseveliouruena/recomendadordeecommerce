# bot_simple.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, re, requests

REC_API_BASE = os.environ.get("REC_API_BASE", "http://localhost:8000")

app = FastAPI(title="Mini Bot E-commerce")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

class Msg(BaseModel):
    message: str
    user_id: int | None = 1

def _first_int(text: str) -> int | None:
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None

def _classify(text: str):
    t = text.lower()
    if any(b in t for b in ["hola", "buenas", "buenos días", "buenas tardes"]):
        return ("greet", None)
    if "recommend" in t or "suger" in t:
        return ("ask_recommendations", None)
    if "similar" in t or "parecid" in t:
        return ("ask_similar", _first_int(t))
    if "inform" in t or "detalle" in t or "producto" in t:
        return ("ask_product_info", _first_int(t))
    return ("fallback", None)


@app.post("/chat")
def chat(msg: Msg):
    intent, num = _classify(msg.message)
    try:
        if intent == "greet":
            return {"reply": "Hola! Soy tu asistente de compras. Puedo recomendarte productos, mostrar similares o dar info de un producto."}

        if intent == "ask_recommendations":
            r = requests.get(f"{REC_API_BASE}/recommend/{msg.user_id}", timeout=5)
            items = r.json()
            txt = "Te recomiendo: " + ", ".join([f"{it['product_id']} [{it['title']}] - ${it['price']}" for it in items])
            return {"reply": txt}

        if intent == "ask_similar" and num:
            r = requests.get(f"{REC_API_BASE}/similar/{num}", timeout=5)
            items = r.json()
            txt = "Similares: " + ", ".join([f"{it['product_id']} [{it['title']}] - ${it['price']}" for it in items])
            return {"reply": txt}

        if intent == "ask_product_info" and num:
            r = requests.get(f"{REC_API_BASE}/products/{num}", timeout=5)
            it = r.json()[0]
            txt = f"Producto {it['product_id']}: {it['title']} - ${it['price']}"
            return {"reply": txt}

        return {"reply": "No entendí. Puedo hacer 'recomiéndame productos', 'productos similares al 3' o 'información del producto 2'."}

    except Exception as e:
        return {"reply": f"Tu API no respondió ({e}). ¿Está corriendo en {REC_API_BASE}?"}

