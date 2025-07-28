import os
import base64
import httpx
import json
from typing import List, Dict, Any
from loguru import logger
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入config_service
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_service import get_config_value

from app.prompts.prompt_datas import PRODUCT_INFORMATION


def find_png_files(directory: str) -> List[str]:
    """
    遍历目录及其子目录，查找所有的PNG文件
    
    Args:
        directory: 要搜索的目录路径
        
    Returns:
        PNG文件路径列表
    """
    png_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.png'):
                png_files.append(os.path.join(root, file))
    return png_files


def file_to_base64(file_path: str) -> str:
    """
    将图片文件转换为Base64编码
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        Base64编码的字符串
    """
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


def get_vl_request(image_base64: str, url: str = None) -> str:
    """
    发送视觉语言模型请求并返回识别结果
    
    Args:
        image_base64: Base64编码的图片
        url: API接口地址
        
    Returns:
        识别结果content内容，如果失败返回空字符串
    """
    try:
        if url is None:
            url = get_config_value("external_services", "vl_api_url", "http://example.com/api/upload")

        payload = {
            "model": "/function/vllm/model",
            "messages": [
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
                            "text": PRODUCT_INFORMATION
                        }
                    ]
                }
            ],
            "stream": False
        }

        # 超时时间注意vllm框架限制
        response = httpx.post(url, json=payload, timeout=600)
        logger.info(f"VL请求响应状态: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            # 提取所有choices中的content并拼接
            content_parts = []
            if "choices" in response_data:
                for choice in response_data["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if content:
                            content_parts.append(content)

            # 拼接所有content
            if content_parts:
                result = "\n".join(content_parts)
                logger.info(f"成功提取内容，长度: {len(result)}")
                return result
            else:
                logger.warning("响应中没有找到有效的content")
                return ""
        else:
            logger.error(f"VL请求失败: {response.status_code}, {response.text}")
            return ""

    except Exception as e:
        logger.error(f"VL请求异常: {str(e)}")
        return ""


def process_images_with_vl(directory: str = None) -> Dict[str, str]:
    """
    处理目录中的所有PNG图片，使用视觉语言模型进行识别
    
    Args:
        directory: 要处理的目录路径，默认为当前工作目录
        
    Returns:
        字典，键为图片路径，值为识别结果content
    """
    try:
        # 从配置文件获取VL API URL
        vl_api_url = get_config_value("external_services", "vl_api_url", "http://example.com/api/upload")
        logger.info(f"使用VL API地址: {vl_api_url}")

        # 使用指定目录或当前工作目录
        if directory is None:
            directory = os.getcwd()

        logger.info(f"开始处理目录: {directory}")

        # 查找所有PNG文件
        png_files = find_png_files(directory)
        logger.info(f"找到PNG文件数量: {len(png_files)}")

        results = {}

        for png_file in png_files:
            logger.info(f"处理图片: {png_file}")

            # 转换为Base64
            image_base64 = file_to_base64(png_file)

            # 发送VL请求
            content = get_vl_request(image_base64, vl_api_url)

            # 存储结果
            results[png_file] = content

            if content:
                logger.info(f"图片 {png_file} 识别成功")
            else:
                logger.warning(f"图片 {png_file} 识别失败或无内容")

        logger.info(f"处理完成，共处理 {len(results)} 个图片")
        return results

    except Exception as e:
        logger.error(f"处理图片异常: {str(e)}")
        return {}


def process_base64_images_with_vl(images_base64: Dict[str, str], url: str = None) -> Dict[str, Any]:
    """
    处理base64编码的图片列表，使用视觉语言模型进行识别并拼接所有文档
    
    Args:
        images_base64: 字典，键为页面标识，值为base64编码的图片
        url: API接口地址
        
    Returns:
        字典，包含处理结果和拼接的文档内容
    """
    try:
        if not images_base64:
            logger.warning("没有提供图片数据")
            return {
                "success": False,
                "message": "没有提供图片数据",
                "results": {},
                "combined_content": "",
                "content_length": 0
            }

        logger.info(f"开始处理 {len(images_base64)} 张图片的VL识别")

        # 处理每张图片并收集结果
        vl_results = {}
        all_content_parts = []

        for page_id, img_b64 in images_base64.items():
            logger.info(f"处理图片 {page_id} 的VL识别")

            # 调用VL请求
            content = get_vl_request(img_b64, url)

            if content:
                vl_results[page_id] = content
                all_content_parts.append(f"=== {page_id} ===\n{content}")
                logger.info(f"图片 {page_id} 识别成功，内容长度: {len(content)}")
            else:
                logger.warning(f"图片 {page_id} 识别失败或无内容")

        # 拼接所有文档内容
        combined_content = "\n\n".join(all_content_parts)

        # 构建返回结果
        result_data = {
            "success": True,
            "message": "VL处理成功",
            "results": vl_results,
            "combined_content": combined_content,
            "content_length": len(combined_content),
            "processed_count": len(vl_results),
            "total_count": len(images_base64)
        }

        logger.info(f"VL处理完成，共处理 {len(vl_results)} 张图片，总内容长度: {len(combined_content)}")

        return result_data

    except Exception as e:
        error_msg = f"VL处理异常: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "results": {},
            "combined_content": "",
            "content_length": 0
        }
