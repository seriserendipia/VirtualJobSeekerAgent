# Chrome Extension + Python Backend 

## 目录结构
- extension/  Chrome扩展前端
- backend/    Python后端

## 项目任务分拆

### 后端
- 提供本地 HTTP 服务，监听 5000 端口的上传内容。
- 接收前端上传（先用示例数据）的简历文件和岗位描述文本。
- 示例数据：`samples/user_resume_sample.txt` 和 `samples/jobdescription_sample.txt`。
- 将简历和岗位描述发送给大语言模型（如 OpenAI GPT）。
- 获取大语言模型生成的邮件内容
- 用 mcp 发送邮件并将结果返回给前端。


### 前端（Chrome Extension）
- 支持用户上传本地简历文件，并保存在 chrome extension storage 里
- 在领英岗位页面，自动获取岗位描述内容。
- 将简历和岗位描述通过 HTTP 请求发送到本地后端（localhost:5000）。
- 接收后端返回的大语言模型生成的邮件内容，并展示给用户。

## 启动方式
1.1. **命令行启动后端**  
    进入 `backend/` 目录，运行 `python server.py` 启动后端服务。

1.2. **通过 VS Code 任务启动后端**  
    在 VS Code 顶部菜单点击“终端” → “运行任务...”，在弹出的任务列表中选择“Run Python Backend”，回车即可启动后端服务。
2. 在Chrome扩展管理页面加载 extension/ 目录
3. 点击扩展弹窗按钮，前端会通过 `fetch` 请求访问本地 5000 端口，后端监听5000端口，并从5000端口发送信息给前端。

> **说明：**  
> - 后端（`server.py`）会一直监听本地 5000 端口。  
> - 只有当前端（Chrome 扩展）点击按钮时，前端的 JS 代码才会通过 HTTP 请求访问后端。  
> - 此时后端才会响应，并返回 “Hello from Python backend！”

## 注意事项
- Python后端仅为演示，未做多线程/异常处理。
- 前端与后端通信需允许CORS，生产环境请加强安全性。
