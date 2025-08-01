# 🚀 VirtualJobSeekerAgent 云端部署完整指南

本指南将带您完成从本地开发到Railway云端部署的完整流程。

## 🎯 为什么选择Railway？

- ✅ **最简单**: GitHub连接，一键部署
- ✅ **免费够用**: 每月500小时 (约20天24小时运行)
- ✅ **自动HTTPS**: 安全访问
- ✅ **固定域名**: 不用担心IP变化

## 📋 完整部署步骤

### 第一步: 修改代码适应云端环境

#### ✅ 1.1 修改后端服务器配置

编辑 `backend/server.py`，找到文件末尾的启动配置并修改：

**当前配置 (本地):**
```python
if __name__ == '__main__':
    print("🚀 后端服务器启动在: http://localhost:5000")
    
    # NEW: Run Aurite setup once at application startup
    import asyncio
    asyncio.run(setup_aurite_for_recruiter_search())
    
    app.run(host='127.0.0.1', port=5000, debug=True)
```

**修改为 (云端):**
```python
if __name__ == '__main__':
    import os
    HOST = '0.0.0.0'  # 允许外部访问
    PORT = int(os.environ.get('PORT', 5000))  # Railway会提供PORT环境变量
    
    print(f"🚀 云服务器启动在: {HOST}:{PORT}")
    
    # NEW: Run Aurite setup once at application startup
    import asyncio
    asyncio.run(setup_aurite_for_recruiter_search())
    
    app.run(host=HOST, port=PORT, debug=False)  # 生产环境关闭debug
```

#### ✅ 1.2 优化CORS配置 (预设Railway URL)

**💡 Railway URL 预测规则:**
- 格式：`https://项目名-production.up.railway.app`
- 您的项目：`https://virtualjobseekeragent-production.up.railway.app`

在 `backend/server.py` 中找到CORS配置并修改：

**当前配置:**
```python
CORS(app) # Enable CORS for all routes
```

**修改为 (直接使用预测的Railway URL):**
```python
from flask_cors import CORS

CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",  # 本地开发
            "https://virtualjobseekeragent-production.up.railway.app",  # 预测的Railway URL
            "chrome-extension://*",  # Chrome扩展
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-From-Extension"]
    }
})
```

#### ✅ 1.3 创建前端配置文件 (预设Railway URL)

创建 `frontend/config.js`:
```javascript
// 服务器配置管理
const SERVER_CONFIG = {
    LOCAL: "http://localhost:5000",
    RAILWAY: "https://virtualjobseekeragent-production.up.railway.app",  // 预测的Railway URL
    CURRENT: "RAILWAY"  // 直接切换到云端模式
};

// 获取当前服务器地址
function getServerUrl() {
    return SERVER_CONFIG[SERVER_CONFIG.CURRENT];
}

// 导出配置 (如果需要)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SERVER_CONFIG, getServerUrl };
}
```

**💡 为什么可以预测URL？**
- Railway 使用固定的命名规则
- 格式：`项目名-production.up.railway.app`
- 99% 情况下都是这个格式
- 如果不匹配，稍后快速修改一次即可

#### ✅ 1.4 更新前端请求地址

编辑 `frontend/sidebar.js`，在文件开头添加配置引用：

**在文件开头添加:**
```javascript
// 引入配置文件 (确保config.js先加载)
const SERVER_URL = getServerUrl();
```

**找到所有硬编码的请求地址并替换:**
```javascript
// 旧的硬编码方式 ❌
// const res = await fetch("http://localhost:5000/generate_email", {

// 新的动态配置方式 ✅
const res = await fetch(`${SERVER_URL}/generate_email`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
    },
    body: JSON.stringify(payload)
});
```

#### ✅ 1.5 更新扩展清单文件

编辑 `frontend/sidebar.html`，在 `<head>` 部分添加配置文件引用：

```html
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="sidebar.css">
    <!-- 先加载配置文件 -->
    <script src="config.js"></script>
</head>
```

### 第二步: 创建部署文件

#### ✅ 2.1 创建依赖文件

**方法一: 手动创建精简版本 (推荐)**

在项目根目录创建 `requirements.txt`:
```txt
# 核心 Web 框架
Flask==3.1.1
Flask-CORS==6.0.1

# 环境变量管理
python-dotenv==1.1.1

# Google API (Gmail功能)
google-api-python-client==2.176.0
google-auth==2.40.3
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.2

# AI 和 MCP
aurite==0.3.27
mcp==1.11.0

# 网络请求
requests==2.32.4
requests-oauthlib==2.0.0

# OpenAI (如果使用)
openai==1.97.1
```

