"""
Keyword Metrics Tool
Gets historical metrics for specific keywords
"""

from typing import List, Dict, Any, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def get_keyword_metrics(
    client: GoogleAdsClient,
    customer_id: str,
    keywords: List[str],
    location_ids: Optional[List[int]] = None,
    language_id: int = 1000,
    network: str = "GOOGLE_SEARCH_AND_PARTNERS",
) -> List[Dict[str, Any]]:
    """
    Get historical metrics for specific keywords.

    Args:
        client: GoogleAdsClient instance
        customer_id: Google Ads customer ID (without hyphens)
        keywords: List of keywords to get metrics for
        location_ids: List of geo target constant IDs
        language_id: Language constant ID (default: 1000 for English)
        network: 'GOOGLE_SEARCH' or 'GOOGLE_SEARCH_AND_PARTNERS'

    Returns:
        List of dictionaries with keyword metrics

    Raises:
        ValueError: If keywords list is empty
        GoogleAdsException: If API request fails
    """
    if not keywords:
        raise ValueError("Keywords list cannot be empty")

    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")

    # Build the request (using keyword seed)
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id

    # Set language
    request.language = client.get_service("GoogleAdsService").language_constant_path(
        language_id
    )

    # Set location targeting
    if location_ids:
        for location_id in location_ids:
            request.geo_target_constants.append(
                client.get_service("GoogleAdsService").geo_target_constant_path(
                    location_id
                )
            )

    # Set network
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum[network]

    # Set keyword seed
    request.keyword_seed.keywords.extend(keywords)

    try:
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

        # Parse results
        results = []
        for idea in response:
            metrics = idea.keyword_idea_metrics

            if not metrics:
                continue

            result = {
                "keyword": idea.text,
                "avg_monthly_searches": metrics.avg_monthly_searches,
                "competition": str(metrics.competition),
                "competition_index": metrics.competition_index,
                "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros,
                "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros,
                "low_top_of_page_bid_usd": metrics.low_top_of_page_bid_micros
                / 1_000_000
                if metrics.low_top_of_page_bid_micros
                else 0,
                "high_top_of_page_bid_usd": metrics.high_top_of_page_bid_micros
                / 1_000_000
                if metrics.high_top_of_page_bid_micros
                else 0,
            }

            # Add monthly breakdown if available
            if metrics.monthly_search_volumes:
                result["monthly_breakdown"] = [
                    {
                        "year": vol.year,
                        "month": str(vol.month),
                        "searches": vol.monthly_searches,
                    }
                    for vol in metrics.monthly_search_volumes
                ]

            results.append(result)

        return results

    except GoogleAdsException as ex:
        error_msg = f"Google Ads API error: {ex.error.code().name}"
        for error in ex.failure.errors:
            error_msg += f"\n  - {error.message}"
        raise Exception(error_msg)
