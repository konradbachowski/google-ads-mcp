# Google Keyword Planner MCP Server - Setup Guide

Complete step-by-step guide to configure Google Ads API credentials for keyword research.

---

## 📋 Prerequisites

- Google account
- Python 3.9+ installed
- Terminal/command line access

---

## 🔐 Step 1: Create Google Ads Account

### Option A: Use Existing Google Ads Account
If you already have a Google Ads account, skip to Step 2.

### Option B: Create New Developer Account (Free)
1. Go to [https://ads.google.com](https://ads.google.com)
2. Click **Start Now** and sign in with your Google account
3. Follow the setup wizard:
   - **Skip billing setup** for now (developer access doesn't require spending money)
   - Choose "Smart campaign" and complete minimal setup
   - You can pause/delete this campaign later

**Important:** You need a standard Google Ads account, not a Manager account, for API access.

---

## ☁️ Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: `keyword-planner-mcp`
4. Click **Create**
5. Wait for project creation (takes ~30 seconds)

---

## 🔌 Step 3: Enable Google Ads API

1. In Google Cloud Console, with your project selected:
2. Go to **APIs & Services** → **Library**
3. Search for **Google Ads API**
4. Click on **Google Ads API**
5. Click **Enable** button
6. Wait for activation (~10 seconds)

---

## 🔑 Step 4: Create OAuth 2.0 Credentials

### 4.1 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Click **Create**
4. Fill in required fields:
   - **App name:** `Keyword Planner MCP`
   - **User support email:** Your email
   - **Developer contact:** Your email
5. Click **Save and Continue**
6. **Scopes:** Click **Save and Continue** (no changes needed)
7. **Test users:** Add your email address
8. Click **Save and Continue**
9. Click **Back to Dashboard**

### 4.2 Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Choose **Desktop app**
4. Name: `MCP Desktop Client`
5. Click **Create**
6. **Important:** Download the JSON file (button: ⬇️ Download JSON)
7. Save as `client_secrets.json` (you'll need this later)

---

## 🎫 Step 5: Get Developer Token

1. Go to your [Google Ads account](https://ads.google.com)
2. Click **Tools & Settings** (wrench icon) in top right
3. Under **Setup**, click **API Center**
4. If you don't see API Center:
   - You might need a Manager (MCC) account
   - Go to [https://ads.google.com/home/tools/manager-accounts/](https://ads.google.com/home/tools/manager-accounts/)
   - Create a Manager account (free)
   - Link your Google Ads account to it
5. In API Center, find **Developer Token** section
6. Click **Request a developer token** or copy existing one
7. **Save this token** - you'll need it for configuration

**Note:** For testing, your token will be in "test" mode. This is sufficient for keyword research.

---

## 🔄 Step 6: Generate Refresh Token

### 6.1 Install Google Ads Library

```bash
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp
source .venv/bin/activate
pip install google-ads
```

### 6.2 Run OAuth Flow

```bash
python -m google.ads.googleads.oauth2 \
    --client_id YOUR_CLIENT_ID \
    --client_secret YOUR_CLIENT_SECRET \
    --scope 'https://www.googleapis.com/auth/adwords'
```

**Where to find Client ID and Secret:**
- Open the `client_secrets.json` file you downloaded in Step 4.2
- Copy `client_id` and `client_secret` values

### 6.3 Complete Authorization

1. The command will print a URL and open your browser
2. Sign in with your Google account
3. Click **Allow** to grant access
4. Browser will show "Success! You can close this window"
5. **In terminal**, you'll see:
```
Your refresh token is: 1//XXXXXXXXXXXXXXXXXXXXX
```
6. **Copy this refresh token** - you'll need it for configuration

---

## ⚙️ Step 7: Configure MCP Server

### Option A: Using .env File (Recommended)

1. Copy the example file:
```bash
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp
cp .env.example .env
```

2. Edit `.env` file and fill in your credentials:
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=1//your_refresh_token_here
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

**Where to find Customer IDs:**
- Go to [ads.google.com](https://ads.google.com)
- Top right corner shows your Customer ID (e.g., `123-456-7890`)
- Remove hyphens: `1234567890`
- Use same ID for both `LOGIN_CUSTOMER_ID` and `CUSTOMER_ID` if you're not using MCC

### Option B: Using YAML File

1. Copy the example:
```bash
cp config/google-ads.yaml.example config/google-ads.yaml
```

2. Edit `config/google-ads.yaml`:
```yaml
developer_token: "YOUR_DEVELOPER_TOKEN"
client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret: "YOUR_CLIENT_SECRET"
refresh_token: "YOUR_REFRESH_TOKEN"
login_customer_id: "YOUR_CUSTOMER_ID_WITHOUT_HYPHENS"
use_proto_plus: True
```

---

## ✅ Step 8: Test Configuration

Run test to verify everything works:

```bash
source .venv/bin/activate
fastmcp dev src/main.py
```

You should see:
```
Server running on stdio
MCP tools loaded: 7 tools available
```

---

## 🚀 Step 9: Add to Claude Desktop

1. Open Claude Desktop configuration:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add MCP server configuration:
```json
{
  "mcpServers": {
    "google-keyword-planner": {
      "command": "/Users/mac/kodziki/mcp/google-keyword-planner-mcp/.venv/bin/python",
      "args": ["/Users/mac/kodziki/mcp/google-keyword-planner-mcp/src/main.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_token_here",
        "GOOGLE_ADS_CLIENT_ID": "your_client_id_here",
        "GOOGLE_ADS_CLIENT_SECRET": "your_secret_here",
        "GOOGLE_ADS_REFRESH_TOKEN": "your_refresh_token_here",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "your_customer_id_here",
        "GOOGLE_ADS_CUSTOMER_ID": "your_customer_id_here"
      }
    }
  }
}
```

**Or use env file reference:**
```json
{
  "mcpServers": {
    "google-keyword-planner": {
      "command": "/Users/mac/kodziki/mcp/google-keyword-planner-mcp/.venv/bin/python",
      "args": ["/Users/mac/kodziki/mcp/google-keyword-planner-mcp/src/main.py"]
    }
  }
}
```
(Server will auto-load from `.env` file)

3. **Restart Claude Desktop**

---

## 🧪 Step 10: Test in Claude

Open Claude and try:

```
Can you generate keyword ideas for "seo tools" in the USA?
```

Claude should use the MCP tools and return keyword suggestions with search volumes!

---

## 🔧 Troubleshooting

### Error: "Missing required environment variables"
- Check your `.env` file exists and has all required fields
- Make sure no quotes around values (except in JSON)
- Verify file is in project root directory

### Error: "DEVELOPER_TOKEN_NOT_APPROVED"
- Your developer token is in test mode (this is OK!)
- You can still use it with your own account
- For production use, apply for token approval in Google Ads API Center

### Error: "CUSTOMER_NOT_FOUND"
- Check your Customer ID is correct (remove hyphens!)
- Make sure you're using the ID from your Google Ads account
- If using MCC, use the MCC ID as login_customer_id

### Error: "Request had invalid authentication credentials"
- Your refresh token might be expired
- Re-run Step 6 to generate new refresh token
- Make sure Client ID and Secret match your OAuth credentials

### OAuth Flow Opens Wrong Browser
```bash
# Set default browser
export BROWSER=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome
# Then run oauth flow again
```

---

## 📚 Additional Resources

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Ads API Python Client](https://github.com/googleads/google-ads-python)
- [OAuth 2.0 Guide](https://developers.google.com/google-ads/api/docs/oauth/overview)

---

## 🆘 Need Help?

If you encounter issues not covered here, check:
1. Google Ads API error codes: https://developers.google.com/google-ads/api/docs/errors
2. MCP server logs in Claude Desktop
3. Test server directly with `fastmcp dev src/main.py`
