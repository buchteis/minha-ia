from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai
from supabase import create_client

app = FastAPI()

# Configurações
genai.configure(
    api_key=os.getenv("GOOGLE_API_KEY")
)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

model = genai.GenerativeModel(
    "gemini-3.5-flash",
    system_instruction="""
    Você é o assistente inteligente do Meu Churras.
    Responda de forma clara, objetiva e amigável.
    Ajude o dono do buffet com informações do sistema.
    """
)


class Pergunta(BaseModel):
    pergunta: str
    buffet_id: str


@app.post("/chat")
async def chat(dados: Pergunta):

    pergunta = dados.pergunta.lower()
    buffet_id = dados.buffet_id

    contexto = ""

    # Clientes
    if "cliente" in pergunta:
        resultado = (
            supabase
            .table("clients")
            .select("id", count="exact")
            .eq("buffet_id", buffet_id)
            .execute()
        )

        contexto = f"O buffet possui {resultado.count} clientes cadastrados."


    # Eventos
    elif "evento" in pergunta:
        resultado = (
            supabase
            .table("events")
           
