import streamlit as st
from openai import OpenAI
import anthropic
import fitz  # PyMuPDF

# pdf extraction 
def extract_text_from_pdf(uploaded_pdf) -> str:
    """Extract all text from an uploaded PDF file using PyMuPDF."""
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# title and description 
st.title("Lab 3 – Chatbot with Conversational Memory")

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

# Checkbox model selection 
use_advanced_model = st.sidebar.checkbox("Use advanced model")

# Load API keys from Streamlit secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
claude_api_key = st.secrets["CLAUDE_API_KEY"]

# Upload PDF 
uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)

    instructions = f"{summary_type}. Write the summary in {language}."

    # Default model  GPT (OpenAI)
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

    # Advanced model Claude (Anthropic)
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

# chatbot section
elif page =="Chatbot":
    if "client" not in st.session_state:
        st.session_state.client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How can I help you?"}
        ]

    for message in st.session_state.messages:
        chat_msg=st.chat_message(msg["role"])
        chat_msg.write(msg["content"])

    if prompt:= st.chat_input("What is up?"):
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
            response= st.write_stream(stream)

        st.session_state.messages.append({"role": "assistant", "content": response})    
else:
    st.info("Upload a PDF to generate a summary.")
