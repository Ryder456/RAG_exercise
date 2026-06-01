# process_upload.py
import hashlib
import io
import os
import traceback

import PyPDF2
from docx import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS

# ---------- 配置 ----------
class Config:
    persist_directory = "./faiss_index"
    chunk_size = 1000
    chunk_overlap = 100
    separators = ["\n\n", "\n", "。", ".", " ", "", "!", "?", "！", "？"]

class KnowledgeBaseService:
    def __init__(self):
        os.makedirs(Config.persist_directory, exist_ok=True)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY")
        self.embedding = DashScopeEmbeddings(model="text-embedding-v4", dashscope_api_key=api_key)

        index_path = os.path.join(Config.persist_directory, "index.faiss")
        if os.path.exists(index_path):
            # 已有索引，直接加载
            self.vectorstore = FAISS.load_local(
                Config.persist_directory,
                self.embedding,
                allow_dangerous_deserialization=True
            )
        else:
            # 创建带占位文档的空索引（占位文档会在问答时被过滤，不影响使用）
            self.vectorstore = FAISS.from_texts(["__placeholder__"], self.embedding)
            self.vectorstore.save_local(Config.persist_directory)

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=Config.chunk_size,
            chunk_overlap=Config.chunk_overlap,
            separators=Config.separators,
            length_function=len,
        )

# 全局服务实例
_kb_service = None

def get_kb_service():
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service

# ---------- 哈希记录 ----------
HASH_FILE = "processed_hashes.txt"

def load_processed_hashes():
    if not os.path.exists(HASH_FILE):
        return set()
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_processed_hashes(hashes_set):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        for h in sorted(hashes_set):
            f.write(h + "\n")

def compute_sha256(file_bytes: bytes) -> str:
    sha = hashlib.sha256()
    sha.update(file_bytes)
    return sha.hexdigest()

# ---------- 文本提取 ----------
def extract_text(file_bytes: bytes, file_type: str) -> str:
    if "text/plain" in file_type:
        return file_bytes.decode("utf-8")

    elif "pdf" in file_type:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)

    elif any(k in file_type for k in ("word", "msword", "officedocument")):
        doc = Document(io.BytesIO(file_bytes))
        text = [para.text for para in doc.paragraphs]
        return "\n".join(text)

    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

# ---------- 文件处理主流程 ----------
def process_file(uploaded_file) -> tuple:
    try:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_type = uploaded_file.type

        # 1. 去重检查
        file_hash = compute_sha256(file_bytes)
        processed_hashes = load_processed_hashes()
        if file_hash in processed_hashes:
            return ("duplicate", "该文件已被上传，请勿重复上传")

        # 2. 提取文本
        raw_text = extract_text(file_bytes, file_type)
        if raw_text.startswith("不支持") or raw_text.startswith("PDF读取失败") or raw_text.startswith("Word文档"):
            return ("error", raw_text)

        # 3. 分割文本
        service = get_kb_service()
        chunks = service.spliter.split_text(raw_text)
        if not chunks:
            return ("error", "文件中未提取到有效文本")

        # 4. 存入向量库
        ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
        service.vectorstore.add_texts(
            texts=chunks,
            metadatas=[{"source": file_name}] * len(chunks),
            ids=ids,
        )
        service.vectorstore.save_local(Config.persist_directory)

        # 5. 更新哈希记录
        processed_hashes.add(file_hash)
        save_processed_hashes(processed_hashes)

        return ("success", f"文件“{file_name}”处理成功，已添加 {len(chunks)} 条记录到向量库")

    except Exception as e:
        traceback.print_exc()
        return ("error", f"处理文件时出错: {str(e)}")