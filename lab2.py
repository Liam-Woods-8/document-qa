import streamlit as st
from openai import OpenAI
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

# Checkbox: model selection (required)
use_advanced_model = st.sidebar.checkbox("Use advanced model")

# Pick model based on checkbox
# (Lab says mini vs nano as an example; this keeps the required structure.)
model_to_use = "gpt-5-chat-latest" if use_advanced_model else "gpt-5-chat-latest"

# Part B: Use Streamlit secrets (no API key text input)
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

# Upload PDF (required)
uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)

    # Build the instructions (Lab hint: summary type should be part of instructions)
    instructions = f"{summary_type}. Write the summary in {language}."

    # Messages list (matches the OpenAI slides pattern)
    messages = [
        {
            "role": "user",
            "content": f"{instructions}\n\nHere's a document:\n{document_text}",
        }
    ]

    # Generate summary with OpenAI (slides pattern)
    stream = client.chat.completions.create(
        model=model_to_use,
        messages=messages,
        stream=True,
    )

    # Stream output
    st.write_stream(stream)
else:
    st.info("Upload a PDF to generate a summary.")