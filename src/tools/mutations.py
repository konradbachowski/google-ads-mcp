"""
Write operations for Google Ads — campaign / ad group / keyword / budget mutations.

Designed for use by autonomous agents (e.g. gads-watch daily run) to auto-apply
safe optimizations identified from SQR / KW health checks.

Safety conventions:
  - Status mutations (pause/enable) only flip the status field, never modify
    targeting or bidding.
  - All bid/budget updates accept PLN floats and convert to micros internally.
  - All mutations target a single resource at a time (no bulk) to keep audit
    trail clean.
"""
from __future__ import annotations

from typing import Optional


# ── Helpers ─────────────────────────────────────────────────────────────────
def _to_micros(amount_pln: float) -> int:
    return int(round(amount_pln * 1_000_000))


def _from_micros(micros: int) -> float:
    return round(int(micros) / 1_000_000.0, 2)


# ── Negative keywords ───────────────────────────────────────────────────────
def add_negative_keyword(
    client,
    customer_id: str,
    campaign_id: int,
    keyword_text: str,
    match_type: str = "BROAD",
) -> dict:
    """
    Add a campaign-level negative keyword.

    Use match_type=BROAD for token-level patterns ("praca", "darmowy"),
    PHRASE for word-order patterns ("co to jest"), EXACT for specific queries.
    """
    match_type = match_type.upper()
    if match_type not in {"EXACT", "PHRASE", "BROAD"}:
        raise ValueError(f"match_type must be EXACT/PHRASE/BROAD, got {match_type}")

    campaign_service = client.get_service("CampaignService")
    campaign_criterion_service = client.get_service("CampaignCriterionService")

    op = client.get_type("CampaignCriterionOperation")
    crit = op.create
    crit.campaign = campaign_service.campaign_path(customer_id, campaign_id)
    crit.negative = True
    crit.keyword.text = keyword_text
    crit.keyword.match_type = getattr(
        client.enums.KeywordMatchTypeEnum, match_type
    )

    response = campaign_criterion_service.mutate_campaign_criteria(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    return {
        "resource_name": resource_name,
        "campaign_id": campaign_id,
        "keyword": keyword_text,
        "match_type": match_type,
    }


# ── Keyword status / bid ────────────────────────────────────────────────────
def _set_keyword_status(client, customer_id, ad_group_id, criterion_id, status):
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    op = client.get_type("AdGroupCriterionOperation")
    crit = op.update
    crit.resource_name = ad_group_criterion_service.ad_group_criterion_path(
        customer_id, ad_group_id, criterion_id
    )
    crit.status = getattr(client.enums.AdGroupCriterionStatusEnum, status)

    from google.api_core import protobuf_helpers
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, crit._pb))

    response = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    return response.results[0].resource_name


def pause_keyword(client, customer_id, ad_group_id: int, criterion_id: int) -> dict:
    rn = _set_keyword_status(client, customer_id, ad_group_id, criterion_id, "PAUSED")
    return {"resource_name": rn, "status": "PAUSED"}


def enable_keyword(client, customer_id, ad_group_id: int, criterion_id: int) -> dict:
    rn = _set_keyword_status(client, customer_id, ad_group_id, criterion_id, "ENABLED")
    return {"resource_name": rn, "status": "ENABLED"}


def update_keyword_bid(
    client,
    customer_id: str,
    ad_group_id: int,
    criterion_id: int,
    new_bid_pln: float,
) -> dict:
    """Update max CPC bid on a single keyword (PLN)."""
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    op = client.get_type("AdGroupCriterionOperation")
    crit = op.update
    crit.resource_name = ad_group_criterion_service.ad_group_criterion_path(
        customer_id, ad_group_id, criterion_id
    )
    crit.cpc_bid_micros = _to_micros(new_bid_pln)

    from google.api_core import protobuf_helpers
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, crit._pb))

    response = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    return {
        "resource_name": response.results[0].resource_name,
        "new_bid_pln": new_bid_pln,
    }


# ── Campaign status / budget ────────────────────────────────────────────────
def _set_campaign_status(client, customer_id, campaign_id, status):
    campaign_service = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    camp = op.update
    camp.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
    camp.status = getattr(client.enums.CampaignStatusEnum, status)

    from google.api_core import protobuf_helpers
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, camp._pb))

    response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[op]
    )
    return response.results[0].resource_name


def pause_campaign(client, customer_id, campaign_id: int) -> dict:
    rn = _set_campaign_status(client, customer_id, campaign_id, "PAUSED")
    return {"resource_name": rn, "status": "PAUSED"}


def enable_campaign(client, customer_id, campaign_id: int) -> dict:
    rn = _set_campaign_status(client, customer_id, campaign_id, "ENABLED")
    return {"resource_name": rn, "status": "ENABLED"}


def update_campaign_budget(
    client,
    customer_id: str,
    budget_id: int,
    new_daily_pln: float,
) -> dict:
    """Update daily budget on a CampaignBudget (PLN)."""
    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    bud = op.update
    bud.resource_name = budget_service.campaign_budget_path(customer_id, budget_id)
    bud.amount_micros = _to_micros(new_daily_pln)

    from google.api_core import protobuf_helpers
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, bud._pb))

    response = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[op]
    )
    return {
        "resource_name": response.results[0].resource_name,
        "new_daily_pln": new_daily_pln,
    }


# ── Lookups (helpful for agent flow: find ids before mutating) ──────────────
def find_keyword(client, customer_id: str, keyword_text: str) -> Optional[dict]:
    """Find a keyword by text. Returns first match with ad_group_id + criterion_id."""
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT
          ad_group_criterion.criterion_id,
          ad_group.id,
          ad_group.name,
          campaign.id,
          campaign.name,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          ad_group_criterion.status
        FROM keyword_view
        WHERE ad_group_criterion.keyword.text = '{keyword_text}'
          AND ad_group_criterion.status != 'REMOVED'
        LIMIT 1
    """
    rows = list(ga_service.search(customer_id=customer_id, query=query))
    if not rows:
        return None
    r = rows[0]
    return {
        "criterion_id": int(r.ad_group_criterion.criterion_id),
        "ad_group_id": int(r.ad_group.id),
        "ad_group_name": r.ad_group.name,
        "campaign_id": int(r.campaign.id),
        "campaign_name": r.campaign.name,
        "match_type": r.ad_group_criterion.keyword.match_type.name,
        "status": r.ad_group_criterion.status.name,
    }
