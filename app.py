import streamlit as st
import google.generativeai as genai

# Configuração da página web
st.set_page_config(page_title="Minha IA Conectada", page_icon="🤖")
st.title("🤖 Minha Primeira IA")
st.write("Conectada e pronta para responder!")

# Conexão com a inteligência do Gemini usando a chave segura do painel
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error("Por favor, configure sua GOOGLE_API_KEY nos Secrets do Streamlit.")
    st.stop()

# Inicializa o histórico do chat na tela
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada do usuário
if prompt := st.chat_input("Digite sua pergunta aqui..."):
    # Mostra a pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera e mostra a resposta da IA
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt)
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
