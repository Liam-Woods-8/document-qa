import streamlit as st
from openai import OpenAI
import anthropic
import fitz  # PyMuPDF


def extract_text_from_pdf(uploaded_pdf) -> str:
    """Extract all text from an uploaded PDF file using PyMuPDF."""
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# Show title and description (Lab 2)
st.title("Lab 2 – Document Summarizer")

# Sidebar dropdown: language (required)
language = st.sidebar.selectbox(
    "Language",
    ("English", "Spanish", "French", "Russian"),
)

# Sidebar dropdown: summary type (required)
summary_type = st.sidebar.selectbox(
    "Summary type",
    (
        "Summarize the document in 100 words",
        "Summarize the document in 2 connecting paragraphs",
        "Summarize the document in 5 bullet points",
    ),
)

# ✅ Checkbox model selection (required by lab wording)
use_advanced_model = st.sidebar.checkbox("Use advanced model")

# Load API keys from Streamlit secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
claude_api_key = st.secrets["CLAUDE_API_KEY"]

# Upload PDF (required)
uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)

    # Lab hint: summary type should be part of instructions
    instructions = f"{summary_type}. Write the summary in {language}."

    # -----------------------------
    # Default model (unchecked): GPT (OpenAI)
    # -----------------------------
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

    # -----------------------------
    # Advanced model (checked): Claude (Anthropic)
    # -----------------------------
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
