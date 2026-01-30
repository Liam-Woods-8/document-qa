import streamlit as st

lab1_page = st.Page("Lab1.py", title="lab 1")
lab2_page = st.Page("Lab2.py", title="lab 2")

pg = st.navigation([lab2_page, lab1_page])

pg.run()