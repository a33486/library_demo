#!/usr/bin/env python3
"""
配置文件管理服务
提供统一的配置文件读取和管理功能
"""
import tomllib
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载完整的配置文件
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含所有配置的字典
    
    Raises:
        FileNotFoundError: 当配置文件不存在时
        tomllib.TOMLDecodeError: 当配置文件格式错误时
    """
    if config_path is None:
        # 从当前文件位置找到项目根目录的config.toml
        config_path = Path(__file__).parent / "config.toml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
        
        logger.info(f"成功加载配置文件: {config_path}")
        logger.debug(f"配置内容: {config_data}")
        
        return config_data
        
    except tomllib.TOMLDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        raise
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        raise


def get_config_section(section_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    获取配置文件中的特定节
    
    Args:
        section_name: 配置节名称，如 'server', 'database', 'app' 等
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        指定配置节的内容字典
    
    Raises:
        KeyError: 当指定的配置节不存在时
    """
    config_data = load_config(config_path)
    
    if section_name not in config_data:
        logger.warning(f"配置节 '{section_name}' 不存在，返回空字典")
        return {}
    
    section_data = config_data[section_name]
    logger.debug(f"获取配置节 '{section_name}': {section_data}")
    
    return section_data


def get_config_value(
    section_name: str, 
    key: str, 
    default_value: Any = None, 
    config_path: Optional[str] = None
) -> Any:
    """
    获取配置文件中的特定值
    
    Args:
        section_name: 配置节名称
        key: 配置项名称
        default_value: 默认值，当配置项不存在时返回
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        配置项的值，如果不存在则返回默认值
    """
    try:
        section_data = get_config_section(section_name, config_path)
        value = section_data.get(key, default_value)
        
        logger.debug(f"获取配置值 [{section_name}].{key} = {value}")
        return value
        
    except Exception as e:
        logger.warning(f"获取配置值失败 [{section_name}].{key}: {e}")
        return default_value


def get_server_config(config_path: Optional[str] = None) -> Dict[str, Union[str, int, bool]]:
    """
    获取服务器配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含服务器配置的字典，包含默认值
    """
    try:
        server_config = get_config_section("server", config_path)
        
        # 设置默认值
        config_with_defaults = {
            "host": server_config.get("host", "0.0.0.0"),
            "port": server_config.get("port", 8000),
            "reload": server_config.get("reload", True),
            "workers": server_config.get("workers", 1),
            "log_level": server_config.get("log_level", "info")
        }
        
        logger.info(f"服务器配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取服务器配置失败: {e}，使用默认配置")
        return {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": True,
            "workers": 1,
            "log_level": "info"
        }


def get_storage_config(config_path: Optional[str] = None) -> Dict[str, Union[str, int]]:
    """
    获取存储配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含存储配置的字典，包含默认值
    """
    try:
        storage_config = get_config_section("storage", config_path)
        
        config_with_defaults = {
            "pdf_upload_path": storage_config.get("pdf_upload_path", "./data/uploads"),
            "result_path": storage_config.get("result_path", "./data/results"),
            "max_file_size": storage_config.get("max_file_size", 50)
        }
        
        logger.info(f"存储配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取存储配置失败: {e}，使用默认配置")
        return {
            "pdf_upload_path": "./data/uploads",
            "result_path": "./data/results",
            "max_file_size": 50
        }


def get_app_config(config_path: Optional[str] = None) -> Dict[str, Union[str, bool]]:
    """
    获取应用配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含应用配置的字典，包含默认值
    """
    try:
        app_config = get_config_section("app", config_path)
        
        config_with_defaults = {
            "name": app_config.get("name", "PDF处理服务"),
            "version": app_config.get("version", "0.1.0"),
            "description": app_config.get("description", "基于FastAPI的PDF文档处理服务"),
            "debug": app_config.get("debug", False)
        }
        
        logger.info(f"应用配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取应用配置失败: {e}，使用默认配置")
        return {
            "name": "PDF处理服务",
            "version": "0.1.0", 
            "description": "基于FastAPI的PDF文档处理服务",
            "debug": False
        }


def get_api_config(config_path: Optional[str] = None) -> Dict[str, Union[str, list]]:
    """
    获取API配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含API配置的字典，包含默认值
    """
    try:
        api_config = get_config_section("api", config_path)
        
        config_with_defaults = {
            "prefix": api_config.get("prefix", "/api/v1"),
            "cors_origins": api_config.get("cors_origins", ["*"]),
            "cors_methods": api_config.get("cors_methods", ["GET", "POST", "PUT", "DELETE"]),
            "cors_headers": api_config.get("cors_headers", ["*"])
        }
        
        logger.info(f"API配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取API配置失败: {e}，使用默认配置")
        return {
            "prefix": "/api/v1",
            "cors_origins": ["*"],
            "cors_methods": ["GET", "POST", "PUT", "DELETE"],
            "cors_headers": ["*"]
        }


def get_embedding_config(config_path: Optional[str] = None) -> Dict[str, Union[str]]:
    """
    获取向量模型配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含向量模型配置的字典，包含默认值
    """
    try:
        embedding_config = get_config_section("external_services", config_path)
        
        config_with_defaults = {
            "embedding_model_path": embedding_config.get("embedding_model_path", "/bge-large-zh-v1.5"),
            "chroma_host": embedding_config.get("chroma_host", "localhost"),
            "chroma_port": embedding_config.get("chroma_port", 8000)
        }
        
        logger.info(f"向量模型配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取向量模型配置失败: {e}，使用默认配置")
        return {
            "embedding_model_path": "/bge-large-zh-v1.5",
            "chroma_host": "localhost",
            "chroma_port": 8000
        }


def get_logging_config(config_path: Optional[str] = None) -> Dict[str, Union[str]]:
    """
    获取日志配置
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的config.toml
    
    Returns:
        包含日志配置的字典，包含默认值
    """
    try:
        logging_config = get_config_section("logging", config_path)
        
        config_with_defaults = {
            "level": logging_config.get("level", "INFO"),
            "format": logging_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"),
            "file_path": logging_config.get("file_path", "./logs/app.log"),
            "rotation": logging_config.get("rotation", "1 day"),
            "retention": logging_config.get("retention", "30 days")
        }
        
        logger.info(f"日志配置: {config_with_defaults}")
        return config_with_defaults
        
    except Exception as e:
        logger.warning(f"获取日志配置失败: {e}，使用默认配置")
        return {
            "level": "INFO",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            "file_path": "./logs/app.log",
            "rotation": "1 day",
            "retention": "30 days"
        }


def validate_config() -> bool:
    """
    验证配置文件的完整性和正确性
    
    Returns:
        配置文件是否有效
    """
    try:
        config_data = load_config()
        
        # 检查必需的配置节是否存在
        required_sections = ["app", "server", "storage"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config_data:
                missing_sections.append(section)
        
        if missing_sections:
            logger.warning(f"缺少必需的配置节: {missing_sections}")
            return False
        
        # 检查服务器配置的端口是否有效
        server_config = config_data.get("server", {})
        port = server_config.get("port", 8000)
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error(f"无效的端口号: {port}")
            return False
        
        # 检查存储路径配置
        storage_config = config_data.get("storage", {})
        paths_to_check = ["pdf_upload_path", "result_path"]
        
        for path_key in paths_to_check:
            path_value = storage_config.get(path_key)
            if path_value:
                path_obj = Path(path_value)
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.warning(f"无法创建目录 {path_value}: {e}")
        
        logger.info("配置文件验证通过")
        return True
        
    except Exception as e:
        logger.error(f"配置文件验证失败: {e}")
        return False 