# main.py
import streamlit as st

st.set_page_config(page_title="知识库 RAG 系统", page_icon="📚", layout="wide")

from app import upload_page
from chat_ui import chat_page

tab1, tab2 = st.tabs(["📂 知识库上传", "💬 智能问答"])

with tab1:
    upload_page()

with tab2:
    chat_page()