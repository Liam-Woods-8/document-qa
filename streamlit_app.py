import importlib
import streamlit as st

# This file registers pages for Streamlit's multipage navigation.
# If the `st.Page` API is not available or raises a TypeError,
# fall back to a simple sidebar-based navigation to avoid crashing.

def _load_lab2():
    importlib.import_module("Lab2")


def _intro_page():
    st.markdown("# Intro-to-Streamlit\n\nWelcome to the lab.")


try:
    pages = [
        st.Page("Intro-to-Streamlit", lambda: _intro_page()),
        st.Page("Lab2.py", _load_lab2),
    ]

    # Register navigation and set the default page to Lab2.py
    st.navigation(pages, default="Lab2.py")

    # Call pg.run() if a page runner is available; ignore if not present.
    try:
        import pg

        pg.run()
    except Exception:
        pass

except TypeError:
    # Fallback: simple sidebar navigation if st.Page isn't supported.
    page_names = ["Intro-to-Streamlit", "Lab2.py"]
    default_index = 1 if "Lab2.py" in page_names else 0
    choice = st.sidebar.selectbox("Page", page_names, index=default_index)
    if choice == "Intro-to-Streamlit":
        _intro_page()
    elif choice == "Lab2.py":
        _load_lab2()
