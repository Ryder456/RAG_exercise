# chat_service.py
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from dashscope import Generation
import os

PERSIST_DIRECTORY = "./faiss_index"

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")

embedding = DashScopeEmbeddings(model="text-embedding-v4", dashscope_api_key=api_key)
os.makedirs(PERSIST_DIRECTORY, exist_ok=True)

def get_vectorstore():
    """加载或重新加载向量库（保证获取最新数据）"""
    index_path = os.path.join(PERSIST_DIRECTORY, "index.faiss")
    if os.path.exists(index_path):
        vectorstore = FAISS.load_local(
            PERSIST_DIRECTORY,
            embedding,
            allow_dangerous_deserialization=True
        )
    else:
        # 创建初始占位，后续查询时忽略
        vectorstore = FAISS.from_texts(["__placeholder__"], embedding)
        vectorstore.save_local(PERSIST_DIRECTORY)
    return vectorstore

PROMPT_TEMPLATE = """基于以下参考资料：
{context}

回答用户问题：{question}
请用中文回答，答案应简洁准确。如果参考资料不足以回答问题，请说明。
"""

def answer_question(question: str, top_k: int = 3) -> str:
    vectorstore = get_vectorstore()  # 每次查询都重新加载，确保最新
    docs = vectorstore.similarity_search(question, k=top_k + 1)  # 多取一个以便过滤占位
    # 过滤掉占位文档
    filtered_docs = [doc for doc in docs if doc.page_content != "__placeholder__"]
    if not filtered_docs:
        return "知识库中暂无相关文档，无法回答该问题。"
    context = "\n\n".join([doc.page_content for doc in filtered_docs[:top_k]])
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    final_prompt = prompt.format(context=context, question=question)
    try:
        response = Generation.call(
            model="qwen-turbo",
            prompt=final_prompt,
            temperature=0.7,
        )
        if response.status_code == 200:
            return response.output.text.strip()
        else:
            return f"大模型调用失败：{response.message}"
    except Exception as e:
        return f"调用大模型时出错：{str(e)}"