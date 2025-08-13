# VirtualJobSeekerAgent - AI Job Assistant

A Chrome extension + Python backend AI job application email generation tool that helps generate professional job application emails on LinkedIn.

## 🚀 Quick Start




### 1. Environment Setup
Copy and edit the environment variables file:
```bash
cp .env.example .env
```

Fill in your API keys in the `.env` file:
```bash
OPENAI_API_KEY=sk-your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com # will get this in next step
SMITHERY_API_KEY=your_smithery_api_key
SMITHERY_PROFILE_ID=your_smithery_profile_id
```

### 2. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/) 
2. Create OAuth 2.0 client ID, choose "Chrome Extension" as application type
3. Copy the client ID to the `GOOGLE_CLIENT_ID` field in `.env` file
4. Enable Gmail API in Google Cloud Console and add OAuth scopes

### 3. Install Dependencies
```bash
pip install Flask Flask-Cors aurite python-dotenv google-api-python-client google-auth-oauthlib google-auth-httplib2 google-auth
```

### 4. Build Extension
Run the build script to generate manifest.json:
```bash
python build_manifest.py
```
or run directly:
```bash
start_dev.bat
```

### 启动方式
1. 命令行启动后端  
    进入 `backend/` 目录，运行 `python server.py` 文件，启动后端服务
2. 进入Chrome扩展（也叫‘插件’）：在浏览器右上角，点击 'Extensions图标 ——— Manage Extensions'，进入'Extensions'，打开页面右上角开发者模式'Developer mode'，点击'Load unpacked'，加载 frontend/ 目录，可看到我们的'Job seeker agent 1.0'扩展成功导入
3. 打开Linkedin Job，应该会自动加载侧边栏
![扩展加载演示](Tutorial/1.png)
4. 上传简历，点击生成邮件，然后再点击发送（注意真的会发到email_content.json中指定的邮箱！）                                                              
![前后端交互演示](Tutorial/2.png)
![前后端交互演示](Tutorial/3.png)

（原理大致解释：前端会通过 `fetch` 请求访问本地 5000 端口，后端监听5000端口，并从5000端口发送信息给前端）

> **说明：**  
> - 后端（`server.py`）会一直监听本地 5000 端口。  
> - 只有当前端（Chrome 扩展）点击按钮时，前端的 JS 代码才会通过 HTTP 请求访问后端。  



### Railway 部署

1. **准备部署**：
   ```bash
   # 设置生产环境
   echo "ENVIRONMENT=production" >> .env
   python build_manifest.py
   ```

2. **Railway 配置**：
   - 连接GitHub仓库
   - 设置环境变量：
     ```
     ENVIRONMENT=production
     GOOGLE_CLIENT_ID=your-production-client-id
     OPENAI_API_KEY=your-openai-key
     ```

3. **自动部署**：
   - 推送代码到GitHub
   - Railway自动构建和部署



## 目录结构
- frontend/   Chrome扩展前端
- (已废除)extension/  Chrome扩展前端
- backend/    Python后端
- samples/    示例数据和对话样例（如：chatbot_dialog_sample.txt）


## 项目任务分拆

### 后端
- 提供本地 HTTP 服务，监听 5000 端口的上传内容。
- 接收前端上传（先用示例数据）的简历文件和岗位描述文本。
- 示例数据：`samples/user_resume_sample.txt` ，`samples/jobdescription_sample.txt`
- 将简历和岗位描述（system prompt），发送给大语言模型（如 OpenAI GPT），如果有用户提问的话，把用户提问的上下文一起发送给大语言模型
- 获取大语言模型生成的邮件内容
- 用 mcp 发送邮件并将结果返回给前端。



