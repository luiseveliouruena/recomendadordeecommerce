from fastapi  import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from recommender.recommender import recommend, similar_items, search_products  # <-- Cambiado aquí
from fastapi import Request


app = FastAPI(title="E-commerce Recs (mínimo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    row = products[products["product_id"] == product_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Not found")
    return row.iloc[0].to_dict()

@app.get("/recommend/user/{user_id}")
def rec_user(user_id: int, k: int = 5):
    return {"items": recommend(user_id, k=k)}  # <-- Cambiado aquí

@app.get("/recommend/similar/{product_id}")
def rec_sim(product_id: int, k: int = 5):
    return {"items": similar_items(product_id, k=k)}

@app.get("/search")
def search(q: str = Query(..., min_length=1), k: int = 10):
    return {"items": search_products(q, k=k)}

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "").lower()
        user_id = data.get("user_id", 1)

        # Recomendar productos al usuario
        if "recomienda" in msg or "sugerencia" in msg or "recomiéndame" in msg:
            recs = recommend(user_id, k=3)
            nombres = [r["title"] for r in recs]
            reply = "Te recomiendo: " + ", ".join(nombres) if nombres else "No tengo recomendaciones para ti ahora."
            return {"reply": reply}

        # Buscar productos similares a un producto dado
        if "similar" in msg:
            import re
            match = re.search(r"(\d+)", msg)
            if match:
                pid = int(match.group(1))
                recs = similar_items(pid, k=3)
                nombres = [r["title"] for r in recs]
                reply = f"Productos similares a {pid}: " + ", ".join(nombres) if nombres else "No encontré productos similares."
                return {"reply": reply}

        # Buscar productos por texto
        if "buscar" in msg or "busca" in msg:
            import re
            q = msg.split("buscar")[-1].strip() or msg.split("busca")[-1].strip()
            if q:
                recs = search_products(q, k=3)
                nombres = [r["title"] for r in recs]
                reply = f"Resultados para '{q}': " + ", ".join(nombres) if nombres else f"No encontré productos para '{q}'."
                return {"reply": reply}

        # Mostrar información de un producto específico
        if "producto" in msg:
            import re
            match = re.search(r"producto\s*(\d+)", msg)
            if match:
                pid = int(match.group(1))
                prod = products[products["product_id"] == pid]
                if not prod.empty:
                    p = prod.iloc[0]
                    reply = f"Producto {pid}: {p['title']} - {p['description']}"
                else:
                    reply = f"No encontré el producto {pid}."
                return {"reply": reply}

        # Respuesta por defecto
        return {"reply": "Hola, soy tu asistente de e-commerce. Puedes pedirme recomendaciones, buscar productos o preguntar por productos similares."}
    except Exception as e:
        # Esto asegura que siempre se responde con CORS aunque haya error
        return {"reply": f"Ocurrió un error interno: {str(e)}"}