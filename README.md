# 🔍 Google Ads MCP Server

Full Google Ads management integrated with Claude AI via Model Context Protocol (MCP).

**29 tools** covering the complete paid search lifecycle: keyword research, conversion tracking, and **full campaign management with write access** — create and launch entire Search campaigns end-to-end without touching the Google Ads UI.

Real data from the official Google Ads API — no guessing, no scraping.

---

## ✨ Features

### 🎯 Keyword Research (read)

- **`generate_keywords`** - Generate keyword ideas from seed keywords or URL
- **`get_metrics`** - Get detailed metrics for specific keywords
- **`filter_keywords_by_competition`** - Filter by LOW/MEDIUM/HIGH competition
- **`filter_keywords_by_volume`** - Filter by search volume range
- **`list_available_locations`** / **`list_available_languages`** - Supported geo/lang

### 🎯 Conversion Tracking (read + write)

- **`create_conversion_action`** - Create a new conversion action
- **`list_conversion_actions`** - List all conversions on the account
- **`upload_offline_conversion`** - Upload CRM/offline conversions (e.g. deal won → real LTV)

### ✍️ Campaign Management — Write

Build and launch complete Search campaigns programmatically:

- **`create_campaign_budget`** - Create a daily budget
- **`create_campaign`** - Create a Search campaign (Maximize Clicks / Conversions, geo, networks)
- **`create_ad_group`** - Create an ad group
- **`add_keyword`** - Add positive keywords (Exact / Phrase / Broad)
- **`create_responsive_search_ad`** - Create an RSA (15 headlines + 4 descriptions)
- **`create_shared_negative_set`** + **`apply_shared_set_to_campaign`** - Shared negative keyword lists
- **`add_negative_keyword`** - Campaign-level negative keyword
- **`pause_campaign`** / **`enable_campaign`** - Campaign status control
- **`pause_keyword`** / **`enable_keyword`** - Keyword status control
- **`update_keyword_bid`** / **`update_campaign_budget`** - Bid & budget changes

### 🔎 Helpers (read)

- **`list_campaigns`** / **`list_ad_groups`** / **`list_campaign_budgets`** / **`list_shared_sets`**
- **`find_keyword`** - Resolve criterion ID from keyword text
- **`find_geo_targets`** - Look up geo target constants (e.g. "Poland" → 2616)

> ⚠️ **Write tools mutate live Google Ads accounts.** New campaigns default to `PAUSED` so you can review before enabling. Use deliberately.

### 📊 Data Provided

- ✅ Average monthly search volume
- ✅ Competition level (LOW/MEDIUM/HIGH)
- ✅ Competition index (0-100)
- ✅ Cost per click (CPC) estimates
- ✅ Monthly search trends (12-month breakdown)
- ✅ Top of page bid estimates

### 🌍 Supported Locations

USA, Poland, UK, Germany, France, Canada, Australia, and more

### 🗣️ Supported Languages

English, Polish, German, French, Spanish, Italian, and more

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials

**See [SETUP.md](SETUP.md) for detailed step-by-step instructions.**

Quick setup:
```bash
cp .env.example .env
# Edit .env with your Google Ads API credentials
```

Required credentials:
- Google Ads Developer Token
- OAuth 2.0 Client ID & Secret
- Refresh Token
- Customer ID

### 3. Test Locally

```bash
fastmcp dev src/main.py
```

### 4. Add to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop.

---

## 💡 Usage Examples

### Example 1: Generate Keywords from Seed

**Prompt to Claude:**
```
Generate keyword ideas for "seo tools" in the USA, limit to 20 results
```

**Claude will use:**
```python
generate_keywords(
    keywords=["seo tools"],
    location="USA",
    limit=20
)
```

**Returns:**
```json
{
  "success": true,
  "total_results": 20,
  "keywords": [
    {
      "keyword": "best seo tools",
      "avg_monthly_searches": 18100,
      "competition": "HIGH",
      "competition_index": 92,
      "low_top_of_page_bid_micros": 8500000,
      "high_top_of_page_bid_micros": 15200000
    },
    ...
  ]
}
```

### Example 2: Analyze Your Website

**Prompt:**
```
What keywords can you find for heyneuron.com website?
```

**Claude uses:**
```python
generate_keywords(
    url="https://heyneuron.com",
    location="USA",
    limit=50
)
```

### Example 3: Get Metrics for Specific Keywords

**Prompt:**
```
Get detailed metrics for these keywords: "ai tools", "machine learning", "chatgpt"
```

**Claude uses:**
```python
get_metrics(
    keywords=["ai tools", "machine learning", "chatgpt"],
    location="USA"
)
```

### Example 4: Find Low Competition Keywords

**Prompt:**
```
Generate keywords for "plumbing services" in Poland, 
then filter for low competition keywords with at least 500 monthly searches
```

**Claude uses:**
```python
# Step 1: Generate keywords
results = generate_keywords(
    keywords=["plumbing services"],
    location="POLAND",
    language="POLISH",
    limit=100
)

# Step 2: Filter by competition
low_comp = filter_keywords_by_competition(
    keywords_data=results["keywords"],
    competition_level="LOW"
)

# Step 3: Filter by volume
final = filter_keywords_by_volume(
    keywords_data=low_comp["keywords"],
    min_searches=500
)
```

