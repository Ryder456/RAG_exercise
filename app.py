# app.py
import streamlit as st
from process_upload import process_file

def upload_page():
    st.title("知识库更新服务")
    uploaded_file = st.file_uploader(
        "请选择一个文件上传",
        type=["txt", "pdf", "docx", "doc"],
        accept_multiple_files=False,
        help="支持 txt、pdf、docx、doc 文件，每次仅能上传一个"
    )
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        size = uploaded_file.size
        st.info(f"文件名：{file_name}")
        st.info(f"文件类型：{file_type}")
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        st.info(f"文件大小：{size_str}")

        # 显示处理中的加载动画
        with st.spinner("正在上传并处理文件，请稍候..."):
            result = process_file(uploaded_file)

        if isinstance(result, tuple) and len(result) == 2:
            status, message = result
            if status == "success":
                st.success(message)
            elif status == "duplicate":
                st.warning(message)
            else:
                st.error(message)
        else:
            # 兼容旧字符串返回
            if "成功" in result:
                st.success(result)
            elif "已被上传" in result:
                st.warning(result)
            else:
                st.error(result)
    else:
        st.info("请选择一个文件以开始上传")