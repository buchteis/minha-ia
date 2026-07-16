from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai
from supabase import create_client
import re

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

@app.post("/chat")
async def chat(dados: Pergunta):
    pergunta = dados.pergunta.lower()
    buffet_id = dados.buffet_id

    if not buffet_id:
        return {"resposta": "Erro: ID do buffet não informado."}

    contexto = ""

    # 🔍 DETECTAR SE É PERGUNTA PARA O BANCO DE DADOS
    is_db_query = any(palavra in pergunta for palavra in [
        "cliente", "clientes", "evento", "eventos", "orçamento", "orcamento",
        "contrato", "contratos", "pagamento", "pagamentos", "faturamento",
        "financeiro", "receita", "agendamento", "agenda"
    ])

    # ==========================================
    # 📊 PESQUISA NO BANCO DE DADOS
    # ==========================================
    if is_db_query:
        try:
            # Clientes
            if "cliente" in pergunta:
                resultado = supabase.table("clients").select("id", count="exact").eq("buffet_id", buffet_id).execute()
                contexto = f"📊 O buffet possui {resultado.count} clientes cadastrados."

            # Eventos
            elif "evento" in pergunta:
                resultado = supabase.table("events").select("id", count="exact").eq("buffet_id", buffet_id).execute()
                contexto = f"📊 O buffet possui {resultado.count} eventos cadastrados."

            # Orçamentos
            elif "orçamento" in pergunta or "orcamento" in pergunta:
                resultado = supabase.table("quotes").select("id", count="exact").eq("buffet_id", buffet_id).execute()
                contexto = f"📊 O buffet possui {resultado.count} orçamentos cadastrados."

            # Faturamento
            elif "faturamento" in pergunta:
                resultado = supabase.table("quotes").select("total_value").eq("buffet_id", buffet_id).eq("status", "fechado").execute()
                total = sum([float(q.get("total_value", 0)) for q in resultado.data])
                contexto = f"💰 O faturamento total do buffet é R$ {total:.2f}"

            return {"resposta": contexto}

        except Exception as e:
            return {"resposta": f"⚠️ Erro ao buscar dados: {str(e)}"}

    # ==========================================
    # 🌐 PESQUISA NA WEB (USANDO GEMINI)
    # ==========================================
    else:
        try:
            # Configuração para buscar na web
            # 🔥 ATENÇÃO: Você precisa ativar o Google Search Grounding no AI Studio
            
            prompt = f"""
            Você é o assistente do Meu Churras.
            Pesquise na internet e responda a seguinte pergunta de forma clara e objetiva:
            
            Pergunta: {dados.pergunta}
            
            Forneça uma resposta com base em informações atualizadas e relevantes.
            Se não encontrar informações, diga que não encontrou.
            """
            
            # Gera resposta usando a IA
            resposta = model.generate_content(prompt)
            return {"resposta": f"🌐 {resposta.text}"}

        except Exception as e:
            # Fallback: tentar responder sem busca
            try:
                resposta = model.generate_content(f"Responda a pergunta: {dados.pergunta}")
                return {"resposta": f"🤖 {resposta.text}"}
            except:
                return {"resposta": "⚠️ Não consegui buscar informações no momento. Tente novamente."}
