import ollama
import requests
import streamlit as st


def chat_with_remote_provider(provider, model, api_key, messages):
    if provider == "OpenAI":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
    elif provider == "Google Gemini":
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
    else:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/streamlit/llm-examples",
            "X-Title": "Streamlit LLM Examples",
        }

    response = requests.post(
        url,
        headers=headers,
        json={"model": model, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


with st.sidebar:
    provider = st.selectbox(
        "Provider",
        options=["Ollama", "OpenAI", "Google Gemini", "OpenRouter"],
        key="chatbot_provider",
    )

    if provider == "Ollama":
        models = []
        try:
            models = [m["model"] for m in ollama.list().get("models", []) if m.get("model")]
        except Exception:
            models = []

        if models:
            default_model = "llama3.1" if "llama3.1" in models else models[0]
            default_index = models.index(default_model)
            model = st.selectbox("Model", options=models, index=default_index, key="chatbot_model")
        else:
            st.info("No local Ollama models found. Pull one with: ollama pull llama3.1")
            model = st.text_input("Model", value="llama3.1", key="chatbot_model")
        api_key = ""
    else:
        default_model = {
            "OpenAI": "gpt-4o-mini",
            "Google Gemini": "gemini-2.0-flash",
            "OpenRouter": "openai/gpt-4o-mini",
        }[provider]
        model = st.text_input("Model", value=default_model, key="chatbot_model")
        api_key = st.text_input(f"{provider} API Key", key="chatbot_api_key", type="password")

    "[Install Ollama](https://ollama.com/download)"
    "[Pull a model](https://ollama.com/library)"
    "[Get an OpenAI API key](https://platform.openai.com/api-keys)"
    "[Get a Gemini API key](https://aistudio.google.com/app/apikey)"
    "[Get an OpenRouter API key](https://openrouter.ai/keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

st.title("💬 Chatbot")
st.caption(f"🚀 A Streamlit chatbot powered by {provider}")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not model:
        st.info("Please provide a model name to continue.")
        st.stop()

    if provider != "Ollama" and not api_key:
        st.info(f"Please add your {provider} API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    try:
        if provider == "Ollama":
            response = ollama.chat(model=model, messages=st.session_state.messages)
            msg = response["message"]["content"]
        else:
            msg = chat_with_remote_provider(provider, model, api_key, st.session_state.messages)
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        st.stop()

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
