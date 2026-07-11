import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Minha IA Conectada", page_icon="🤖")
st.title("🤖 Minha Primeira IA")
st.write("Conectada e pronta para responder!")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Alterado para o nome clássico aceito em qualquer versão da biblioteca
    model = genai.GenerativeModel(
        "gemini-pro",
        system_instruction=(
            "Você é um assistente com uma personalidade única: sabe ser brincalhão, "
            "espirituoso e usar um toque de humor, mas é extremamente sério, direto, "
            "focado e objetivo ao responder às dúvidas do usuário. Evite enrolação e "
            "vá direto ao ponto com respostas claras, mas mantenha um tom amigável e leve."
        )
    )
except Exception as e:
    st.error("Por favor, configure sua GOOGLE_API_KEY nos Secrets do Streamlit.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Digite sua pergunta aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt)
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
            
