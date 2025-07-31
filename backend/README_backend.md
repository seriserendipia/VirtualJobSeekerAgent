# 一、项目说明

这是一个基于 Python Flask 框架和 Aurite Agent 框架构建的后端服务，主要用于自动化求职流程中的邮件生成、修改和招聘者信息查找。

# 二、功能概述 
核心功能：
* **智能邮件生成**：根据用户简历和职位描述，通过 AI 生成个性化的求职跟进邮件。
* **多轮邮件修改**：支持用户对 AI 生成的邮件进行多轮反馈和修改，直至满意。
* **招聘者信息查找**：
    * **JD 内置邮箱提取**：优先从职位描述 (JD) 中直接提取招聘者邮箱。
    * **智能网页搜索**：如果 JD 中没有找到邮箱，则自动触发网页搜索 Agent，通过 Smithery Exa MCP Server 全网查找公司招聘者的邮箱或相关联系页面（例如领英个人主页）。
* **邮件发送**：通过 Google Gmail API 实现邮件的 OAuth 认证发送。


# 三、先决条件

1. 创建 `.env` 文件，添加
```bash
OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY"
SMITHERY_API_KEY="YOUR_SMITHERY_API_KEY"
SMITHERY_PROFILE_ID="YOUR_SMITHERY_PROFILE_ID_IF_NEEDED"
```

2. 安装依赖库：

```bash
pip install Flask Flask-Cors aurite python-dotenv google-api-python-client google-auth-oauthlib google-auth-httplib2 google-auth termcolor
```

# 四、后端模块功能总览
| 文件名 | 角色/定位 | 主要职责与功能 | 包含的核心 Agent/类/函数 | 关联文件/依赖 |
|--------|------------|----------------|----------------------------|----------------|
| `server.py` | API 网关 / 业务流程协调器 | - 接收前端 HTTP 请求，定义 API 路由 (`/generate_email`, `/modify_email`, `/send-email` 等) <br> - 根据请求类型协调各 Agent 和服务，处理业务流程 <br> - 处理通用请求验证和错误响应 <br> - 在应用启动时一次性注册 Aurite Agent 和 Client 配置 | `Flask` 应用实例, `handle_generate_email()`, `handle_modify_email()`, `validate_request()`, `handle_send_email()` | `generate_followup_email.py`, `web_search_agent.py`, `email_handling.py`, `aurite_service.py`, `mcp.types` |
| `generate_followup_email.py` | 邮件生成/修改 Agent | - 加载简历和 JD 文件内容 <br> - 解析 AI 生成的邮件文本到 JSON <br> - 尝试从 JD 中提取邮箱、公司名、职位名 <br> - 如果 JD 中有邮箱，调用 OpenAI LLM（Email Generate Agent）生成邮件 <br> - 提供 `modify_email` 功能，通过 Email Modifier Agent 修改邮件 | `load_files()`, `parse_email_to_json()`, `extract_email_from_jd()`, `extract_company_name_from_jd()`, `extract_job_title_from_jd()`, `generate_email()`（Agent 1 逻辑）, `modify_email()`（Agent X）, `fast_llm`（LLM 配置） | `aurite.py`, `aurite_service.py`, `dotenv` |
| `web_search_agent.py` | 招聘者邮箱搜索 Agent | - 设置 Aurite MCP Client 连接 Smithery Exa 服务 <br> - 定义 Recruiter Email Search Agent，其 `system_prompt` 指导 LLM 使用 `web_search_exa` 工具进行搜索 <br> - 运行 Agent 获取搜索结果，并从中解析提取招聘者邮箱或相关 LinkedIn/官网 URL <br> - 不再直接使用 `exa-py` 库执行搜索，而是通过 MCP Server 间接调用 | `setup_aurite_for_recruiter_search()`, `find_recruiter_email_via_web_search()`（Agent 2）, `recruiter_llm_config`（LLM 配置）, `exa_recruiter_mcp_client_config`（MCP Client 配置）, `recruiter_search_agent_config`（Agent 配置） | `aurite.py`, `aurite_service.py`, `dotenv`, `os`, `json`, `re` |
| `email_handling.py` | 邮件发送服务 | - 使用 Google OAuth 访问令牌创建 Gmail API 服务 <br> - 构建符合 Gmail API 要求的邮件消息格式 <br> - 执行邮件发送操作 <br> - 提供异步接口 `send_email_via_aurite` 供其他模块调用 | `create_gmail_service()`, `create_message()`, `send_message()`, `send_email_via_aurite()` | `google.oauth2.credentials`, `googleapiclient.discovery`, `asyncio`, `base64` |
| `aurite_service.py` | Aurite 单例管理 | - 提供 Aurite 框架的单例实例 <br> - 确保整个应用共享同一个 Aurite 实例，便于 Agent 和 Client 的注册与管理 | `_aurite_instance`, `get_aurite()` | `aurite.py` |
| `llm_service.py` | LLM 客户端初始化 | - 初始化 OpenAI LLM 客户端 <br> - 处理 API 密钥加载（支持 Colab 或 `.env`） <br> - 进行简单的 API 连接测试 <br> - 返回可用的 OpenAI 客户端对象 | `init_openai_client()` | `openai`, `os`, `dotenv`（如果不在 Colab） |
