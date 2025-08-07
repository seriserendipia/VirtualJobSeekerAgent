# VirtualJobSeekerAgent - AI求职助手

一个Chrome扩展 + Python后端的AI求职邮件生成工具，帮助在LinkedIn上生成专业的求职邮件。

## 🚀 快速开始




### 1. 环境配置
复制并编辑环境变量文件：
```bash
cp .env.example .env
```

在 `.env` 文件中填入您的API密钥：
```bash
OPENAI_API_KEY=sk-your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com # 下一步会获得
GMAIL_MCP_CREDS_PATH=PATH_TO_FILE #  下一步会获得....\credentials.json, downloaded from GCP after creating client
SMITHERY_API_KEY=your_smithery_api_key
SMITHERY_PROFILE_ID=your_smithery_profile_id
```

### 2. Google OAuth配置
1. 前往 [Google Cloud Console](https://console.cloud.google.com/) 
2. 创建OAuth 2.0客户端ID，应用类型选择"Chrome应用扩展程序"
3. 复制客户端ID到 `.env` 文件的 `GOOGLE_CLIENT_ID` 字段
5. 下载创建的 `credentials.json` 文件，复制 `credentials.json` 文件路径到 `.env` 文件的 `GMAIL_MCP_CREDS_PATH` 字段
4. 在Google Cloud Console中启用Gmail API并添加OAuth范围

### 3. 安装依赖
```bash
pip install Flask Flask-Cors aurite python-dotenv google-api-python-client google-auth-oauthlib google-auth-httplib2 google-auth
```

### 4. 构建扩展
运行构建脚本生成manifest.json：
```bash
python build_manifest.py
```
或直接运行：
```bash
start_dev.bat
```

### 5. 启动应用
1. **启动后端**：进入`backend/`目录，运行：
   ```bash
   python server.py
   ```
   
2. **加载Chrome扩展**：
   - 打开Chrome扩展管理页面
   - 开启"开发者模式"
   - 点击"加载已解压的扩展程序"
   - 选择`frontend/`目录

3. **使用**：打开LinkedIn职位页面，右侧会自动显示AI助手侧边栏

## 📁 项目结构
```
├── frontend/           # Chrome扩展前端
│   ├── manifest.template.json
│   ├── sidebar.html    # 侧边栏界面
│   ├── sidebar.js      # 前端逻辑
│   ├── content.js      # 内容脚本
│   └── sidebar.css     # 样式文件
├── backend/            # Python后端服务
│   ├── server.py       # Flask服务器
│   ├── generate_followup_email.py  # 邮件生成逻辑
│   ├── web_search_agent.py         # 招聘邮箱搜索
│   ├── email_handling.py           # 邮件发送功能
│   └── aurite_service.py           # Aurite实例管理
├── samples/            # 示例数据
└── build_manifest.py   # 构建脚本
```

## ✨ 主要功能

1. **智能邮件生成**：基于简历和职位描述生成个性化求职邮件
2. **邮件修改优化**：通过对话形式修改和完善邮件内容
3. **自动信息提取**：从LinkedIn页面自动提取公司名称和职位信息
4. **招聘邮箱搜索**：通过网络搜索查找招聘联系邮箱
5. **一键发送邮件**：通过Google Gmail API直接发送邮件

## 🔧 技术栈

**前端**：
- Chrome Extension (Manifest V3)
- Vanilla JavaScript
- HTML/CSS

**后端**：
- Python Flask
- Aurite (LLM代理框架)
- OpenAI GPT API
- Google Gmail API
- Smithery Exa (网络搜索)

## 📝 使用流程

1. 在LinkedIn职位页面打开扩展
2. 上传简历文件（支持PDF/TXT）
3. 系统自动提取职位信息
4. 点击"生成邮件"创建初始邮件
5. 通过聊天界面修改邮件内容
6. 搜索招聘联系邮箱（可选）
7. 一键发送邮件

## ⚠️ 注意事项

- 后端仅监听本地5000端口，仅供个人使用
- 发送邮件功能需要有效的Google OAuth配置
- 请确保API密钥的安全性，不要提交到版本控制
- 网络搜索功能需要Smithery API支持

## 🚧 已知限制

- 目前仅支持LinkedIn职位页面
- PDF文件解析功能有限
- 仅支持英文邮件生成
- 需要本地运行Python后端服务

## 📄 许可证

本项目采用 GPL-3.0 许可证，详见 [LICENSE](LICENSE) 文件。
