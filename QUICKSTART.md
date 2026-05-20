# ⚡ Quick Start Guide

Get up and running with Google Keyword Planner MCP in 5 minutes.

---

## 🎯 What You'll Need

Before starting, prepare:
- Google account
- 10 minutes for Google Ads/Cloud setup
- Terminal access

---

## 🚀 Installation (2 minutes)

```bash
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔐 Configuration (5-10 minutes)

### Quick Path (If you have credentials already)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

### First Time Setup

**Don't have Google Ads API credentials yet?**

Follow the detailed guide: **[SETUP.md](SETUP.md)**

You'll need to:
1. Create Google Ads account (free, no billing required)
2. Create Google Cloud project
3. Enable Google Ads API
4. Generate OAuth credentials
5. Get developer token
6. Generate refresh token

**Estimated time:** 10-15 minutes for first-time setup

---

## ✅ Test It Works

```bash
./START.sh
```

You should see:
```
✅ Starting MCP server in development mode...
Server running on stdio
```

Press `Ctrl+C` to stop.

---

## 🔌 Add to Claude Desktop

1. Edit Claude config:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add this server:
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

3. Restart Claude Desktop

---

## 🎉 Try It Out

Open Claude and ask:

```
Can you generate 20 keyword ideas for "coffee shop" in the USA?
```

Claude will use your new MCP tools to fetch real keyword data from Google!

---

## 📚 Next Steps

- Read [README.md](README.md) for full documentation
- See [SETUP.md](SETUP.md) for troubleshooting
- Check usage examples in README

---

## ❓ Quick Troubleshooting

**Server won't start?**
- Check your .env file has all required fields
- Make sure virtual environment is activated
- Verify credentials are correct

**Claude doesn't see tools?**
- Confirm server is in Claude Desktop config
- Restart Claude Desktop
- Check paths are absolute (not relative)

**Need more help?**
See full troubleshooting guide in [SETUP.md](SETUP.md)
