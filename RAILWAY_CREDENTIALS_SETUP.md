# Railway环境变量配置指南

## 必需的环境变量

在Railway项目的 **Variables** 标签中设置以下环境变量：

### 基础配置
```
ENVIRONMENT=production
SMITHERY_API_KEY=你的 Smithery API 密钥
OPENAI_API_KEY=你的 OpenAI API 密钥
SMITHERY_PROFILE_ID=你的 Smithery Profile ID
GOOGLE_CLIENT_ID=你的 Google Client ID
```
> ⚠️ 请勿将真实密钥写入文档或提交到代码仓库，仅在Railway环境变量中安全设置。

### Gmail凭据配置
```
GMAIL_MCP_CREDS_JSON={"web":{"client_id":"982748144668-q3tf5s5im9ogehrkec0vh2ohthv1nauq.apps.googleusercontent.com","project_id":"YOUR_PROJECT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR_CLIENT_SECRET","redirect_uris":["http://localhost"]}}
```

## 如何获取GMAIL_MCP_CREDS_JSON的值

1. **打开你的Gmail凭据文件** (`client_secret_*.json`)

2. **复制完整的JSON内容**，例如：
   ```json
   {
     "web": {
       "client_id": "982748144668-q3tf5s5im9ogehrkec0vh2ohthv1nauq.apps.googleusercontent.com",
       "project_id": "your-project-id",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "GOCSPX-your-client-secret",
       "redirect_uris": ["http://localhost"]
     }
   }
   ```

3. **将JSON压缩为一行**（移除换行和多余空格）：
   ```
   {"web":{"client_id":"982748144668-q3tf5s5im9ogehrkec0vh2ohthv1nauq.apps.googleusercontent.com","project_id":"your-project-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"GOCSPX-your-client-secret","redirect_uris":["http://localhost"]}}
   ```

4. **在Railway Variables中添加**：
   - Variable Name: `GMAIL_MCP_CREDS_JSON`
   - Variable Value: 上面压缩的JSON字符串

## 验证配置

部署后，在Deploy Logs中查找：
```
✅ Gmail凭据验证成功: /tmp/tmpXXXXXX.json
```

如果看到错误，检查：
1. JSON格式是否正确
2. 是否包含所有必需字段
3. client_secret等敏感信息是否正确

## 本地开发

本地开发时，继续使用 `.env` 文件中的 `GMAIL_MCP_CREDS_PATH` 指向本地文件路径。

## 安全注意事项

- ⚠️ **不要将Gmail凭据文件提交到Git**
- ✅ Railway环境变量是安全的，不会出现在日志中
- ✅ 临时文件会在程序结束时自动清理
