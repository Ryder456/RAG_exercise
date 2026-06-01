# chat_ui.py
import streamlit as st
from datetime import datetime
from chat_service import answer_question
from history import get_all_histories, load_history, save_history, delete_history

def chat_page():
    st.title("📚 知识库智能问答")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history_time" not in st.session_state:
        st.session_state.history_time = None
    if "histories" not in st.session_state:
        st.session_state.histories = get_all_histories()

    with st.sidebar:
        st.header("历史对话")
        history_options = ["-- 新建对话 --"] + [h[0] for h in st.session_state.histories]

        if st.session_state.history_time is not None:
            try:
                default_index = [h[0] for h in st.session_state.histories].index(
                    st.session_state.history_time
                ) + 1
            except ValueError:
                default_index = 0
        else:
            default_index = 0

        selected = st.selectbox(
            "选择或新建对话",
            history_options,
            index=default_index
        )

        if selected != "-- 新建对话 --":
            for time_str, path in st.session_state.histories:
                if time_str == selected:
                    st.session_state.messages = load_history(path)
                    st.session_state.history_time = selected
                    break
        else:
            if st.session_state.history_time is not None:
                st.session_state.messages = []
                st.session_state.history_time = None

        if st.session_state.history_time is not None:
            if st.button("删除此对话", type="secondary"):
                delete_history(st.session_state.history_time)
                st.session_state.histories = get_all_histories()
                st.session_state.messages = []
                st.session_state.history_time = None
                st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("请输入你的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state.history_time is None:
            st.session_state.history_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                answer = answer_question(prompt)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        save_history(st.session_state.messages, first_question_time_str=st.session_state.history_time)
        st.session_state.histories = get_all_histories()