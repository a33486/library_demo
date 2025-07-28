import httpx
import json
from typing import Dict, Any
from loguru import logger
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入config_service
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_service import get_config_value
from app.prompts.prompt_datas import DOCUMENT_INTEGRATION_PROMPT, DOCUMENT_INTEGRATION_PROMPT_SYSTEM

def integrate_document_with_vllm(document_content: str) -> Dict[str, Any]:
    """
    使用VLLM框架整合文档内容
    
    Args:
        document_content: 要整合的文档内容
        
    Returns:
        整合后的文档内容
    """
    try:
        # 从配置文件获取VLLM API URL
        vllm_api_url = get_config_value("external_services", "vllm_api_url", "http://localhost:58123/v1/chat/completions")
        
        # 构建请求payload
        payload = {
            "model": "/models/qwen2.5-7b",
            "messages": [
                {
                    "role": "system",
                    "content": DOCUMENT_INTEGRATION_PROMPT_SYSTEM
                },
                {
                    "role": "user",
                    "content": DOCUMENT_INTEGRATION_PROMPT.format(document_content=document_content)
                }
            ],
            "max_tokens": 10000,
            "stream": False
        }
        
        logger.info(f"发送VLLM请求到: {vllm_api_url}")
        
        # 发送请求
        response = httpx.post(vllm_api_url, json=payload, timeout=600)
        logger.info(f"VLLM请求响应状态: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            # 提取响应内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content", "")
                logger.info(f"文档整合成功，内容长度: {len(content)}")
                
                return {
                    "success": True,
                    "message": "文档整合成功",
                    "integrated_content": content,
                    "content_length": len(content)
                }
            else:
                logger.warning("VLLM响应中没有找到有效内容")
                return {
                    "success": False,
                    "message": "VLLM响应中没有找到有效内容",
                    "integrated_content": "",
                    "content_length": 0
                }
        else:
            logger.error(f"VLLM请求失败: {response.status_code}, {response.text}")
            return {
                "success": False,
                "message": f"VLLM请求失败: {response.status_code}",
                "integrated_content": "",
                "content_length": 0
            }
            
    except Exception as e:
        error_msg = f"文档整合异常: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "integrated_content": "",
            "content_length": 0
        } 