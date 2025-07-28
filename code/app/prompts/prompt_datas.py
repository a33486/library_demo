
PRODUCT_INFORMATION = "请提取图片中的产品信息"

DOCUMENT_INTEGRATION_PROMPT = "请帮忙整合以下文档 {document_content}"

DOCUMENT_INTEGRATION_PROMPT_SYSTEM = "你是一个文档处理员"

# 翻译相关提示词
TRANSLATION_PROMPT = "请将以下内容翻译成中文，只返回翻译结果，不要添加任何解释：{content}"

TRANSLATION_SYSTEM = "你是一个专业的翻译助手，请将用户输入的内容准确翻译成中文。"

# 查询相关提示词
QUERY_ANSWER_PROMPT = "基于以下检索到的文档内容，回答用户的问题。如果文档内容不足以回答问题，请说明。\n\n用户问题：{user_question}\n\n检索到的文档内容：{retrieved_content}"

QUERY_ANSWER_SYSTEM = "你是一个专业的文档问答助手，请基于提供的文档内容准确回答用户问题。"

