"""
Filtering utilities for keyword results
"""

from typing import List, Dict, Any, Optional


def filter_by_competition(
    keywords: List[Dict[str, Any]], competition_level: str
) -> List[Dict[str, Any]]:
    """
    Filter keywords by competition level.

    Args:
        keywords: List of keyword dictionaries with 'competition' key
        competition_level: One of 'LOW', 'MEDIUM', 'HIGH', 'UNSPECIFIED'

    Returns:
        Filtered list of keywords
    """
    return [kw for kw in keywords if kw.get("competition") == competition_level]


def filter_by_volume(
    keywords: List[Dict[str, Any]],
    min_searches: Optional[int] = None,
    max_searches: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Filter keywords by average monthly search volume.

    Args:
        keywords: List of keyword dictionaries with 'avg_monthly_searches' key
        min_searches: Minimum average monthly searches (inclusive)
        max_searches: Maximum average monthly searches (inclusive)

    Returns:
        Filtered list of keywords
    """
    filtered = keywords

    if min_searches is not None:
        filtered = [
            kw for kw in filtered if kw.get("avg_monthly_searches", 0) >= min_searches
        ]

    if max_searches is not None:
        filtered = [
            kw for kw in filtered if kw.get("avg_monthly_searches", 0) <= max_searches
        ]

    return filtered


def filter_by_cpc(
    keywords: List[Dict[str, Any]],
    min_cpc_usd: Optional[float] = None,
    max_cpc_usd: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Filter keywords by CPC (Cost Per Click) range.

    Args:
        keywords: List of keyword dictionaries with CPC data
        min_cpc_usd: Minimum CPC in USD (inclusive)
        max_cpc_usd: Maximum CPC in USD (inclusive)

    Returns:
        Filtered list of keywords
    """
    filtered = keywords

    if min_cpc_usd is not None:
        filtered = [
            kw
            for kw in filtered
            if kw.get("low_top_of_page_bid_micros", 0) / 1_000_000 >= min_cpc_usd
        ]

    if max_cpc_usd is not None:
        filtered = [
            kw
            for kw in filtered
            if kw.get("high_top_of_page_bid_micros", 0) / 1_000_000 <= max_cpc_usd
        ]

    return filtered


def sort_keywords(
    keywords: List[Dict[str, Any]],
    sort_by: str = "avg_monthly_searches",
    descending: bool = True,
) -> List[Dict[str, Any]]:
    """
    Sort keywords by a specific metric.

    Args:
        keywords: List of keyword dictionaries
        sort_by: Field to sort by (e.g., 'avg_monthly_searches', 'competition_index')
        descending: Sort in descending order (default: True)

    Returns:
        Sorted list of keywords
    """
    return sorted(keywords, key=lambda x: x.get(sort_by, 0), reverse=descending)
