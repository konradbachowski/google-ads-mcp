"""
Google Keyword Planner MCP Server
FastMCP implementation for Google Ads API keyword research
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Import our modules
from auth.google_auth import load_google_ads_client, get_customer_id
from tools.keyword_ideas import generate_keyword_ideas
from tools.metrics import get_keyword_metrics
from tools.filters import filter_by_competition, filter_by_volume, sort_keywords
from tools.conversions import (
    create_conversion_action as create_conversion_action_impl,
    list_conversion_actions as list_conversion_actions_impl,
    upload_offline_conversion as upload_offline_conversion_impl,
)
from tools.mutations import (
    add_negative_keyword as add_negative_keyword_impl,
    pause_keyword as pause_keyword_impl,
    enable_keyword as enable_keyword_impl,
    update_keyword_bid as update_keyword_bid_impl,
    pause_campaign as pause_campaign_impl,
    enable_campaign as enable_campaign_impl,
    update_campaign_budget as update_campaign_budget_impl,
    find_keyword as find_keyword_impl,
)
from tools.mutations_create import (
    create_campaign_budget as create_campaign_budget_impl,
    create_campaign as create_campaign_impl,
    create_ad_group as create_ad_group_impl,
    add_keyword as add_keyword_impl,
    create_responsive_search_ad as create_responsive_search_ad_impl,
    create_shared_negative_set as create_shared_negative_set_impl,
    apply_shared_set_to_campaign as apply_shared_set_to_campaign_impl,
    list_campaigns as list_campaigns_impl,
    list_ad_groups as list_ad_groups_impl,
    list_campaign_budgets as list_campaign_budgets_impl,
    list_shared_sets as list_shared_sets_impl,
    find_geo_targets as find_geo_targets_impl,
)
from utils.constants import LOCATIONS, LANGUAGES, NETWORKS

# Initialize FastMCP server
mcp = FastMCP("Google Keyword Planner")

# Initialize Google Ads client (lazy loading)
_client = None
_customer_id = None


def get_client():
    """Lazy load Google Ads client"""
    global _client, _customer_id
    if _client is None:
        _client = load_google_ads_client()
        _customer_id = get_customer_id()
    return _client, _customer_id


@mcp.tool()
async def generate_keywords(
    keywords: Optional[List[str]] = None,
    url: Optional[str] = None,
    location: str = "USA",
    language: str = "ENGLISH",
    network: str = "GOOGLE_SEARCH_AND_PARTNERS",
    limit: int = 50,
) -> dict:
    """
    Generate keyword ideas for SEO and PPC campaigns.

    Provide either keywords, a URL, or both to get keyword suggestions with search volumes,
    competition levels, and CPC data.

    Args:
        keywords: List of seed keywords (e.g., ["plumber", "drain cleaning"])
        url: Website URL to analyze (e.g., "https://example.com")
        location: Target location (USA, POLAND, UK, GERMANY, FRANCE, CANADA, AUSTRALIA)
        language: Target language (ENGLISH, POLISH, GERMAN, FRENCH, SPANISH, ITALIAN)
        network: GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS
        limit: Maximum number of results (default: 50, max: 1000)

    Returns:
        Dictionary with keyword ideas and metrics

    Example:
        generate_keywords(keywords=["seo tools"], location="USA", limit=20)
    """
    try:
        client, customer_id = get_client()

        # Validate inputs
        if not keywords and not url:
            return {
                "error": "Please provide either keywords or url (or both)",
                "keywords": keywords,
                "url": url,
            }

        # Get location ID
        location_id = LOCATIONS.get(location.upper())
        location_ids = [location_id] if location_id else None

        # Get language ID
        language_id = LANGUAGES.get(language.upper(), 1000)

        # Generate keyword ideas
        results = generate_keyword_ideas(
            client=client,
            customer_id=customer_id,
            keywords=keywords,
            url=url,
            location_ids=location_ids,
            language_id=language_id,
            network=network,
            page_size=min(limit, 1000),
        )

        # Sort by search volume
        results = sort_keywords(
            results, sort_by="avg_monthly_searches", descending=True
        )

        # Limit results
        results = results[:limit]

        return {
            "success": True,
            "total_results": len(results),
            "keywords": results,
            "filters": {"location": location, "language": language, "network": network},
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_metrics(
    keywords: List[str], location: str = "USA", language: str = "ENGLISH"
) -> dict:
    """
    Get detailed metrics for specific keywords.

    Returns search volume, competition, CPC data, and monthly trends for your keywords.

    Args:
        keywords: List of keywords to analyze (e.g., ["best seo tools", "keyword research"])
        location: Target location (USA, POLAND, UK, etc.)
        language: Target language (ENGLISH, POLISH, GERMAN, etc.)

    Returns:
        Dictionary with detailed metrics for each keyword

    Example:
        get_metrics(keywords=["seo tools", "keyword planner"], location="USA")
    """
    try:
        client, customer_id = get_client()

        if not keywords:
            return {"error": "Keywords list cannot be empty"}

        # Get location ID
        location_id = LOCATIONS.get(location.upper())
        location_ids = [location_id] if location_id else None

        # Get language ID
        language_id = LANGUAGES.get(language.upper(), 1000)

        # Get metrics
        results = get_keyword_metrics(
            client=client,
            customer_id=customer_id,
            keywords=keywords,
            location_ids=location_ids,
            language_id=language_id,
        )

        return {
            "success": True,
            "total_keywords": len(results),
            "metrics": results,
            "filters": {"location": location, "language": language},
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def filter_keywords_by_competition(
    keywords_data: List[dict], competition_level: str
) -> dict:
    """
    Filter keywords by competition level.

    Args:
        keywords_data: List of keyword dictionaries (from generate_keywords or get_metrics)
        competition_level: LOW, MEDIUM, or HIGH

    Returns:
        Filtered list of keywords

    Example:
        filter_keywords_by_competition(keywords_data=results, competition_level="LOW")
    """
    try:
        filtered = filter_by_competition(keywords_data, competition_level.upper())

        return {
            "success": True,
            "original_count": len(keywords_data),
            "filtered_count": len(filtered),
            "competition_level": competition_level.upper(),
            "keywords": filtered,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def filter_keywords_by_volume(
    keywords_data: List[dict],
    min_searches: Optional[int] = None,
    max_searches: Optional[int] = None,
) -> dict:
    """
    Filter keywords by search volume range.

    Args:
        keywords_data: List of keyword dictionaries
        min_searches: Minimum average monthly searches
        max_searches: Maximum average monthly searches

    Returns:
        Filtered list of keywords

    Example:
        filter_keywords_by_volume(keywords_data=results, min_searches=1000, max_searches=10000)
    """
    try:
        filtered = filter_by_volume(keywords_data, min_searches, max_searches)

        return {
            "success": True,
            "original_count": len(keywords_data),
            "filtered_count": len(filtered),
            "filters": {"min_searches": min_searches, "max_searches": max_searches},
            "keywords": filtered,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_available_locations() -> dict:
    """
    List all available location targeting options.

    Returns:
        Dictionary of location names and their IDs
    """
    return {"success": True, "locations": LOCATIONS}


@mcp.tool()
async def list_available_languages() -> dict:
    """
    List all available language targeting options.

    Returns:
        Dictionary of language names and their IDs
    """
    return {"success": True, "languages": LANGUAGES}


@mcp.tool()
async def create_conversion_action(
    name: str,
    default_value: float,
    category: str = "SUBMIT_LEAD_FORM",
    currency_code: str = "PLN",
    counting_type: str = "ONE_PER_CLICK",
) -> dict:
    """
    Create a new Google Ads conversion action.

    Args:
        name: Human-readable conversion name (e.g. "Booking konsultacji cal.com")
        default_value: Default monetary value used when a conversion fires
            without an explicit value. Used by Smart Bidding.
        category: One of SUBMIT_LEAD_FORM, BOOK_APPOINTMENT, LEAD,
            QUALIFIED_LEAD, CONVERTED_LEAD, REQUEST_QUOTE, CONTACT, SIGNUP,
            PURCHASE, DEFAULT.
        currency_code: ISO-4217 currency code (default PLN).
        counting_type: ONE_PER_CLICK (lead-style) or MANY_PER_CLICK (ecommerce).

    Returns:
        Dictionary with the new conversion's resource_name, numeric id,
        and tag snippets (global_site_tag + event_snippet) ready to paste
        into GTM as a Google Ads Conversion Tracking tag.
    """
    try:
        client, customer_id = get_client()
        result = create_conversion_action_impl(
            client=client,
            customer_id=customer_id,
            name=name,
            default_value=default_value,
            category=category,
            currency_code=currency_code,
            counting_type=counting_type,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_conversion_actions() -> dict:
    """
    List all Google Ads conversion actions on the account.

    Returns:
        Dictionary with all conversions: id, name, status, category, type,
        counting_type, default_value, currency_code.
    """
    try:
        client, customer_id = get_client()
        actions = list_conversion_actions_impl(client=client, customer_id=customer_id)
        return {"success": True, "total": len(actions), "conversions": actions}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def upload_offline_conversion(
    conversion_action_id: int,
    gclid: str,
    conversion_value: float,
    conversion_date_time: str,
    currency_code: str = "PLN",
    order_id: str = "",
) -> dict:
    """
    Upload an offline conversion to Google Ads (e.g. CRM deal won).

    Used to feed real revenue back to Smart Bidding once a lead becomes a
    paying customer. Requires a gclid captured at the original click.

    Args:
        conversion_action_id: Numeric id from create_conversion_action.
        gclid: Google Ads click id captured at landing.
        conversion_value: Real revenue / deal value.
        conversion_date_time: Timezone-aware timestamp,
            format "YYYY-MM-DD HH:MM:SS+HH:MM"
            (e.g. "2026-05-18 14:30:00+02:00").
        currency_code: ISO-4217 currency code (default PLN).
        order_id: Optional unique identifier to dedupe re-uploads.

    Returns:
        Dictionary with upload result and partial_failure_error if any.
    """
    try:
        client, customer_id = get_client()
        result = upload_offline_conversion_impl(
            client=client,
            customer_id=customer_id,
            conversion_action_id=conversion_action_id,
            gclid=gclid,
            conversion_value=conversion_value,
            conversion_date_time=conversion_date_time,
            currency_code=currency_code,
            order_id=order_id or None,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Write tools (mutations) — for interactive use by Konrad / Claude Code session.
# Never call these from autonomous cron without explicit user approval per action.
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def add_negative_keyword(
    campaign_id: int,
    keyword_text: str,
    match_type: str = "BROAD",
) -> dict:
    """
    Add a campaign-level negative keyword.

    Args:
        campaign_id: Numeric campaign id (from list_campaigns or Google Ads UI URL).
        keyword_text: The keyword text to block. Token-level patterns (e.g. "praca")
            work best with BROAD. Word-order patterns ("co to jest") use PHRASE.
            Exact queries use EXACT.
        match_type: EXACT, PHRASE, or BROAD. Default BROAD (broadest block).
    """
    try:
        client, customer_id = get_client()
        result = add_negative_keyword_impl(
            client=client,
            customer_id=customer_id,
            campaign_id=campaign_id,
            keyword_text=keyword_text,
            match_type=match_type,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def pause_keyword(ad_group_id: int, criterion_id: int) -> dict:
    """
    Pause a single keyword (sets status=PAUSED). Use find_keyword first
    to resolve criterion_id from keyword text.
    """
    try:
        client, customer_id = get_client()
        result = pause_keyword_impl(
            client=client,
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            criterion_id=criterion_id,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def enable_keyword(ad_group_id: int, criterion_id: int) -> dict:
    """Enable a previously paused keyword."""
    try:
        client, customer_id = get_client()
        result = enable_keyword_impl(
            client=client,
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            criterion_id=criterion_id,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_keyword_bid(
    ad_group_id: int,
    criterion_id: int,
    new_bid_pln: float,
) -> dict:
    """
    Update max CPC bid for a single keyword.

    Args:
        new_bid_pln: New max CPC in PLN (e.g. 3.50). Converted to micros internally.
    """
    try:
        client, customer_id = get_client()
        result = update_keyword_bid_impl(
            client=client,
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            criterion_id=criterion_id,
            new_bid_pln=new_bid_pln,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def pause_campaign(campaign_id: int) -> dict:
    """Pause a campaign (emergency stop)."""
    try:
        client, customer_id = get_client()
        result = pause_campaign_impl(
            client=client,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def enable_campaign(campaign_id: int) -> dict:
    """Enable a previously paused campaign."""
    try:
        client, customer_id = get_client()
        result = enable_campaign_impl(
            client=client,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_campaign_budget(
    budget_id: int,
    new_daily_pln: float,
) -> dict:
    """
    Update daily budget on a CampaignBudget resource.

    Args:
        budget_id: Numeric budget id (from list_campaign_budgets).
        new_daily_pln: New daily cap in PLN (e.g. 100.00).
    """
    try:
        client, customer_id = get_client()
        result = update_campaign_budget_impl(
            client=client,
            customer_id=customer_id,
            budget_id=budget_id,
            new_daily_pln=new_daily_pln,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def find_keyword(keyword_text: str) -> dict:
    """
    Find a keyword by its text. Returns first match with criterion_id, ad_group_id,
    campaign_id — needed before pause_keyword / update_keyword_bid.
    """
    try:
        client, customer_id = get_client()
        result = find_keyword_impl(
            client=client,
            customer_id=customer_id,
            keyword_text=keyword_text,
        )
        if not result:
            return {"success": False, "error": f"No keyword found matching '{keyword_text}'"}
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# CREATE tools — full campaign lifecycle (budget → campaign → ad group → KW → RSA)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def create_campaign_budget(
    name: str,
    daily_pln: float,
    delivery_method: str = "STANDARD",
) -> dict:
    """
    Create a CampaignBudget resource.

    Args:
        name: Display name (e.g. "HeyNeuron M1 — 65 PLN/dzień").
        daily_pln: Daily budget cap in PLN.
        delivery_method: STANDARD (smooth pacing) or ACCELERATED (spend fast).
    """
    try:
        client, customer_id = get_client()
        result = create_campaign_budget_impl(
            client=client, customer_id=customer_id,
            name=name, daily_pln=daily_pln, delivery_method=delivery_method,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_campaign(
    name: str,
    budget_id: int,
    advertising_channel_type: str = "SEARCH",
    bidding_strategy_type: str = "MAXIMIZE_CLICKS",
    target_spend_cap_pln: float = 0,
    geo_target_constant_ids: list = None,
    language_constant_ids: list = None,
    status: str = "PAUSED",
    network_partner_search: bool = False,
    network_content: bool = False,
) -> dict:
    """
    Create a Search campaign (default PAUSED — flip to ENABLED via enable_campaign).

    Args:
        budget_id: Numeric id from create_campaign_budget.
        advertising_channel_type: SEARCH (default) | DISPLAY | SHOPPING | VIDEO | PERFORMANCE_MAX.
        bidding_strategy_type: MAXIMIZE_CLICKS (default) | MAXIMIZE_CONVERSIONS |
            MAXIMIZE_CONVERSION_VALUE | MANUAL_CPC.
        target_spend_cap_pln: For MAXIMIZE_CLICKS — CPC ceiling, 0 = no cap.
        geo_target_constant_ids: e.g. [2616] for Poland. None = worldwide.
        language_constant_ids: e.g. [1045, 1000] = Polish + English.
        status: PAUSED (safer default) | ENABLED.
        network_partner_search: include Search Partners (default False).
        network_content: include Display Network (default False).
    """
    try:
        client, customer_id = get_client()
        result = create_campaign_impl(
            client=client, customer_id=customer_id,
            name=name, budget_id=budget_id,
            advertising_channel_type=advertising_channel_type,
            bidding_strategy_type=bidding_strategy_type,
            target_spend_cap_pln=target_spend_cap_pln if target_spend_cap_pln > 0 else None,
            geo_target_constant_ids=geo_target_constant_ids or [],
            language_constant_ids=language_constant_ids or [],
            status=status,
            network_partner_search=network_partner_search,
            network_content=network_content,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_ad_group(
    campaign_id: int,
    name: str,
    default_bid_pln: float = 0,
    status: str = "ENABLED",
) -> dict:
    """
    Create an ad group under a campaign.

    Args:
        campaign_id: Numeric campaign id from create_campaign.
        name: Ad group name (e.g. "AG1 — Automatyzacja procesów").
        default_bid_pln: Default max CPC for keywords in this AG (0 = inherited).
        status: ENABLED (default) | PAUSED.
    """
    try:
        client, customer_id = get_client()
        result = create_ad_group_impl(
            client=client, customer_id=customer_id,
            campaign_id=campaign_id, name=name,
            default_bid_pln=default_bid_pln if default_bid_pln > 0 else None,
            status=status,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def add_keyword(
    ad_group_id: int,
    text: str,
    match_type: str = "EXACT",
    bid_pln: float = 0,
) -> dict:
    """
    Add a positive keyword to an ad group.

    Args:
        text: Keyword text (without brackets/quotes).
        match_type: EXACT (default — only exact matches) | PHRASE | BROAD.
        bid_pln: Optional max CPC override for this keyword (0 = use ad group default).
    """
    try:
        client, customer_id = get_client()
        result = add_keyword_impl(
            client=client, customer_id=customer_id,
            ad_group_id=ad_group_id, text=text, match_type=match_type,
            bid_pln=bid_pln if bid_pln > 0 else None,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_responsive_search_ad(
    ad_group_id: int,
    headlines: list,
    descriptions: list,
    final_url: str,
    path1: str = "",
    path2: str = "",
    status: str = "ENABLED",
) -> dict:
    """
    Create a Responsive Search Ad (RSA).

    Args:
        ad_group_id: Numeric ad group id.
        headlines: List of 3-15 headlines, each max 30 chars.
        descriptions: List of 2-4 descriptions, each max 90 chars.
        final_url: Absolute URL where users land after click.
        path1: Optional display URL token 1 (max 15 chars).
        path2: Optional display URL token 2 (max 15 chars).
        status: ENABLED (default) | PAUSED.
    """
    try:
        client, customer_id = get_client()
        result = create_responsive_search_ad_impl(
            client=client, customer_id=customer_id,
            ad_group_id=ad_group_id, headlines=headlines,
            descriptions=descriptions, final_url=final_url,
            path1=path1 or None, path2=path2 or None, status=status,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_shared_negative_set(name: str, members: list) -> dict:
    """
    Create a shared negative keyword list (Master Negatives).

    Args:
        name: List name (e.g. "HeyNeuron — Master Negatives").
        members: List of {"keyword_text": str, "match_type": "EXACT"|"PHRASE"|"BROAD"} objects.
    """
    try:
        client, customer_id = get_client()
        result = create_shared_negative_set_impl(
            client=client, customer_id=customer_id,
            name=name, members=members,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def apply_shared_set_to_campaign(campaign_id: int, shared_set_id: int) -> dict:
    """Apply a shared negative keyword list to a campaign."""
    try:
        client, customer_id = get_client()
        result = apply_shared_set_to_campaign_impl(
            client=client, customer_id=customer_id,
            campaign_id=campaign_id, shared_set_id=shared_set_id,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — list & find for agent flow
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_campaigns(only_enabled: bool = False) -> dict:
    """List campaigns on the account (excluding REMOVED)."""
    try:
        client, customer_id = get_client()
        items = list_campaigns_impl(
            client=client, customer_id=customer_id, only_enabled=only_enabled,
        )
        return {"success": True, "total": len(items), "campaigns": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_ad_groups(campaign_id: int = 0) -> dict:
    """List ad groups (optionally filtered by campaign_id, 0 = all)."""
    try:
        client, customer_id = get_client()
        items = list_ad_groups_impl(
            client=client, customer_id=customer_id,
            campaign_id=campaign_id if campaign_id > 0 else None,
        )
        return {"success": True, "total": len(items), "ad_groups": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_campaign_budgets() -> dict:
    """List campaign budgets on the account."""
    try:
        client, customer_id = get_client()
        items = list_campaign_budgets_impl(client=client, customer_id=customer_id)
        return {"success": True, "total": len(items), "budgets": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_shared_sets() -> dict:
    """List shared sets (negative keyword lists, etc.)."""
    try:
        client, customer_id = get_client()
        items = list_shared_sets_impl(client=client, customer_id=customer_id)
        return {"success": True, "total": len(items), "shared_sets": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def find_geo_targets(
    query_text: str,
    locale: str = "pl",
    country_code: str = "PL",
) -> dict:
    """
    Lookup geo target constants by text.

    Args:
        query_text: e.g. "Poland", "Warszawa", "Kraków".
        locale: language of input (default "pl").
        country_code: ISO country code (default "PL").
    """
    try:
        client, _ = get_client()
        items = find_geo_targets_impl(
            client=client, query_text=query_text,
            locale=locale, country_code=country_code,
        )
        return {"success": True, "total": len(items), "targets": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
