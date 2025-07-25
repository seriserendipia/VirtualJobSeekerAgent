# 📬 Virtual Job Seeker Agent (Powered by Aurite)

本项目是一个基于 **Aurite 框架** 构建的智能求职助手，能够根据用户的简历和职位描述自动生成一封专业的 **跟进邮件（follow-up email）**，并支持通过 MCP（如 Gmail 工具）自动发送。

---

## 项目已迁移至 Aurite 架构

| 文件名 | 职责说明 | 类型 |
|--------|-----------|------|
| `main.py` | 项目主入口，注册 LLM 与 Agent，加载简历与 JD，生成邮件并通过 MCP 自动发送 | ✅ 命令行交互脚本 |
| `followup_email_agent.py` | 定义结构化邮件生成 Agent，基于简历与 JD 输出 JSON 格式邮件内容 | ✅ Aurite Agent 配置 |
| `server.py` | 启动 Flask 服务，提供 `/send-email` 和 `/test` 接口，通过 MCP 调用 Gmail 客户端发送邮件 | ✅ 后端接口模块 |

## 环境配置

1. 在根目录下创建 `.env` 文件并设置以下环境变量
![env_screenshot](./env_screenshot.png)
```env
OPENAI_API_KEY=your_openai_key_here
SMITHERY_API_KEY=your_smithery_key_here
```
2. 安装依赖
```bash
pip install aurite==0.3.18 openai python-dotenv flask flask-cors
```
## 运行
```bash
python backend/main.py
```
流程说明：

自动读取 samples/ 文件夹中的简历和 JD；

调用 Aurite agent 生成结构化邮件内容（subject + body）；

用户输入邮箱地址，自动调用 MCP 发送邮件。