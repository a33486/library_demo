# FastAPI PDF智能处理服务

基于FastAPI的智能PDF文档处理服务，支持PDF文件上传、视觉语言识别、向量化存储和智能问答。

## 功能特性

- **PDF文件处理**: PDF上传、分页、图片提取
- **视觉语言识别**: 使用VL模型识别PDF页面内容
- **向量化存储**: 使用BGE模型将文档内容向量化存储到Chroma数据库
- **智能问答**: 支持多语言查询，自动翻译、向量检索和VL回答
- **文档整合**: 使用VLLM框架整合文档内容
- **RESTful API接口**: 完整的API接口支持
- **配置文件管理**: 统一的配置管理
- **日志记录**: 详细的日志记录
- **CORS支持**: 跨域请求支持

## 项目结构

```
code/
├── app/
│   ├── main.py                    # FastAPI应用主文件
│   ├── prompts/
│   │   └── prompt_datas.py        # 提示词配置
│   ├── routers/                   # 路由模块
│   │   ├── pdf_router.py          # PDF处理路由
│   │   └── query_router.py        # 智能查询路由
│   └── services/                  # 服务模块
│       ├── pdf_service.py         # PDF处理服务
│       ├── get_vl_data.py         # 视觉语言识别服务
│       ├── get_embeddings.py      # 向量化服务
│       ├── document_integration_service.py  # 文档整合服务
│       └── query_service.py       # 智能查询服务
├── config.toml                    # 应用配置文件
├── config_service.py              # 配置管理服务
├── run.py                         # 启动脚本
├── start.sh                       # Linux/macOS启动脚本
├── start.bat                      # Windows启动脚本
├── pyproject.toml                 # Poetry项目配置
└── README.md                      # 项目说明文档
```

## 配置文件说明

项目使用 `config.toml` 文件进行配置管理，包含以下配置项：

### 应用配置 (app)
- `name`: 应用名称
- `version`: 应用版本
- `description`: 应用描述
- `debug`: 调试模式开关

### 服务器配置 (server)
- `host`: 服务器监听地址
- `port`: 服务器端口
- `reload`: 自动重载开关
- `workers`: 工作进程数
- `log_level`: 日志级别

### 存储配置 (storage)
- `pdf_upload_path`: PDF文件上传路径
- `result_path`: 处理结果存储路径
- `max_file_size`: 最大文件大小(MB)

### 外部服务配置 (external_services)
- `vl_api_url`: 视觉语言模型API地址
- `vllm_api_url`: 大语言模型PI地址
- `embedding_model_path`: 向量模型路径
- `chroma_host`: Chroma数据库主机
- `chroma_port`: Chroma数据库端口

### 日志配置 (logging)
- `level`: 日志级别
- `format`: 日志格式
- `file_path`: 日志文件路径
- `rotation`: 日志轮转周期
- `retention`: 日志保留时间

### API配置 (api)
- `prefix`: API前缀
- `cors_origins`: 跨域允许的源
- `cors_methods`: 允许的HTTP方法
- `cors_headers`: 允许的HTTP头

## 安装和运行

### 环境要求

- Python 3.11+
- Poetry
- VLLM框架服务
- Chroma向量数据库

### 安装依赖

```bash
poetry install
```

### 启动服务

#### 方法1: 使用启动脚本

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

#### 方法2: 直接运行

```bash
poetry run python run.py
```