### Example 5: Launch a Full Search Campaign

**Prompt:**
```
Build a Search campaign "Q3 Lead Gen" with a 50 EUR/day budget,
two ad groups, keywords and ads. Keep it paused so I can review.
```

**Claude uses the write tools in sequence:**
```python
budget   = create_campaign_budget(name="Q3 Lead Gen", daily_pln=50)
campaign = create_campaign(
    name="Q3 Lead Gen", budget_id=budget["id"],
    bidding_strategy_type="MAXIMIZE_CLICKS",
    geo_target_constant_ids=[2616],      # Poland
    status="PAUSED",                      # review before enabling
)
ag = create_ad_group(campaign_id=campaign["id"], name="Brand", default_bid_pln=3)
add_keyword(ad_group_id=ag["id"], text="my product", match_type="EXACT")
create_responsive_search_ad(
    ad_group_id=ag["id"],
    headlines=[...15 headlines...],
    descriptions=[...4 descriptions...],
    final_url="https://example.com/landing",
)
neg = create_shared_negative_set(name="Master Negatives", members=[...])
apply_shared_set_to_campaign(campaign_id=campaign["id"], shared_set_id=neg["id"])
```

Campaign is created **PAUSED** — review in the Google Ads UI, then `enable_campaign(campaign_id)`.

---

## 🛠️ Tool Reference

### `generate_keywords`

Generate keyword ideas from seeds or URL.

**Parameters:**
- `keywords` (optional): List of seed keywords
- `url` (optional): Website URL to analyze
- `location`: Target country (default: "USA")
- `language`: Target language (default: "ENGLISH")
- `network`: "GOOGLE_SEARCH" or "GOOGLE_SEARCH_AND_PARTNERS" (default)
- `limit`: Max results (default: 50, max: 1000)

**Note:** Provide at least one of `keywords` or `url`.

### `get_metrics`

Get detailed metrics for specific keywords.

**Parameters:**
- `keywords`: List of keywords to analyze (required)
- `location`: Target country (default: "USA")
- `language`: Target language (default: "ENGLISH")

### `filter_keywords_by_competition`

Filter keywords by competition level.

**Parameters:**
- `keywords_data`: List of keyword dictionaries
- `competition_level`: "LOW", "MEDIUM", or "HIGH"

### `filter_keywords_by_volume`

Filter keywords by search volume range.

**Parameters:**
- `keywords_data`: List of keyword dictionaries
- `min_searches`: Minimum monthly searches (optional)
- `max_searches`: Maximum monthly searches (optional)

---

## 📁 Project Structure

```
google-ads-mcp/
├── src/
│   ├── main.py                  # FastMCP server & tool registration (29 tools)
│   ├── auth/
│   │   └── google_auth.py       # OAuth & client loading
│   ├── tools/
│   │   ├── keyword_ideas.py     # Keyword generation
│   │   ├── metrics.py           # Metrics retrieval
│   │   ├── filters.py           # Filtering utilities
│   │   ├── conversions.py       # Conversion actions + offline upload
│   │   ├── mutations.py         # Pause/enable, bid/budget updates, negatives
│   │   └── mutations_create.py  # Campaign lifecycle CREATE (budget→campaign→AG→KW→RSA)
│   └── utils/
│       └── constants.py         # Location/language IDs
├── config/
│   └── google-ads.yaml.example  # Config template
├── requirements.txt
├── SETUP.md                     # Setup instructions
└── README.md
```

---

## 🔐 Security

**Never commit these files:**
- `.env`
- `config/google-ads.yaml`
- `client_secrets.json`
- Any file containing API credentials

All sensitive files are in `.gitignore`.

---

## 🐛 Troubleshooting

### "Missing required environment variables"
- Check `.env` file exists and contains all required fields
- Verify no extra quotes around values

### "DEVELOPER_TOKEN_NOT_APPROVED"
- Test mode tokens work fine for personal use
- You can use up to 15,000 operations per day
- Apply for approval in Google Ads if you need production access

### "Authentication failed"
- Refresh token might be expired - regenerate it
- Check Client ID and Secret match your OAuth credentials
- Ensure you authorized the correct Google account

### Claude doesn't see the tools
- Verify server is in Claude Desktop config
- Check paths are absolute, not relative
- Restart Claude Desktop after config changes
- Test server with `fastmcp dev src/main.py`

**For detailed troubleshooting, see [SETUP.md](SETUP.md)**

---

## 📚 API Limits

Google Ads API has rate limits:

- **Test tokens:** 15,000 operations/day (sufficient for keyword research)
- **Production tokens:** Higher limits (requires approval)

Keyword Planner services are designed for research, not high-frequency queries. Cache results when possible.

---

## 🤝 Contributing

Found a bug? Have a feature request?

1. Check existing issues
2. Create new issue with details
3. PRs welcome!

---

## 📖 Resources

- [Google Ads API Docs](https://developers.google.com/google-ads/api/docs/start)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Credits

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [Google Ads Python Client](https://github.com/googleads/google-ads-python)
- Claude AI by Anthropic

---

## ⭐ Support

If this MCP server helps your keyword research, consider:
- ⭐ Star this repo
- 🐛 Report issues
- 💡 Suggest features
- 🔗 Share with others

---

**Made with ❤️ for the SEO and marketing community**
