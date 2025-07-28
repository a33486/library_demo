#!/bin/bash

# FastAPI应用启动脚本
# 使用配置文件中的设置启动服务器

echo "=========================================="
echo "启动 FastAPI PDF处理服务"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python环境"
    exit 1
fi

# 检查Poetry环境
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到Poetry环境，请先安装Poetry"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.toml" ]; then
    echo "错误: 未找到配置文件 config.toml"
    exit 1
fi

echo "正在检查依赖..."
poetry install

echo "正在启动服务器..."
poetry run python run.py

echo "服务器已启动完成！"
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs" 