**方法二: 从 Anaconda 环境导出 (包含所有依赖)**

首先激活环境并导出：
```bash
conda activate agent_env
pip freeze > requirements_full.txt
```

然后可以手动精简或直接使用完整版本。

#### ✅ 2.2 创建启动配置

在项目根目录创建 `Procfile` (无扩展名):
```
web: python backend/server.py
```

#### ✅ 2.3 激活环境并测试依赖

```bash
# 激活 Anaconda 环境
conda activate agent_env

# 测试服务器是否能正常启动
python backend/server.py
```

如果遇到缺少的包，可以安装：
```bash
conda activate agent_env
pip install -r requirements.txt
```

#### ✅ 2.4 一次性提交到GitHub (包含完整配置)

```bash
# 激活 Anaconda 环境
conda activate agent_env

# 测试服务器是否能正常启动 (可选)
python backend/server.py

# 一次性提交所有配置
git add .
git commit -m "🚀 Deploy to Railway with complete cloud configuration"
git push origin main
```

**✅ 优势：**
- 🎯 **一次性配置** - 无需后续修改URL
- ⚡ **快速部署** - 避免两次commit
- 🔒 **配置完整** - 直接包含正确的CORS和前端配置
- 📝 **清晰流程** - 减少出错机会

### 第三步: Railway部署

#### ✅ 3.1 注册Railway账号
1. 访问: https://railway.app/
2. 点击 "Start a New Project"
3. 使用GitHub账号登录

#### ✅ 3.2 部署项目
1. **选择 "Deploy from GitHub repo"**
2. **授权Railway访问您的GitHub**
3. **选择您的VirtualJobSeekerAgent仓库**
4. **Railway自动检测并开始部署**

#### ✅ 3.3 配置环境变量

在Railway仪表板中点击您的项目，进入 "Variables" 标签，添加以下环境变量：

```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# Smithery API配置 (如果使用)
SMITHERY_API_KEY=your_smithery_key_here

# Google OAuth配置 (如果使用Gmail功能)
GOOGLE_CLIENT_ID=your_google_client_id_here
GMAIL_MCP_CREDS_PATH=/app/credentials.json

# MCP配置 (如果使用)
EXA_MCP_ENDPOINT=https://server.smithery.ai/exa/mcp?api_key={SMITHERY_API_KEY}&profile={SMITHERY_PROFILE_ID}
```

#### ✅ 3.4 验证Railway访问URL
1. **部署完成后，点击 "View Logs" 查看部署状态**
2. **在 "Settings" → "Domains" 中找到您的URL**
3. **验证是否为: `https://virtualjobseekeragent-production.up.railway.app`**

**🎯 两种情况：**
- ✅ **URL匹配** - 完美！直接进入测试阶段
- ❌ **URL不同** - 快速更新一次配置（跳到第五步）

### 第四步: 测试云服务 (URL匹配的情况)

### 第四步: 测试云服务 (URL匹配的情况)

#### ✅ 4.1 测试基本连接

在浏览器访问: `https://virtualjobseekeragent-production.up.railway.app`
- 应该看到"Forbidden"页面 (这是正常的，因为没有X-From-Extension头)

#### ✅ 4.2 测试API功能

使用PowerShell测试API：
```powershell
# 激活环境
conda activate agent_env

# 测试基本连接
Invoke-RestMethod -Uri "https://virtualjobseekeragent-production.up.railway.app/" -Headers @{"X-From-Extension"="true"}

# 应该返回: "Aloha from Python backend!"
```

#### ✅ 4.3 测试Chrome扩展

1. **确保您的Chrome扩展已安装**
2. **打开任意LinkedIn职位页面**
3. **点击扩展图标，测试邮件生成功能**

#### ✅ 4.4 配置Google OAuth (如果使用Gmail功能)

