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
GMAIL_MCP_CREDS_PATH=PATH_TO_FILE # will get this in next step....\credentials.json, downloaded from GCP after creating client
SMITHERY_API_KEY=your_smithery_api_key
SMITHERY_PROFILE_ID=your_smithery_profile_id
```

### 2. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/) 
2. Create OAuth 2.0 client ID, choose "Chrome Extension" as application type
3. Copy the client ID to the `GOOGLE_CLIENT_ID` field in `.env` file
5. Download the created `credentials.json` file, copy the `credentials.json` file path to the `GMAIL_MCP_CREDS_PATH` field in `.env` file
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
