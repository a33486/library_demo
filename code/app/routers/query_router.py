from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from app.services.query_service import process_query

router = APIRouter(prefix="/query", tags=["智能查询"])

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str
    image_base64: Optional[str] = None

class QueryResponse(BaseModel):
    """查询响应模型"""
    success: bool
    message: str
    original_question: Optional[str] = None
    translated_question: Optional[str] = None
    answer: Optional[str] = None
    search_count: Optional[int] = None
    search_results: Optional[list] = None
    step: Optional[str] = None

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest) -> QueryResponse:
    """
    智能查询接口
    
    支持多语言输入，自动翻译、向量检索和VL回答
    
    Args:
        request: 包含用户问题和可选图片的请求
        
    Returns:
        查询结果
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        logger.info(f"收到查询请求: {request.question[:100]}...")
        
        # 调用查询服务处理
        result = process_query(request.question, request.image_base64)
        
        return QueryResponse(
            success=result["success"],
            message=result["message"],
            original_question=result.get("original_question"),
            translated_question=result.get("translated_question"),
            answer=result.get("answer"),
            search_count=result.get("search_count"),
            search_results=result.get("search_results"),
            step=result.get("step")
        )
        
    except Exception as e:
        error_msg = f"查询处理失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/health")
async def query_health_check() -> Dict[str, str]:
    """
    查询服务健康检查
    """
    return {"status": "healthy", "service": "query"} 