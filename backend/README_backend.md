# 项目说明

本项目包含两个核心 Python 文件，配合使用 OpenAI API 来自动生成基于简历和职位描述的跟进邮件，并将邮件内容以结构化 JSON 格式输出。

---

## 先决条件

1. 创建 `.env` 文件，添加你的 OpenAI API 密钥

   ![1](E:\Project\VirtualJobSeekerAgent\backend\1.png)

1. 安装依赖库：

```bash
pip install openai python-dotenv
pip install mcp google-auth google-auth-oauthlib google-api-python-client
```

# 文件说明

本项目需配合使用 OpenAI API 来自动生成基于简历和职位描述的跟进邮件，并将邮件内容以结构化 JSON 格式输出。

## 1.  `llm_service.py`

负责初始化 OpenAI 客户端，自动检测运行环境（Colab / 本地），并测试 API key 是否可用。

### 主要功能

- 自动从 本地 `.env` 文件加载 `OPENAI_API_KEY`
- 连接并测试 OpenAI API
- 返回已初始化的 OpenAI 客户端实例

### 运行方式

```

python llm_service.py
```

执行后会测试 API key 是否有效，并打印响应。

------

## 2. `generate_followup_email.py`

根据简历文件和职位描述文件内容，调用 OpenAI GPT-4o 生成专业的跟进邮件，并提取邮件主题和正文，最后以 JSON 格式打印输出。

### 主要功能

- 读取指定路径的简历和职位描述文本文件
- 拼接提示词（prompt）并调用 GPT-4o 生成邮件内容
- 用正则表达式从 GPT 返回文本中提取 `Subject` 和 `Body`
- 返回邮件内容的 JSON 字典格式

### 使用方法

```

python generate_followup_email.py
```

### 代码关键点

- 修改 `resume_path` 和 `jd_path` 为你本地的文件路径
- 邮件生成结果会以 JSON 格式打印，方便后续程序处理

------

## 示例输出

```
json{
    "subject": "Follow-Up on Quality Data Analyst Position Application",
    "body": "Dear [Recruiter's Name],\n\nI hope this message finds you well. I am writing to express my continued interest..."
}
```





```bash



```