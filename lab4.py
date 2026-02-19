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
    return text



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

def retrieve_top_docs(question: str, n_results: int = 3):
    results = st.session_state.Lab4_VectorDB.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas"],
    )
    docs = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]
    return docs, sources

st.title("Lab 4 – RAG")

# NAV 
page = st.sidebar.radio("Navigation", ["Lab4","Summary", "Chatbot"])

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

if page == "Lab4":
    PDF_FOLDER = "lab4_pdfs"

    if "Lab4_VectorDB" not in st.session_state:
        st.session_state.Lab4_VectorDB = create_lab4_vectordb(PDF_FOLDER)

    test_query = st.text_input("Test search (remove after you validate)", "")
    if test_query:
        results = st.session_state.Lab4_VectorDB.query(
            query_texts=[test_query],
            n_results=3,
            include=["metadatas"],
        )
        st.write("Top 3 documents:")
        for i, meta in enumerate(results["metadatas"][0], start=1):
            st.write(f"{i}. {meta['source']}")

    st.divider()
    st.subheader("Course Chatbot (RAG)")

    rag_question = st.chat_input("Ask a question about the syllabi...")
    if rag_question:
        docs, sources = retrieve_top_docs(rag_question, n_results=3)

        context = "\n\n---\n\n".join(docs)

        rag_prompt = (
            "You are a course information chatbot.\n"
            "Use the RAG context below to answer.\n"
            "Be clear when you are using knowledge from the RAG context.\n"
            "If the answer is not in the RAG context, say you cannot find it.\n\n"
            f"RAG CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{rag_question}\n"
        )

        client = OpenAI(api_key=openai_api_key)

        stream = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": rag_prompt}],
            stream=True,
        )

        with st.chat_message("assistant"):
            st.write_stream(stream)

        st.write("Sources:", sources)
