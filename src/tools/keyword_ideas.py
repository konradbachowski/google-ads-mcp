"""
Keyword Ideas Tool
Generates keyword suggestions using Google Ads API KeywordPlanIdeaService
"""

from typing import List, Optional, Dict, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def generate_keyword_ideas(
    client: GoogleAdsClient,
    customer_id: str,
    keywords: Optional[List[str]] = None,
    url: Optional[str] = None,
    location_ids: Optional[List[int]] = None,
    language_id: int = 1000,  # English by default
    network: str = "GOOGLE_SEARCH_AND_PARTNERS",
    include_adult_keywords: bool = False,
    page_size: int = 100,
) -> List[Dict[str, Any]]:
    """
    Generate keyword ideas using Google Ads API.

    Args:
        client: GoogleAdsClient instance
        customer_id: Google Ads customer ID (without hyphens)
        keywords: List of seed keywords (optional)
        url: Seed URL for keyword generation (optional)
        location_ids: List of geo target constant IDs (e.g., [2840] for USA)
        language_id: Language constant ID (default: 1000 for English)
        network: 'GOOGLE_SEARCH' or 'GOOGLE_SEARCH_AND_PARTNERS'
        include_adult_keywords: Whether to include adult keywords
        page_size: Number of results per page (max: 10000)

    Returns:
        List of dictionaries with keyword ideas and metrics

    Raises:
        ValueError: If neither keywords nor URL provided
        GoogleAdsException: If API request fails
    """
    if not keywords and not url:
        raise ValueError("At least one of keywords or url must be provided")

    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")

    # Build the request
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

    # Set adult keywords flag
    request.include_adult_keywords = include_adult_keywords

    # Set seeds
    if keywords and url:
        # Both keywords and URL
        request.keyword_and_url_seed.url = url
        request.keyword_and_url_seed.keywords.extend(keywords)
    elif keywords:
        # Only keywords
        request.keyword_seed.keywords.extend(keywords)
    elif url:
        # Only URL
        request.url_seed.url = url

    # Set page size
    request.page_size = page_size

    try:
        # Make the API request
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

        # Parse results
        results = []
        for idea in response:
            metrics = idea.keyword_idea_metrics

            result = {
                "keyword": idea.text,
                "avg_monthly_searches": metrics.avg_monthly_searches if metrics else 0,
                "competition": str(metrics.competition) if metrics else "UNSPECIFIED",
                "competition_index": metrics.competition_index if metrics else 0,
                "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros
                if metrics
                else 0,
                "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros
                if metrics
                else 0,
            }

            # Add monthly search volumes if available
            if metrics and metrics.monthly_search_volumes:
                result["monthly_search_volumes"] = [
                    {
                        "year": vol.year,
                        "month": str(vol.month),
                        "monthly_searches": vol.monthly_searches,
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
