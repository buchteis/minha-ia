import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Minha IA Conectada", page_icon="🤖")
st.title("🤖 Minha Primeira IA")
st.write("Conectada e pronta para responder!")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Tentando usar o modelo padrão
    model = genai.GenerativeModel("gemini-1.5-flash")
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
            # SE DER ERRO: O código vai listar os modelos disponíveis na tela!
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                models_text = "\n".join([f"- `{m}`" for m in available_models])
                st.error(f"Erro ao processar. Modelos disponíveis na sua conta:\n\n{models_text}")
            except Exception as list_error:
                st.error(f"Erro crítico: {e}. Não foi possível listar os modelos: {list_error}")
