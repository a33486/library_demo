import base64
import hashlib
import json
import sys
from pathlib import Path
from pdfplumber import open as pdf_open
from io import BytesIO
from typing import Dict, Tuple, List, Any
from loguru import logger

from config_service import get_storage_config
from app.services.get_vl_data import get_vl_request
from app.services.document_integration_service import integrate_document_with_vllm

# 添加项目根目录到Python路径，以便导入config_service
sys.path.append(str(Path(__file__).parent.parent.parent))


def split_pdf_to_images_service(pdf_bytes: bytes) -> Tuple[bool, str, Dict[str, str]]:
    """
    将PDF字节流按页切割为图片，计算MD5值并存储到指定文件夹。
    
    Args:
        pdf_bytes: PDF文件的字节流
        
    Returns:
        Tuple[bool, str, Dict[str, str]]: (成功标志, 消息, 结果数据)
    """
    try:
        # 从配置获取存储路径
        storage_config = get_storage_config()
        result_path = storage_config["result_path"]

        # 计算PDF文件的MD5值
        md5_hash = hashlib.md5(pdf_bytes).hexdigest()
        logger.info(f"PDF文件MD5值: {md5_hash}")

        # 创建基于配置的存储目录结构
        documents_dir = Path(result_path) / "documents"
        md5_dir = documents_dir / md5_hash

        # 确保目录存在
        md5_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {md5_dir}")

        result = {}
        saved_files = []
        images_base64 = {}  # 存储所有图片的base64数据
        s = ""
        with pdf_open(BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF总页数: {total_pages}")

            for i, page in enumerate(pdf.pages, start=1):
                # 生成图片
                pil_img = page.to_image(resolution=200).original

                # 将图片转为字节流并计算MD5
                buf = BytesIO()
                pil_img.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                img_md5 = hashlib.md5(img_bytes).hexdigest()

                # 使用图片MD5值作为文件名
                img_filename = f"{img_md5}.png"
                img_path = md5_dir / img_filename

                # 保存图片到文件
                pil_img.save(img_path, format="PNG", optimize=True)
                saved_files.append(str(img_path))

                # 生成base64字符串并存储
                img_b64 = base64.b64encode(img_bytes).decode()
                images_base64[str(i)] = img_b64

                # 调用VL请求获取识别结果

                logger.info(f"已保存第 {i} 页: {img_filename} (MD5: {img_md5})")
                vl_content = get_vl_request(img_b64)
                if vl_content:
                    s += vl_content
                    
                    # 将VL内容存储到向量数据库
                    from app.services.get_embeddings import store_vl_content_to_vector_db
                    metadata = {
                        "page_num": i,
                        "pdf_md5": md5_hash,
                        "img_md5": img_md5,
                        "source": "pdf_vl_extraction"
                    }
                    vector_result = store_vl_content_to_vector_db(vl_content, metadata)
                    if vector_result["success"]:
                        logger.info(f"第 {i} 页VL内容向量化存储成功")
                    else:
                        logger.warning(f"第 {i} 页VL内容向量化存储失败: {vector_result['message']}")

        # 保存文件信息到元数据文件
        metadata = {
            "md5": md5_hash,
            "total_pages": total_pages,
            "saved_files": saved_files,
            "directory": str(md5_dir),
            "storage_config": storage_config
        }

        metadata_path = md5_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"PDF处理完成，文件保存在: {md5_dir}")
        if s:
            # 调用文档整合服务获取摘要
            integration_result = integrate_document_with_vllm(s)
            if integration_result["success"]:
                logger.info(f"文档整合成功，整合后内容长度: {integration_result['content_length']}")
                return True, "PDF处理成功", {
                    "dir": str(md5_dir),
                    "original_content": s,
                    "integrated_content": integration_result["integrated_content"],
                    "content_length": integration_result["content_length"]
                }
            else:
                logger.warning(f"文档整合失败: {integration_result['message']}")
                return True, "PDF处理成功，但文档整合失败", {
                    "dir": str(md5_dir),
                    "original_content": s,
                    "integration_error": integration_result["message"]
                }
        return True, "PDF处理成功", {"dir": str(md5_dir)}

    except Exception as e:
        error_msg = f"PDF处理失败: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, {}


def process_pdf_with_vl(pdf_bytes: bytes) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理PDF文件并调用VL模型进行识别，返回拼接的文档内容
    
    Args:
        pdf_bytes: PDF文件的字节流
        
    Returns:
        Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 结果数据)
    """
    try:
        # 首先处理PDF文件
        success, message, pdf_result = split_pdf_to_images_service(pdf_bytes)
        if not success:
            return False, message, {}

        # 导入VL处理函数
        from app.services.get_vl_data import process_base64_images_with_vl

        images_base64 = pdf_result.get("images_base64", {})
        total_pages = pdf_result.get("total_pages", 0)

        if not images_base64:
            return False, "没有找到图片数据", {}

        logger.info(f"开始处理 {len(images_base64)} 张图片的VL识别")

        # 使用新的VL处理函数
        vl_result = process_base64_images_with_vl(images_base64)

        if not vl_result.get("success", False):
            return False, vl_result.get("message", "VL处理失败"), {}

        # 构建返回结果
        result_data = {
            "dir": pdf_result.get("dir", ""),
            "total_pages": total_pages,
            "processed_pages": vl_result.get("processed_count", 0),
            "vl_results": vl_result.get("results", {}),
            "combined_content": vl_result.get("combined_content", ""),
            "content_length": vl_result.get("content_length", 0)
        }

        logger.info(
            f"PDF VL处理完成，共处理 {vl_result.get('processed_count', 0)} 页，总内容长度: {vl_result.get('content_length', 0)}")

        return True, "PDF VL处理成功", result_data

    except Exception as e:
        error_msg = f"PDF VL处理失败: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, {}