#### 方法3: 使用uvicorn

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 6677 --reload
```

### 访问服务

- 应用地址: http://localhost:6677
- API文档: http://localhost:6677/docs
- 健康检查: http://localhost:6677/health
- 配置信息: http://localhost:6677/config

## API接口

### 健康检查
- `GET /health` - 应用健康状态检查

### 配置信息
- `GET /config` - 获取当前配置信息（调试用）

### PDF处理
- `POST /api/v1/pdf/upload` - 上传PDF文件进行处理
- `GET /api/v1/pdf/list` - 获取PDF文件列表
- `GET /api/v1/pdf/{file_id}` - 获取PDF文件详情

### 智能查询
- `POST /api/v1/query/ask` - 智能问答接口
- `GET /api/v1/query/health` - 查询服务健康检查

## 核心功能详解

### 1. PDF处理流程

1. **PDF上传**: 接收PDF文件并计算MD5值
2. **页面分割**: 将PDF按页分割成图片
3. **视觉识别**: 使用VL模型识别每页内容
4. **向量化存储**: 将识别内容向量化存储到Chroma数据库
5. **文档整合**: 使用大语言模型整合所有页面内容

### 2. 智能查询流程

1. **多语言输入**: 支持各种语言的用户问题
2. **自动翻译**: 使用语言模型将问题翻译成中文
3. **向量检索**: 在Chroma数据库中检索相似文档
4. **VL回答**: 使用VL模型生成答案
5. **结果返回**: 返回完整的查询结果

### 3. 向量化存储

- 使用BGE-large-zh-v1.5模型进行文本向量化
- 支持文本分割和重叠处理
- 自动持久化到本地Chroma数据库
- 提供相似性搜索功能

## 使用示例

### PDF处理

```bash
# 上传PDF文件
curl -X POST http://localhost:6677/api/v1/pdf/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 智能查询

```bash
# 文本查询
curl -X POST http://localhost:6677/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the product information?",
    "image_base64": null
  }'

# 带图片的查询
curl -X POST http://localhost:6677/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is shown in this image?",
    "image_base64": "base64_encoded_image_data"
  }'
```

## 配置修改

修改 `config.toml` 文件中的配置项，重启服务即可生效：

```toml
[server]
host = "127.0.0.1"  # 修改监听地址
port = 8080         # 修改端口

[external_services]
vl_api_url = "http://your-vl-service:port/api"  # 修改VL服务地址
vllm_api_url = "http://your-vllm-service:port/v1/chat/completions"  # 修改VLLM服务地址
embedding_model_path = "/path/to/your/model"  # 修改向量模型路径
```

## 日志

应用日志会同时输出到控制台和文件：
- 控制台: 实时显示
- 文件: `./logs/app.log`

日志配置可在 `config.toml` 中修改。

## 开发

### 代码结构

- `app/main.py`: FastAPI应用主文件，包含中间件和路由注册
- `config_service.py`: 配置管理服务
- `app/services/`: 核心业务逻辑服务
- `app/routers/`: API路由定义
- `app/prompts/`: 提示词配置

### 添加新功能

1. 在 `app/services/` 中添加新的服务模块
2. 在 `app/routers/` 中添加对应的路由
3. 在 `app/main.py` 中注册新路由
4. 在 `config.toml` 中添加相关配置

## 依赖服务

- **VLLM框架**: 提供语言模型服务
- **Chroma数据库**: 向量数据库存储
- **BGE模型**: 文本向量化模型

## 许可证

MIT License

## other
1.全文总结 (Full-text Summarization): 提供一个功能，可以为上传的 PDF 文档生成一份高质量的摘要。 （demo实现）
    实现方式 把传入的pdf切割成png文件 请求vl模型获取内容，然后把内容整合，使用大预言模型生成文档摘要

    
2.跨文档关联问答: 用户提出的问题，系统应能整合来自**所有数据源（PDF 文本、表格、CSV、图像）**的信息来 （未作）
    实现方式 文档提取产品信息存入关系型数据库里面进行模糊匹配检索，表格或产品的文本不推荐使用向量检索，因为检索出内容不准确

    
3.全文翻译与跨语言问答 (Translation & Cross-lingual Q&A)。（demo实现）
    实现方式 首先把用户问题使用大语言模型转换成中文 然后使用中文进行向量检索，然后找到对应的图片（推荐s3），把对应的图片和用户问题输入给大模型获取答案
