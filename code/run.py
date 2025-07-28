#!/usr/bin/env python3
"""
FastAPI应用启动脚本
"""
import uvicorn
from loguru import logger
from config_service import get_server_config, get_app_config, validate_config

def main():
    """主启动函数"""
    # 验证配置文件
    if not validate_config():
        logger.error("配置文件验证失败，程序退出")
        return
    
    # 获取应用和服务器配置
    app_config = get_app_config()
    server_config = get_server_config()
    
    logger.info(f"正在启动 {app_config['name']} v{app_config['version']}")
    logger.info(f"服务器配置: {server_config['host']}:{server_config['port']}")
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=server_config["host"],
        port=server_config["port"],
        reload=server_config["reload"],
        log_level=server_config["log_level"]
    )

if __name__ == "__main__":
    main() 