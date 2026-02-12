import streamlit as st

lab1_page = st.Page("lab1.py", title="lab 1")
lab2_page = st.Page("lab2.py", title="lab 2")
lab3_page = st.Page("lab3.py", title="lab 3")
lab4_page = st.Page("lab4.py", title="lab 4")

pg = st.navigation([lab4_page, lab3_page, lab2_page, lab1_page])

pg.run()