from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from supabase import create_client
import requests
import json
from typing import Optional

app = FastAPI()

# Configurações
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

# ==========================================
# 🔍 FUNÇÃO PARA BUSCAR NA WEB
# ==========================================
def search_web(query: str) -> Optional[str]:
    """Busca informações na web usando a API do Google Custom Search"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        
        if not search_engine_id:
            # Fallback: usar a IA para responder sem busca
            return None
        
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}&num=3"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            resultados = []
            for item in data['items'][:3]:
                resultados.append(f"• {item['title']}: {item['snippet']}")
            return "\n".join(resultados)
        return None
    except Exception as e:
        print(f"Erro na busca web: {e}")
        return None

# ==========================================
# 📊 FUNÇÃO PARA BUSCAR NO BANCO
# ==========================================
def buscar_no_banco(pergunta: str, buffet_id: str) -> Optional[str]:
    """Busca informações no banco de dados"""
    pergunta_lower = pergunta.lower()
    
    try:
        # Clientes
        if "cliente" in pergunta_lower:
            resultado = supabase.table("clients").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return f"📊 O buffet possui {resultado.count} clientes cadastrados."
        
        # Eventos
        elif "evento" in pergunta_lower:
            resultado = supabase.table("events").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return f"📊 O buffet possui {resultado.count} eventos cadastrados."
        
        # Orçamentos
        elif "orçamento" in pergunta_lower or "orcamento" in pergunta_lower:
            resultado = supabase.table("quotes").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return f"📊 O buffet possui {resultado.count} orçamentos cadastrados."
        
        # Faturamento
        elif "faturamento" in pergunta_lower:
            resultado = supabase.table("quotes").select("total_value").eq("buffet_id", buffet_id).eq("status", "fechado").execute()
            total = sum([float(q.get("total_value", 0)) for q in resultado.data])
            return f"💰 O faturamento total do buffet é R$ {total:.2f}"
        
        return None
    except Exception as e:
        print(f"Erro no banco: {e}")
        return None

# ==========================================
# 🚀 ENDPOINT PRINCIPAL
# ==========================================
@app.post("/chat")
async def chat(dados: Pergunta):
    pergunta = dados.pergunta
    buffet_id = dados.buffet_id

    if not buffet_id:
        return {"resposta": "Erro: ID do buffet não informado."}

    # 🔍 1. TENTAR BANCO DE DADOS PRIMEIRO
    resposta_banco = buscar_no_banco(pergunta, buffet_id)
    if resposta_banco:
        return {"resposta": resposta_banco}

    # 🌐 2. TENTAR BUSCA NA WEB
    resposta_web = search_web(pergunta)
    if resposta_web:
        return {"resposta": f"🌐 Encontrei na web:\n\n{resposta_web}"}

    # 🤖 3. USAR A IA PARA RESPONDER
    try:
        prompt = f"""
        O usuário perguntou: {pergunta}
        
        Responda de forma clara, objetiva e amigável.
        Se for uma pergunta sobre churrasco, buffet ou eventos, dê dicas úteis.
        """
        resposta = model.generate_content(prompt)
        return {"resposta": f"🤖 {resposta.text}"}
    except Exception as e:
        return {"resposta": f"⚠️ Não consegui responder. Tente reformular a pergunta."}
