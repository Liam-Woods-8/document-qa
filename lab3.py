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


st.title("Lab 3 – Chatbot with Conversational Memory")

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

# CHATBOT PAGE (slides style)
elif page == "Chatbot":
    if not uploaded_file:
        st.info("Upload a PDF to chat about it.")
    else:
        if "client" not in st.session_state:
            st.session_state.client = OpenAI(api_key=openai_api_key)

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "How can I help you?"}
            ]

        for msg in st.session_state.messages:
            chat_msg = st.chat_message(msg["role"])
            chat_msg.write(msg["content"])

        if prompt := st.chat_input("What is up?"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            messages_for_llm = [
                {
                    "role": "user",
                    "content": f"{instructions}\n\nHere's a document:\n{document_text}",
                }
            ] + st.session_state.messages

            client = st.session_state.client

            stream = client.chat.completions.create(
                model="gpt-5-chat-latest",
                messages=messages_for_llm,
                stream=True,
            )

            with st.chat_message("assistant"):
                response = st.write_stream(stream)

            st.session_state.messages.append({"role": "assistant", "content": response})
