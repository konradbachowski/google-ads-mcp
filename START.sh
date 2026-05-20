#!/bin/bash

# Google Keyword Planner MCP Server - Quick Start Script

echo "🔍 Google Keyword Planner MCP Server"
echo "====================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if credentials are configured
if [ ! -f ".env" ] && [ ! -f "config/google-ads.yaml" ]; then
    echo "⚠️  Credentials not configured!"
    echo ""
    echo "Please configure your Google Ads API credentials:"
    echo "1. Copy .env.example to .env"
    echo "2. Fill in your credentials (see SETUP.md for instructions)"
    echo ""
    exit 1
fi

echo "✅ Starting MCP server in development mode..."
echo ""

# Activate virtual environment and run server
source .venv/bin/activate
fastmcp dev src/main.py
