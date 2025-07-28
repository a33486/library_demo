import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_service import get_embedding_config

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError as e:
    logger.error(f"导入langchain相关模块失败: {e}")
    logger.error("请安装: pip install langchain langchain-community chromadb sentence-transformers")

class EmbeddingService:
    """向量化服务类"""
    
    def __init__(self):
        """初始化向量化服务"""
        self.config = get_embedding_config()
        self.embedding_model_path = self.config["embedding_model_path"]
        self.chroma_host = self.config["chroma_host"]
        self.chroma_port = self.config["chroma_port"]
        
        # 初始化embedding模型
        self.embeddings = None
        self.vectorstore = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """初始化embedding模型"""
        try:
            logger.info(f"初始化embedding模型: {self.embedding_model_path}")
            
            # 检查模型路径是否存在
            if not os.path.exists(self.embedding_model_path):
                logger.warning(f"模型路径不存在: {self.embedding_model_path}")
                logger.info("尝试从HuggingFace下载模型...")
            
            # 初始化HuggingFace embedding模型
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_path,
                model_kwargs={'device': 'cpu'},  # 可以根据需要改为'cuda'
                encode_kwargs={'normalize_embeddings': True}
            )
            
            logger.info("Embedding模型初始化成功")
            
        except Exception as e:
            logger.error(f"初始化embedding模型失败: {e}")
            raise
    
    def _initialize_vectorstore(self, collection_name: str = "pdf_documents"):
        """初始化向量数据库"""
        try:
            logger.info(f"初始化Chroma向量数据库: {self.chroma_host}:{self.chroma_port}")
            
            # 初始化Chroma向量数据库
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                collection_name=collection_name,
                persist_directory="./chroma_db"  # 本地持久化目录
            )
            
            logger.info("向量数据库初始化成功")
            
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}")
            raise
    
    def split_text(self, text: str, chunk_size: int = 300, chunk_overlap: int = 30) -> List[Document]:
        """
        将文本分割成小块
        
        Args:
            text: 要分割的文本
            chunk_size: 每块的大小
            chunk_overlap: 块之间的重叠大小
            
        Returns:
            分割后的文档列表
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
            )
            
            documents = text_splitter.create_documents([text])
            logger.info(f"文本分割完成，共 {len(documents)} 个文档块")
            
            return documents
            
        except Exception as e:
            logger.error(f"文本分割失败: {e}")
            raise
    
    def store_embeddings(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
                        collection_name: str = "pdf_documents") -> Dict[str, Any]:
        """
        将文本内容转换为向量并存储到Chroma数据库
        
        Args:
            content: 要向量化的文本内容
            metadata: 元数据信息
            collection_name: 集合名称
            
        Returns:
            存储结果信息
        """
        try:
            if not content.strip():
                logger.warning("内容为空，跳过向量化")
                return {"success": False, "message": "内容为空"}
            
            # 初始化向量数据库
            self._initialize_vectorstore(collection_name)
            
            # 分割文本
            documents = self.split_text(content)
            
            if not documents:
                logger.warning("文本分割后为空")
                return {"success": False, "message": "文本分割后为空"}
            
            # 添加元数据
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
            
            # 存储到向量数据库
            logger.info(f"开始存储 {len(documents)} 个文档到向量数据库")
            
            # 使用add_documents方法添加文档
            ids = self.vectorstore.add_documents(documents)
            
            # 持久化数据库
            self.vectorstore.persist()
            
            logger.info(f"向量化存储成功，共存储 {len(ids)} 个文档")
            
            return {
                "success": True,
                "message": "向量化存储成功",
                "document_count": len(documents),
                "ids": ids,
                "collection_name": collection_name
            }
            
        except Exception as e:
            error_msg = f"向量化存储失败: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def search_similar(self, query: str, k: int = 5, collection_name: str = "pdf_documents") -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            collection_name: 集合名称
            
        Returns:
            相似文档列表
        """
        try:
            # 初始化向量数据库
            self._initialize_vectorstore(collection_name)
            
            # 执行相似性搜索
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            logger.info(f"相似性搜索完成，找到 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            return []

# 创建全局实例
embedding_service = EmbeddingService()

def store_vl_content_to_vector_db(vl_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    将VL识别内容存储到向量数据库
    
    Args:
        vl_content: VL识别的内容
        metadata: 元数据信息
        
    Returns:
        存储结果
    """
    try:
        logger.info(f"开始将VL内容存储到向量数据库，内容长度: {len(vl_content)}")
        
        # 调用embedding服务存储内容
        result = embedding_service.store_embeddings(vl_content, metadata)
        
        if result["success"]:
            logger.info(f"VL内容向量化存储成功: {result['message']}")
        else:
            logger.error(f"VL内容向量化存储失败: {result['message']}")
        
        return result
        
    except Exception as e:
        error_msg = f"VL内容向量化存储异常: {e}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
