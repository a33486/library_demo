import httpx
import json
from typing import Dict, Any, List
from loguru import logger
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_service import get_config_value
from app.prompts.prompt_datas import (
    TRANSLATION_PROMPT, 
    TRANSLATION_SYSTEM,
    QUERY_ANSWER_PROMPT,
    QUERY_ANSWER_SYSTEM
)
from app.services.get_embeddings import embedding_service
from app.services.get_vl_data import get_vl_request

def translate_to_chinese(content: str) -> Dict[str, Any]:
    """
    将用户输入翻译成中文
    
    Args:
        content: 用户输入的内容
        
    Returns:
        翻译结果
    """
    try:
        # 使用现有的VLLM API配置
        vllm_api_url = get_config_value("external_services", "vllm_api_url", "http://localhost:58123/v1/chat/completions")
        
        payload = {
            "model": "/models/qwen2.5-7b",
            "messages": [
                {
                    "role": "system",
                    "content": TRANSLATION_SYSTEM
                },
                {
                    "role": "user",
                    "content": TRANSLATION_PROMPT.format(content=content)
                }
            ],
            "max_tokens": 1000,
            "stream": False
        }
        
        logger.info(f"发送翻译请求: {content}")
        
        response = httpx.post(vllm_api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                translated_content = response_data["choices"][0].get("message", {}).get("content", "")
                logger.info(f"翻译成功: {content} -> {translated_content}")
                return {
                    "success": True,
                    "translated_content": translated_content.strip()
                }
        
        logger.error(f"翻译失败: {response.status_code}")
        return {"success": False, "message": "翻译失败"}
        
    except Exception as e:
        logger.error(f"翻译异常: {e}")
        return {"success": False, "message": str(e)}

def search_similar_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    在向量数据库中搜索相似文档
    
    Args:
        query: 查询内容
        k: 返回结果数量
        
    Returns:
        相似文档列表
    """
    try:
        logger.info(f"搜索相似文档: {query}")
        results = embedding_service.search_similar(query, k=k)
        logger.info(f"找到 {len(results)} 个相似文档")
        return results
        
    except Exception as e:
        logger.error(f"搜索相似文档失败: {e}")
        return []

def get_answer_with_vl(user_question: str, retrieved_content: str, image_base64: str = None) -> Dict[str, Any]:
    """
    使用VL模型获取答案
    
    Args:
        user_question: 用户问题
        retrieved_content: 检索到的内容
        image_base64: 图片base64（可选）
        
    Returns:
        答案结果
    """
    try:
        # 使用现有的VLLM API配置
        vllm_api_url = get_config_value("external_services", "vllm_api_url", "http://localhost:58123/v1/chat/completions")
        
        # 构建消息内容
        if image_base64:
            # 如果有图片，使用VL模型
            messages = [
                {
                    "role": "system",
                    "content": QUERY_ANSWER_SYSTEM
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": QUERY_ANSWER_PROMPT.format(
                                user_question=user_question,
                                retrieved_content=retrieved_content
                            )
                        }
                    ]
                }
            ]
        else:
            # 如果没有图片，使用纯文本模型
            messages = [
                {
                    "role": "system",
                    "content": QUERY_ANSWER_SYSTEM
                },
                {
                    "role": "user",
                    "content": QUERY_ANSWER_PROMPT.format(
                        user_question=user_question,
                        retrieved_content=retrieved_content
                    )
                }
            ]
        
        payload = {
            "model": "/models/qwen2.5-7b",
            "messages": messages,
            "max_tokens": 2000,
            "stream": False
        }
        
        logger.info(f"发送VL回答请求")
        
        response = httpx.post(vllm_api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                answer = response_data["choices"][0].get("message", {}).get("content", "")
                logger.info(f"VL回答成功，答案长度: {len(answer)}")
                return {
                    "success": True,
                    "answer": answer.strip()
                }
        
        logger.error(f"VL回答失败: {response.status_code}")
        return {"success": False, "message": "VL回答失败"}
        
    except Exception as e:
        logger.error(f"VL回答异常: {e}")
        return {"success": False, "message": str(e)}

def process_query(user_question: str, image_base64: str = None) -> Dict[str, Any]:
    """
    处理用户查询的完整流程
    
    Args:
        user_question: 用户问题
        image_base64: 图片base64（可选）
        
    Returns:
        处理结果
    """
    try:
        logger.info(f"开始处理用户查询: {user_question}")
        
        # 1. 翻译成中文
        translation_result = translate_to_chinese(user_question)
        if not translation_result["success"]:
            return {
                "success": False,
                "message": f"翻译失败: {translation_result['message']}",
                "step": "translation"
            }
        
        translated_question = translation_result["translated_content"]
        logger.info(f"翻译结果: {translated_question}")
        
        # 2. 向量数据库检索
        search_results = search_similar_documents(translated_question, k=3)
        if not search_results:
            return {
                "success": False,
                "message": "未找到相关文档",
                "step": "search",
                "translated_question": translated_question
            }
        
        # 3. 构建检索内容
        retrieved_content = "\n\n".join([
            f"文档{i+1} (相似度: {result['score']:.3f}):\n{result['content']}"
            for i, result in enumerate(search_results)
        ])
        
        logger.info(f"检索到 {len(search_results)} 个相关文档")
        
        # 4. 使用VL模型获取答案
        answer_result = get_answer_with_vl(user_question, retrieved_content, image_base64)
        if not answer_result["success"]:
            return {
                "success": False,
                "message": f"VL回答失败: {answer_result['message']}",
                "step": "answer",
                "translated_question": translated_question,
                "search_results": search_results
            }
        
        # 5. 返回完整结果
        return {
            "success": True,
            "message": "查询处理成功",
            "original_question": user_question,
            "translated_question": translated_question,
            "search_results": search_results,
            "answer": answer_result["answer"],
            "search_count": len(search_results)
        }
        
    except Exception as e:
        error_msg = f"查询处理异常: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "step": "general"
        } 