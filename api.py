from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai
from supabase import create_client

app = FastAPI()

# Configurações
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Modelo da IA
model = genai.GenerativeModel(
    "gemini-3.5-flash",
    system_instruction="""
    Você é um assistente especializado em interpretar perguntas sobre um sistema de buffet.
    Sua função é entender o que o usuário quer saber e extrair a intenção.
    """
)

class Pergunta(BaseModel):
    pergunta: str
    buffet_id: str

@app.post("/chat")
async def chat(dados: Pergunta):
    pergunta = dados.pergunta
    buffet_id = dados.buffet_id

    if not buffet_id:
        return {"resposta": "Erro: ID do buffet não informado."}

    # ==========================================
    # 🤖 USAR IA PARA INTERPRETAR A PERGUNTA
    # ==========================================
    try:
        # 1. A IA interpreta a pergunta e decide o que buscar
        prompt_interpretacao = f"""
        Analise a pergunta do usuário e determine qual informação ele quer do sistema.

        Pergunta: "{pergunta}"

        Responda APENAS com uma das opções abaixo:
        - CLIENTES: se perguntar sobre quantidade de clientes
        - EVENTOS: se perguntar sobre quantidade de eventos
        - ORCAMENTOS: se perguntar sobre quantidade de orçamentos
        - FATURAMENTO: se perguntar sobre faturamento ou valores
        - CONTRATOS: se perguntar sobre contratos
        - PAGAMENTOS: se perguntar sobre pagamentos pendentes
        - DESCONHECIDO: se não for sobre nenhum desses assuntos

        Resposta: """

        resposta_ia = model.generate_content(prompt_interpretacao)
        tipo = resposta_ia.text.strip().upper()

        # 2. Buscar no banco de dados baseado na interpretação
        if tipo == "CLIENTES":
            resultado = supabase.table("clients").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return {"resposta": f"📊 O buffet possui {resultado.count} clientes cadastrados."}

        elif tipo == "EVENTOS":
            resultado = supabase.table("events").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return {"resposta": f"📊 O buffet possui {resultado.count} eventos cadastrados."}

        elif tipo == "ORCAMENTOS":
            resultado = supabase.table("quotes").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return {"resposta": f"📊 O buffet possui {resultado.count} orçamentos cadastrados."}

        elif tipo == "FATURAMENTO":
            resultado = supabase.table("quotes").select("total_value").eq("buffet_id", buffet_id).eq("status", "fechado").execute()
            total = sum([float(q.get("total_value", 0)) for q in resultado.data])
            return {"resposta": f"💰 O faturamento total do buffet é R$ {total:.2f}"}

        elif tipo == "CONTRATOS":
            resultado = supabase.table("contracts").select("id", count="exact").eq("buffet_id", buffet_id).execute()
            return {"resposta": f"📄 O buffet possui {resultado.count} contratos cadastrados."}

        elif tipo == "PAGAMENTOS":
            resultado = supabase.table("transactions").select("id", count="exact").eq("buffet_id", buffet_id).eq("status", "pendente").execute()
            return {"resposta": f"💰 O buffet possui {resultado.count} pagamentos pendentes."}

        else:
            return {"resposta": f"🤔 Não entendi sua pergunta. Você pode perguntar sobre:\n• Clientes\n• Eventos\n• Orçamentos\n• Faturamento\n• Contratos\n• Pagamentos"}

    except Exception as e:
        return {"resposta": f"⚠️ Erro ao processar sua pergunta: {str(e)}"}
