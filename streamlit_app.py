import importlib
import streamlit as st

# This file only registers pages for Streamlit's multipage navigation.
# It intentionally avoids importing `Lab2` at top-level so the page
# code only runs when the Lab2 page is selected.

def _load_lab2():
    importlib.import_module("Lab2")


pages = [
    st.Page("Intro-to-Streamlit", lambda: st.markdown("# Intro-to-Streamlit\n\nWelcome to the lab.")),
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
