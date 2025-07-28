@echo off
chcp 65001 >nul

echo ==========================================
echo 启动 FastAPI PDF处理服务
echo ==========================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

REM 检查Poetry环境
poetry --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Poetry环境，请先安装Poetry
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "config.toml" (
    echo 错误: 未找到配置文件 config.toml
    pause
    exit /b 1
)

echo 正在检查依赖...
poetry install

echo 正在启动服务器...
poetry run python run.py

echo 服务器已启动完成！
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
pause 