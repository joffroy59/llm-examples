import ollama
import streamlit as st

with st.sidebar:
    models = []
    try:
        models = [m["model"] for m in ollama.list().get("models", []) if m.get("model")]
    except Exception:
        models = []

    if models:
        default_model = "llama3.1" if "llama3.1" in models else models[0]
        default_index = models.index(default_model)
        ollama_model = st.selectbox("Ollama model", options=models, index=default_index, key="chatbot_model")
    else:
        st.info("No local Ollama models found. Pull one with: ollama pull llama3.1")
        ollama_model = st.text_input("Ollama model", value="llama3.1", key="chatbot_model")
    "[Install Ollama](https://ollama.com/download)"
    "[Pull a model](https://ollama.com/library)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by Ollama")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not ollama_model:
        st.info("Please provide an Ollama model name to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = ollama.chat(model=ollama_model, messages=st.session_state.messages)
    msg = response["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
