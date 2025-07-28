from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.pdf_router import router as pdf_router
from app.routers.query_router import router as query_router
from loguru import logger
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入config_service
sys.path.append(str(Path(__file__).parent.parent))
from config_service import (
    get_app_config, 
    get_server_config, 
    get_api_config, 
    get_logging_config,
    get_storage_config,
    validate_config
)

# 获取配置
app_config = get_app_config()
api_config = get_api_config()
logging_config = get_logging_config()
server_config = get_server_config()
storage_config = get_storage_config()

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format=logging_config["format"],
    level=logging_config["level"]
)
logger.add(
    logging_config["file_path"],
    format=logging_config["format"],
    level=logging_config["level"],
    rotation=logging_config["rotation"],
    retention=logging_config["retention"]
)

# 创建FastAPI应用实例
app = FastAPI(
    title=app_config["name"],
    version=app_config["version"],
    description=app_config["description"],
    debug=app_config["debug"]
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config["cors_origins"],
    allow_credentials=True,
    allow_methods=api_config["cors_methods"],
    allow_headers=api_config["cors_headers"],
)

@app.get("/health")
def health_check() -> JSONResponse:
    """
    健康检查接口，返回应用状态信息。
    """
    return JSONResponse({
        "msg": "success",
        "app_name": app_config["name"],
        "version": app_config["version"],
        "status": "running"
    })

@app.get("/config")
def get_config_info() -> JSONResponse:
    """
    获取配置信息接口（仅用于调试）。
    """
    return JSONResponse({
        "server": server_config,
        "storage": storage_config,
        "api": api_config,
        "logging": logging_config
    })

# 包含路由
app.include_router(pdf_router, prefix=api_config["prefix"])
app.include_router(query_router, prefix=api_config["prefix"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    # 验证配置文件
    if not validate_config():
        logger.error("配置文件验证失败！")
        
    logger.info(f"应用 {app_config['name']} v{app_config['version']} 正在启动...")
    logger.info(f"服务器配置: {server_config['host']}:{server_config['port']}")
    logger.info(f"调试模式: {app_config['debug']}")
    logger.info(f"API前缀: {api_config['prefix']}")
    logger.info(f"存储路径: {storage_config['result_path']}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info(f"应用 {app_config['name']} 正在关闭...")
