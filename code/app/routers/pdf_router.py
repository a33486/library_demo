from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.pdf_service import split_pdf_to_images_service
from loguru import logger
import threading

router = APIRouter(prefix="/pdf")

@router.post("/split")
def split_pdf_to_images(file: UploadFile = File(...)) -> JSONResponse:
    """
    接收PDF文件，立即响应成功，然后在后台处理文件。
    
    Args:
        file: 上传的PDF文件
        
    Returns:
        JSONResponse: 处理结果
    """
    # 验证文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="请上传PDF文件")
    
    try:
        # 读取文件内容
        pdf_bytes = file.file.read()
        filename = file.filename
        logger.info(f"接收到PDF文件: {filename}, 大小: {len(pdf_bytes)} 字节")
        
        # 启动后台线程处理PDF
        def background_process():
            try:
                logger.info(f"开始处理PDF文件: {filename}")
                success, message, result = split_pdf_to_images_service(pdf_bytes)
                
                if success:
                    logger.info(f"PDF文件 {filename} 处理完成: {message}")
                else:
                    logger.error(f"PDF文件 {filename} 处理失败: {message}")
                    
            except Exception as e:
                logger.error(f"PDF文件 {filename} 处理异常: {str(e)}")
        
        thread = threading.Thread(target=background_process, daemon=True)
        thread.start()
        
        # 立即响应成功
        return JSONResponse({
            "success": True,
            "message": "文件已接收，正在后台处理",
            "data": {
                "filename": filename,
                "file_size": len(pdf_bytes)
            }
        })
            
    except Exception as e:
        error_msg = f"文件接收失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg) 