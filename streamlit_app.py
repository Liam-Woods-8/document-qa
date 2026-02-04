import streamlit as st

lab1_page = st.Page("lab1.py", title="lab 1")
lab2_page = st.Page("lab2.py", title="lab 2")
lab3_page = st.Page("lab3.py", title="lab 3")

pg = st.navigation([lab3_page, lab2_page, lab1_page])

pg.run()