import base64
import io

import ollama
import requests
import streamlit as st

try:
    from streamlit_paste_button import paste_image_button
except ModuleNotFoundError:
    paste_image_button = None


def model_likely_supports_images(provider, model):
    if not model:
        return False

    model_lower = model.lower()
    if provider == "Ollama":
        vision_hints = ["vision", "llava", "bakllava", "moondream", "minicpm-v", "qwen2.5-vl"]
        return any(hint in model_lower for hint in vision_hints)

    # Most modern default models for these providers are multimodal, but users can choose text-only models.
    text_only_hints = ["gpt-3.5", "instruct", "text-"]
    return not any(hint in model_lower for hint in text_only_hints)


def build_provider_messages(provider, messages):
    if provider == "Ollama":
        formatted = []
        for message in messages:
            item = {"role": message["role"], "content": message.get("content", "")}
            if message.get("images"):
                item["images"] = [img["data"] for img in message["images"]]
            formatted.append(item)
        return formatted

    formatted = []
    for message in messages:
        if message.get("images"):
            content = []
            text = message.get("content", "")
            if text:
                content.append({"type": "text", "text": text})
            for image in message["images"]:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image['mime_type']};base64,{image['data']}",
                        },
                    }
                )
            if not content:
                content.append({"type": "text", "text": "Describe this image."})
            formatted.append({"role": message["role"], "content": content})
        else:
            formatted.append({"role": message["role"], "content": message.get("content", "")})
    return formatted


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
            preferred_defaults = ["llama3.2-vision", "llava", "llava:latest", "bakllava", "moondream"]
            default_model = next((m for m in preferred_defaults if m in models), models[0])
            default_index = models.index(default_model)
            model = st.selectbox("Model", options=models, index=default_index, key="chatbot_model")
        else:
            st.info("No local Ollama models found. Pull one with: ollama pull llama3.1")
            model = st.text_input("Model", value="llama3.2-vision", key="chatbot_model")
        st.caption("For image prompts with Ollama, use a vision model (for example: llama3.2-vision or llava).")
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
if "chatbot_upload_key" not in st.session_state:
    st.session_state["chatbot_upload_key"] = 0
if "chatbot_clipboard_images" not in st.session_state:
    st.session_state["chatbot_clipboard_images"] = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("content"):
            st.write(msg["content"])
        for image in msg.get("images", []):
            st.image(base64.b64decode(image["data"]))

if paste_image_button is None:
    st.info("Optional dependency missing: install streamlit-paste-button to use the clipboard paste button.")
else:
    paste_result = paste_image_button(
        label="Paste image from clipboard",
        key="chatbot_paste_button",
    )
    if paste_result.image_data is not None:
        image_buffer = io.BytesIO()
        paste_result.image_data.save(image_buffer, format="PNG")
        st.session_state["chatbot_clipboard_images"].append(
            {
                "mime_type": "image/png",
                "data": base64.b64encode(image_buffer.getvalue()).decode("utf-8"),
            }
        )
        st.success("Pasted image added to your next message.")

if st.session_state["chatbot_clipboard_images"]:
    st.caption(
        f"{len(st.session_state['chatbot_clipboard_images'])} clipboard image(s) ready for your next message."
    )
    preview_cols = st.columns(min(3, len(st.session_state["chatbot_clipboard_images"])))
    for idx, image in enumerate(st.session_state["chatbot_clipboard_images"]):
        with preview_cols[idx % len(preview_cols)]:
            st.image(base64.b64decode(image["data"]))
    if st.button("Clear pasted images", key="chatbot_clear_clipboard_images"):
        st.session_state["chatbot_clipboard_images"] = []
        st.rerun()

using_chat_input_files = True
try:
    chat_payload = st.chat_input(
        "Type a message, or paste/drop image(s)",
        accept_file="multiple",
        file_type=["png", "jpg", "jpeg", "webp", "gif"],
    )
except TypeError:
    using_chat_input_files = False
    st.info("Your Streamlit version does not support image paste in chat input. Use the uploader below or upgrade Streamlit.")
    uploaded_images = st.file_uploader(
        "Attach image(s) for your next message",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        key=f"chatbot_images_{st.session_state['chatbot_upload_key']}",
    )
    if uploaded_images:
        st.caption(f"{len(uploaded_images)} image(s) ready to send.")
    chat_payload = st.chat_input("Type a message")

prompt = ""
if using_chat_input_files:
    uploaded_images = []
if chat_payload is not None:
    if isinstance(chat_payload, str):
        prompt = chat_payload
    elif isinstance(chat_payload, dict):
        prompt = chat_payload.get("text", "") or ""
        uploaded_images = chat_payload.get("files", []) or []
    else:
        prompt = getattr(chat_payload, "text", "") or ""
        uploaded_images = list(getattr(chat_payload, "files", []) or [])

if chat_payload is not None:
    if not prompt and not uploaded_images:
        if not st.session_state["chatbot_clipboard_images"]:
            st.info("Please enter a message or attach at least one image.")
            st.stop()

    message_images = []
    if uploaded_images:
        message_images.extend(
            [
                {
                    "mime_type": image.type or "image/png",
                    "data": base64.b64encode(image.getvalue()).decode("utf-8"),
                }
                for image in uploaded_images
                if image.getvalue()
            ]
        )
    message_images.extend(st.session_state["chatbot_clipboard_images"])
    if not prompt and not message_images:
        st.info("Please enter a message or attach at least one image.")
        st.stop()

    if not model:
        st.info("Please provide a model name to continue.")
        st.stop()

    if provider != "Ollama" and not api_key:
        st.info(f"Please add your {provider} API key to continue.")
        st.stop()

    if message_images and not model_likely_supports_images(provider, model):
        st.error(
            f"The selected model '{model}' may not support images. Please switch to a vision-capable model and try again."
        )
        st.stop()

    user_message = {"role": "user", "content": prompt}
    if message_images:
        user_message["images"] = message_images

    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        if prompt:
            st.write(prompt)
        for image in user_message.get("images", []):
            st.image(base64.b64decode(image["data"]))

    provider_messages = build_provider_messages(provider, st.session_state.messages)
    try:
        if provider == "Ollama":
            response = ollama.chat(model=model, messages=provider_messages)
            msg = response["message"]["content"]
        else:
            msg = chat_with_remote_provider(provider, model, api_key, provider_messages)
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        st.stop()

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

    if uploaded_images and not using_chat_input_files:
        st.session_state["chatbot_upload_key"] += 1
    st.session_state["chatbot_clipboard_images"] = []
    if uploaded_images and not using_chat_input_files:
        st.rerun()
