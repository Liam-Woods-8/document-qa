import sys


try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

import os
import chromadb 
from chromadb.utils import embedding_functions
import streamlit as st
from openai import OpenAI
import anthropic
import fitz  # PyMuPDF

# pdf extraction
def extract_text_from_pdf(uploaded_pdf) -> str:
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return 



# lab 3 part b + c
def conversation_buffer(messages, keep_user_message=2):
    if not messages:
        return messages

    # keep system prompt
    system = []
    if messages[0]["role"] == "system":
        system = [messages[0]]

    # find user messages
    user_indices = [i for i, m in enumerate(messages) if m["role"] == "user"]

    # if <= 2 user messages, keep all
    if len(user_indices) <= keep_user_message:
        return messages

    # keep last 2 user turns + responses
    start_index = user_indices[-keep_user_message]
    return system + messages[start_index:]


# lab 4 - RAG
def create_lab4_vectordb(pdf_folder: str):
    client = chromadb.PersistentClient(path="./chroma_lab4")

    embed_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=st.secrets["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )

    collection = client.get_or_create_collection(
        name="Lab4Collection",
        embedding_function=embed_fn,
    )

    existing = set(collection.get(include=[])["ids"])

    for filename in os.listdir(pdf_folder):
        if not filename.lower().endswith(".pdf"):
            continue

        if filename in existing:
            continue

        with open(os.path.join(pdf_folder, filename), "rb") as f:
            text = extract_text_from_pdf(f)

        collection.add(
            ids=[filename],
            documents=[text],
            metadatas=[{"source": filename}],
        )

    return collection

st.title("Lab 4 – RAG")

# NAV 
page = st.sidebar.radio("Navigation", ["Summary", "Chatbot"])

language = st.sidebar.selectbox("Language", ("English", "Spanish", "French", "Russian"))

summary_type = st.sidebar.selectbox(
    "Summary type",
    (
        "Summarize the document in 100 words",
        "Summarize the document in 2 connecting paragraphs",
        "Summarize the document in 5 bullet points",
    ),
)

use_advanced_model = st.sidebar.checkbox("Use advanced model")

openai_api_key = st.secrets["OPENAI_API_KEY"]
claude_api_key = st.secrets["CLAUDE_API_KEY"]

uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

document_text = ""
if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)

instructions = f"{summary_type}. Write the summary in {language}."

SYSTEM_PROMPT = (
    "You are a helpful chatbot. "
    "Explain things so a 10-year-old can understand. "
    "After you answer, you must ask: 'Do you want more info?' "
    "If the user says yes, give more information (still for a 10-year-old) "
    "and then ask again: 'Do you want more info?' "
    "If the user says no, say: 'Okay—what can I help you with?'"
)

# SUMMARY PAGE
if page == "Summary":
    if uploaded_file:
        if not use_advanced_model:
            client = OpenAI(api_key=openai_api_key)

            messages = [
                {
                    "role": "user",
                    "content": f"{instructions}\n\nHere's a document:\n{document_text}",
                }
            ]

            stream = client.chat.completions.create(
                model="gpt-5-chat-latest",
                messages=messages,
                stream=True,
            )

            st.write_stream(stream)

        else:
            client = anthropic.Anthropic(api_key=claude_api_key)

            messages_to_llm = [
                {
                    "role": "user",
                    "content": f"{instructions}\n\nHere's a document:\n{document_text}",
                }
            ]

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0,
                messages=messages_to_llm,
            )

            st.markdown(response.content[0].text)
    else:
        st.info("Upload a PDF to generate a summary.")

# CHATBOT PAGE 
elif page == "Chatbot":
    if not uploaded_file:
        st.info("Upload a PDF to chat about it.")
    else:
        if "client" not in st.session_state:
            st.session_state.client = OpenAI(api_key=openai_api_key)

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "How can I help you?"}
            ]

        if "awaiting_more_info" not in st.session_state:
            st.session_state.awaiting_more_info = False

        st.session_state.messages = conversation_buffer(
            st.session_state.messages, keep_user_message=2
        )

        for msg in st.session_state.messages:
            if msg["role"] == "system":
                continue
            chat_msg = st.chat_message(msg["role"])
            chat_msg.write(msg["content"])

        if prompt := st.chat_input("What is up?"):
            normalized = prompt.strip().lower()

            if st.session_state.awaiting_more_info and normalized in ["no", "n", "nope", "nah"]:
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                assistant_text = "Okay—what can I help you with?"

                with st.chat_message("assistant"):
                    st.markdown(assistant_text)

                st.session_state.messages.append({"role": "assistant", "content": assistant_text})

                st.session_state.awaiting_more_info = False

                st.session_state.messages = conversation_buffer(
                    st.session_state.messages, keep_user_message=2
                )

            else:
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                buffered_history = conversation_buffer(
                    st.session_state.messages, keep_user_message=2
                )

                messages_for_llm = [
                    {
                        "role": "user",
                        "content": f"{instructions}\n\nHere's a document:\n{document_text}",
                    }
                ] + buffered_history

                client = st.session_state.client

                stream = client.chat.completions.create(
                    model="gpt-5-chat-latest",
                    messages=messages_for_llm,
                    stream=True,
                )

                with st.chat_message("assistant"):
                    response = st.write_stream(stream)

                st.session_state.messages.append({"role": "assistant", "content": response})

                if normalized in ["no", "n", "nope", "nah"]:
                    st.session_state.awaiting_more_info = False
                else:
                    st.session_state.awaiting_more_info = True

                st.session_state.messages = conversation_buffer(
                    st.session_state.messages, keep_user_message=2
                )
