"""
Google Ads API Authentication Helper
Handles OAuth 2.0 and configuration loading
"""

import os
import re
from pathlib import Path
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import yaml


def _normalize_customer_id(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _is_valid_customer_id(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", _normalize_customer_id(value)))


def load_google_ads_client() -> GoogleAdsClient:
    """
    Load Google Ads API client from configuration.

    Supports two methods:
    1. YAML file (config/google-ads.yaml)
    2. Environment variables

    Returns:
        GoogleAdsClient: Configured Google Ads API client

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required credentials are missing
    """
    # Try loading from YAML first
    config_path = Path(__file__).parent.parent.parent / "config" / "google-ads.yaml"

    if config_path.exists():
        print(f"Loading credentials from {config_path}")
        return GoogleAdsClient.load_from_storage(str(config_path))

    # Fallback to environment variables
    print("Loading credentials from environment variables")

    required_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set them in .env file or create config/google-ads.yaml"
        )

    # Build config dict from env vars
    config = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "use_proto_plus": True,
    }

    # Optional: login_customer_id (MCC / manager account id)
    login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        if _is_valid_customer_id(login_customer_id):
            config["login_customer_id"] = _normalize_customer_id(login_customer_id)
        else:
            print(
                "Warning: GOOGLE_ADS_LOGIN_CUSTOMER_ID is set but invalid (must be 10 digits). "
                "Ignoring it."
            )

    return GoogleAdsClient.load_from_dict(config)


def get_customer_id() -> str:
    """
    Get customer ID from environment or raise error

    Returns:
        str: Customer ID without hyphens

    Raises:
        ValueError: If GOOGLE_ADS_CUSTOMER_ID not set
    """
    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

    if not customer_id:
        raise ValueError(
            "GOOGLE_ADS_CUSTOMER_ID environment variable is required. "
            "Set it in your .env file."
        )

    normalized = _normalize_customer_id(customer_id)
    if not _is_valid_customer_id(normalized):
        raise ValueError(
            "GOOGLE_ADS_CUSTOMER_ID must be a 10 digit number (without hyphens). "
            "Example: 1234567890"
        )

    return normalized


def generate_refresh_token_instructions():
    """
    Print instructions for generating OAuth refresh token
    """
    instructions = """
    ═══════════════════════════════════════════════════════════════════
    HOW TO GENERATE GOOGLE ADS API REFRESH TOKEN
    ═══════════════════════════════════════════════════════════════════
    
    1. Install google-ads library (already done if you see this):
       pip install google-ads
    
    2. Run the OAuth helper script:
       python -m google.ads.googleads.oauth2 --client_id YOUR_CLIENT_ID \\
           --client_secret YOUR_CLIENT_SECRET \\
           --scope 'https://www.googleapis.com/auth/adwords'
    
    3. This will:
       - Open your browser for Google login
       - Ask you to authorize access
       - Print your REFRESH_TOKEN to console
    
    4. Copy the refresh_token and add it to:
       - .env file as GOOGLE_ADS_REFRESH_TOKEN
       OR
       - config/google-ads.yaml
    
    ═══════════════════════════════════════════════════════════════════
    
    For detailed setup instructions, see SETUP.md
    """
    print(instructions)
