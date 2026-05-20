"""
Constants for Google Ads API
Common location and language constants for keyword research
"""

# Popular location IDs for geo-targeting
# Full list: https://developers.google.com/google-ads/api/data/geotargets
LOCATIONS = {
    "USA": 2840,
    "POLAND": 2616,
    "UK": 2826,
    "GERMANY": 2276,
    "FRANCE": 2250,
    "CANADA": 2124,
    "AUSTRALIA": 2036,
    "WORLDWIDE": None,  # No geo-targeting
}

# Popular language IDs
# Full list: https://developers.google.com/google-ads/api/data/codes-formats#languages
LANGUAGES = {
    "ENGLISH": 1000,
    "POLISH": 1025,
    "GERMAN": 1001,
    "FRENCH": 1002,
    "SPANISH": 1003,
    "ITALIAN": 1004,
}

# Keyword Plan Network options
NETWORKS = {
    "GOOGLE_SEARCH": "GOOGLE_SEARCH",
    "GOOGLE_SEARCH_AND_PARTNERS": "GOOGLE_SEARCH_AND_PARTNERS",
}

# Competition levels
COMPETITION_LEVELS = {
    "LOW": "LOW",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
    "UNSPECIFIED": "UNSPECIFIED",
}