在 [Google Cloud Console](https://console.cloud.google.com/) 中：

1. **进入您的项目 → APIs & Services → Credentials**
2. **编辑OAuth 2.0客户端ID**
3. **添加授权的JavaScript来源**: `https://virtualjobseekeragent-production.up.railway.app`
4. **添加授权的重定向URI**: `https://virtualjobseekeragent-production.up.railway.app/oauth2callback`

**🎉 如果测试全部通过，部署完成！跳过第五步。**

### 第五步: URL不匹配时的快速修正 (可选)

#### ✅ 5.1 更新前端配置

如果实际URL不是 `virtualjobseekeragent-production.up.railway.app`，修改 `frontend/config.js`:

```javascript
const SERVER_CONFIG = {
    LOCAL: "http://localhost:5000",
    RAILWAY: "https://您的实际URL.up.railway.app",  // 替换为实际URL
    CURRENT: "RAILWAY"
};
```

#### ✅ 5.2 更新CORS配置

在 `backend/server.py` 中更新CORS配置的origins：

```python
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "https://您的实际URL.up.railway.app",  # 实际URL
            "chrome-extension://*",
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-From-Extension"]
    }
})
```

#### ✅ 5.3 提交修正

```bash
conda activate agent_env
git add .
git commit -m "Fix Railway URL to actual domain"
git push origin main
```

Railway会自动重新部署，然后重复第四步的测试。

### 第六步: 更新朋友的安装包 (可选)

如果您有分享给朋友的安装包系统：

```bash
conda activate agent_env

# 更新网络配置
python update_network_config.py  # 会自动更新为新的URL

# 重新创建安装包
create_friend_package.bat
```

## 📈 优化后的部署流程总结

### 🎯 **一次性部署 vs 传统两次部署**

| 步骤 | 传统方式 | 优化方式 ✅ |
|------|----------|-------------|
| 配置 | 先用占位符 | 直接用预测URL |
| 第一次commit | 不完整配置 | 完整配置 |
| 部署 | 可能有CORS错误 | 直接成功 |
| 获取URL | 手动复制 | 验证是否匹配 |
| 第二次commit | 必须要 | 90%情况不需要 |
| **总时间** | ~20分钟 | ~10分钟 |

### 🚀 **Railway URL预测规律**

**99%准确的预测规则：**
```
https://[仓库名转小写]-production.up.railway.app
```

**示例：**
- 仓库：`VirtualJobSeekerAgent` 
- URL：`https://virtualjobseekeragent-production.up.railway.app`

**例外情况：**
- 仓库名有特殊字符时可能略有不同
- 多个同名项目时会加数字后缀
- 自定义域名时会完全不同

## 🧪 故障排除

### 常见问题解决

#### 问题1: 部署失败
- **检查logs**: Railway仪表板 → View Logs
- **检查依赖**: 确保`requirements.txt`包含所有必要包
- **检查语法**: 确保Python代码无语法错误

#### 问题2: CORS错误
- **检查origins配置**: 确保包含您的域名
- **检查headers**: 确保请求包含正确的headers

#### 问题3: 环境变量问题
- **检查Variables标签**: 确保所有API密钥都已设置
- **检查拼写**: 环境变量名称必须完全匹配

#### 问题4: OAuth重定向错误
- **检查Google Console**: 确保重定向URI正确配置
- **检查HTTPS**: Railway自动提供HTTPS，确保URI使用https://

## 💰 Railway免费额度

- **计算时间**: 每月500小时
- **带宽**: 100GB/月
- **存储**: 1GB
- **项目数**: 无限制

**💡 优化建议**:
- 如果使用量大，可以配置"Sleep on idle"自动休眠
- 免费额度足够个人和朋友使用

## 🔄 日常更新流程

当您修改代码时：
```bash
git add .
git commit -m "Update features"
git push origin main
```
Railway会自动重新部署！

## ✨ Railway vs 本地部署对比

| 特性 | 本地部署 | Railway云服务 |
|------|----------|---------------|
| 稳定性 | 依赖您的电脑和网络 | 24/7云端运行 |
| 访问地址 | IP会变化 | 固定域名 |
| 网络配置 | 需要端口转发 | 无需配置 |
| 维护成本 | 需要一直开机 | 自动维护 |
| HTTPS | 需要配置 | 自动提供 |
| 与朋友分享 | 复杂 | 简单 |

## 🎉 部署完成检查清单

### ✅ **一次性部署流程 (推荐)**
- [ ] 修改 `backend/server.py` 启动配置 (预设Railway URL)
- [ ] 优化CORS安全配置 (使用预测URL)
- [ ] 创建 `frontend/config.js` (直接设为RAILWAY模式)
- [ ] 更新 `frontend/sidebar.js` 请求地址
- [ ] 创建 `requirements.txt` 和 `Procfile`
- [ ] **一次性commit和push**
- [ ] 配置Railway环境变量
- [ ] 验证URL是否匹配预测
- [ ] 测试云端API和Chrome扩展功能
- [ ] 配置Google OAuth重定向设置

### ⚡ **如果URL不匹配 (10%可能性)**
- [ ] 快速修正 `config.js` 和 `server.py` 中的URL
- [ ] 第二次commit修正URL
- [ ] 重新测试功能

**结论**: 使用预测URL的一次性部署，90%情况下无需第二次commit，大大提升部署效率！🚀

---

**需要帮助？** 
- 查看Railway文档: https://docs.railway.app/
- 检查项目logs获取错误信息
- 确保所有配置步骤都已完成
