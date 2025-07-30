# Gmail Server for Model Context Protocol (MCP) - Multi-User Edition

## Credits & Improvements

This MCP server is based on the original [gmail-mcp-server](https://github.com/jasonsum/gmail-mcp-server) by **Jason Summer** (@jasonsum) and **Igor Tarasenko** (@Saik0s).

### Key Enhancements in this Fork:

✅ **Multi-User Support**: Migrated from single-user to multi-user architecture  
✅ **Enhanced Security**: No longer stores refresh_tokens on server  
✅ **Stateless Design**: Uses temporary access_tokens for better security  

> Note: This server enables an MCP client to read, remove, and send emails. However, the client prompts the user before conducting such activities.


## 🔄 Comparison with Previous Version

| Feature | Old Version | New Version |
|---------|-------------|-------------|
| User Support | Single User | Multi-User |
| Token Storage | Server stores refresh_token | No storage, uses temporary access_token |
| Security | Medium | High |
| Launch Parameters | Requires token-path | Only needs creds-file-path |
| Frontend Integration | Complex | Simple with GIS |

## 🏗️ Architecture Change

### Old Architecture (Single User):
```
Developer OAuth Flow → Save refresh_token → Single User Service
```

### New Architecture (Multi-User):
```
Frontend GIS → Temporary access_token → MCP Server → Stateless Service
```

## Components

### Tools

- **send-email**
  - Sends email to email address recipient 
  - Input:
    - `access_token` (string): Temporary access token from GIS
    - `recipient_id` (string): Email address of addressee
    - `subject` (string): Email subject
    - `message` (string): Email content
  - Returns status and message_id

- **trash-email**
  - Moves email to trash 
  - Input:
    - `access_token` (string): Temporary access token from GIS
    - `email_id` (string): Auto-generated ID of email
  - Returns success message

- **mark-email-as-read**
  - Marks email as read 
  - Input:
    - `access_token` (string): Temporary access token from GIS
    - `email_id` (string): Auto-generated ID of email
  - Returns success message

- **get-unread-emails**
  - Retrieves unread emails 
  - Input:
    - `access_token` (string): Temporary access token from GIS
  - Returns list of emails including email ID

- **read-email**
  - Retrieves given email content
  - Input:
    - `access_token` (string): Temporary access token from GIS
    - `email_id` (string): Auto-generated ID of email
  - Returns dictionary of email metadata and marks email as read

- **open-email**
  - Open email in browser
  - Input:
    - `access_token` (string): Temporary access token from GIS
    - `email_id` (string): Auto-generated ID of email
  - Returns success message and opens given email in default browser

## Setup

### Gmail API Setup

1. [Create a new Google Cloud project](https://console.cloud.google.com/projectcreate)
2. [Enable the Gmail API](https://console.cloud.google.com/workspace-api/products)
3. [Configure an OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) 
    - Select "external". However, we will not publish the app.
    - Add your personal email address as a "Test user".
4. Add OAuth scope `https://www.googleapis.com/auth/gmail.modify`
5. [Create an OAuth Client ID](https://console.cloud.google.com/apis/credentials/oauthclient) for application type "Web Application"
6. Download the JSON file of your client's OAuth keys
7. Rename the key file and save it to your local machine in a secure location. Take note of the location.
    - The absolute path to this file will be passed as parameter `--creds-file-path` when the server is started.

### Server Launch

For the new multi-user version, only the credentials file path is required:

```bash
python server.py --creds-file-path "path/to/credentials.json"
```

**Windows Example:**
```bash
python server.py --creds-file-path "c:\Users\serendipity\.gmail-mcp\gcp-oauth.keys.json"
```

### Usage with Desktop App

Using [uv](https://docs.astral.sh/uv/) is recommended.

To integrate this server with Claude Desktop as the MCP Client, add the following to your app's server configuration. By default, this is stored as `~/Library/Application\ Support/Claude/claude_desktop_config.json`. 

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "--directory",
        "[absolute-path-to-git-repo]",
        "run",
        "gmail",
        "--creds-file-path",
        "[absolute-path-to-credentials-file]"
      ]
    }
  }
}
```

**Note:** The `--token-path` parameter is no longer needed in the multi-user version.

### Troubleshooting with MCP Inspector

To test the server, use [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector).
From the git repo, run the below changing the parameter arguments accordingly.

```bash
npx @modelcontextprotocol/inspector python gmail_mcp_server.py --creds-file-path "C:\Users\zli3\OneDrive\Desktop\GH\VirtualJobSeekerAgent-1\backend\credentials.json"
```

**Windows Example:**
```bash
```bash
npx @modelcontextprotocol/inspector python gmail-mcp-server\\gmail_mcp_server.py --creds-file-path "c:\\Users\\serendipity\\.gmail-mcp\\gcp-oauth.keys.json"
```
```

## Common Issues

1. **Frontend CORS Error**: Ensure correct authorized JavaScript origins in Google Cloud Console
2. **access_token Expired**: GIS handles this automatically, but ensure frontend has error handling
3. **Insufficient Permissions**: Ensure access_token has `gmail.modify` scope
4. **Concurrent Requests**: Multi-user support is implemented, but concurrent request handling has not been thoroughly tested.