### 前端（Chrome Extension）
- 调研一下网上有什么chatbot frontend开源代码可以用在chrome extension里，选一个用
- 实现Chatbot基础界面，示例数据 amples/chatbot_dialog_sample.txt` 
- 支持用户上传本地简历文件，并保存在 chrome extension storage 里
- 在领英岗位页面，自动获取岗位描述内容。
- 将简历和岗位描述（system prompt），用户提问等，通过 HTTP 请求发送到本地后端（localhost:5000）。
- 接收后端返回的大语言模型生成的邮件内容，并展示给用户
- 一个发送邮件的按钮，接收后端的邮件是否发送成功的结果，并展示给用户

## 未来再做的

### 1. 支持多用户的远程服务器部署(不做了暂时)
- 将 Python 后端部署到云服务器（如 AWS、阿里云、腾讯云等），开放公网端口，支持多个用户同时访问，记得更新 gcp 授权的重定向链接

### 2. 邮件发送功能（这个要做）
- 发邮件时提示用户有多个可能的收件人，给用户选择


### 数据追踪与用户历史面板（不做了暂时）
- 前端增加“数据追踪”面板，展示用户已申请岗位数量、已发送邮件数量等历史数据。
- 每次用户成功申请岗位或发送邮件后，前端将相关数据记录到 Chrome extension storage。
- 数据追踪面板可随时查看历史统计信息，便于用户了解自己的求职进展。
- 前端根据用户的求职历史，自动判断是否需要进行 follow up，并通过 HTTP 请求通知后端。
- 后端收到请求后，生成并推送 follow up 邮件提醒，提升用户的跟进效率。


## 注意事项
- Python后端仅为演示，未做多线程/异常处理。
- 前端与后端通信需允许CORS，生产环境请加强安全性。
### 5. Start Application
1. **Start Backend**: Go to `backend/` directory and run:
   ```bash
   python server.py
   ```
   
2. **Load Chrome Extension**:
   - Open Chrome extension management page
   - Enable "Developer mode"
   - Click "Load unpacked extension"
   - Select the `frontend/` directory

3. **Usage**: Open LinkedIn job page, the AI assistant sidebar will automatically appear on the right

## 📁 Project Structure
```
├── frontend/           # Chrome extension frontend
│   ├── manifest.template.json
│   ├── sidebar.html    # Sidebar interface
│   ├── sidebar.js      # Frontend logic
│   ├── content.js      # Content script
│   └── sidebar.css     # Style files
├── backend/            # Python backend service
│   ├── server.py       # Flask server
│   ├── generate_followup_email.py  # Email generation logic
│   ├── web_search_agent.py         # Recruiter email search
│   ├── email_handling.py           # Email sending functionality
│   └── aurite_service.py           # Aurite instance management
├── samples/            # Sample data
└── build_manifest.py   # Build script
```

## ✨ Main Features

1. **Smart Email Generation**: Generate personalized job application emails based on resume and job description
2. **Email Modification**: Modify and improve email content through conversational interface
3. **Auto Information Extraction**: Automatically extract company name and job information from LinkedIn pages
4. **Recruiter Email Search**: Find recruiter contact emails through web search
5. **One-click Email Sending**: Send emails directly through Google Gmail API

## 🔧 Tech Stack

**Frontend**:
- Chrome Extension (Manifest V3)
- Vanilla JavaScript
- HTML/CSS

**Backend**:
- Python Flask
- Aurite (LLM Agent Framework)
- OpenAI GPT API
- Google Gmail API
- Smithery Exa (Web Search)

## 📝 Usage Flow

1. Open the extension on LinkedIn job pages
2. Upload resume file (supports PDF/TXT)
3. System automatically extracts job information
4. Click "Generate Email" to create initial email
5. Modify email content through chat interface
6. Search for recruiter contact email (optional)
7. Send email with one click

## ⚠️ Important Notes

- Backend only listens on local port 5000, for personal use only
- Email sending functionality requires valid Google OAuth configuration
- Ensure API key security, do not commit to version control
- Web search functionality requires Smithery API support

## 🚧 Known Limitations

- Currently only supports LinkedIn job pages
- Limited PDF file parsing capability
- Only supports English email generation
- Requires running Python backend service locally

## 📄 License

This project is licensed under GPL-3.0 license, see [LICENSE](LICENSE) file for details.
