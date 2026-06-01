# 📚 RAG 知识库问答系统

一个基于检索增强生成（RAG）的本地知识库智能问答系统。支持上传 Word、PDF、TXT 文档，自动向量化并存入 FAISS 向量数据库，然后通过自然语言提问，由通义千问大模型生成基于文档的准确回答。

## ✨ 功能特性

- **文件上传与去重**：Web 界面上传文档，SHA‑256 哈希自动去重。
- **文档向量化**：文本分割后使用阿里云 DashScope 嵌入模型生成向量，存入 FAISS。
- **智能问答**：用户问题向量化后检索相关段落，拼接上下文调用 qwen-turbo 生成回答。
- **聊天历史**：对话以首条提问时间命名，支持继续历史对话和删除。
- **技术栈**：Python · Streamlit · LangChain · FAISS · DashScope API

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/Ryder456/RAG_Practice.git
cd RAG_Practice