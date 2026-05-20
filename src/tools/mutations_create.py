"""
CREATE operations for Google Ads — full campaign lifecycle.

Pattern: each function takes (client, customer_id, ...) and returns dict with
resource_name + relevant ids.

Coverage:
  - create_campaign_budget       (CampaignBudgetService)
  - create_campaign              (CampaignService) — Search-only, Maximize Clicks
  - create_ad_group              (AdGroupService)
  - add_keyword                  (AdGroupCriterionService) — positive KW
  - create_responsive_search_ad  (AdGroupAdService)
  - create_shared_negative_set   (SharedSetService + SharedCriterionService)
  - apply_shared_set_to_campaign (CampaignSharedSetService)

Plus helpers (GAQL-backed):
  - list_campaigns, list_ad_groups, list_campaign_budgets, list_shared_sets
  - find_geo_targets (GeoTargetConstantService.suggest)
"""
from __future__ import annotations

from typing import List, Optional


def _to_micros(amount_pln: float) -> int:
    return int(round(amount_pln * 1_000_000))


# ── Budgets ─────────────────────────────────────────────────────────────────
def create_campaign_budget(
    client,
    customer_id: str,
    name: str,
    daily_pln: float,
    delivery_method: str = "STANDARD",
) -> dict:
    """Create a CampaignBudget resource (shared between campaigns)."""
    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    b = op.create
    b.name = name
    b.amount_micros = _to_micros(daily_pln)
    b.delivery_method = getattr(
        client.enums.BudgetDeliveryMethodEnum, delivery_method.upper()
    )
    response = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    return {
        "resource_name": resource_name,
        "id": int(resource_name.split("/")[-1]),
        "name": name,
        "daily_pln": daily_pln,
    }


# ── Campaigns ───────────────────────────────────────────────────────────────
def create_campaign(
    client,
    customer_id: str,
    name: str,
    budget_id: int,
    advertising_channel_type: str = "SEARCH",
    bidding_strategy_type: str = "MAXIMIZE_CLICKS",
    target_spend_cap_pln: Optional[float] = None,
    geo_target_constant_ids: Optional[List[int]] = None,
    language_constant_ids: Optional[List[int]] = None,
    status: str = "PAUSED",
    network_partner_search: bool = False,
    network_content: bool = False,
) -> dict:
    """
    Create a Search campaign.

    Args:
        name: Campaign display name.
        budget_id: CampaignBudget numeric id.
        advertising_channel_type: SEARCH | DISPLAY | SHOPPING | VIDEO | PERFORMANCE_MAX.
        bidding_strategy_type: MAXIMIZE_CLICKS | MAXIMIZE_CONVERSIONS |
            MAXIMIZE_CONVERSION_VALUE | TARGET_CPA | TARGET_ROAS | MANUAL_CPC.
        target_spend_cap_pln: For MAXIMIZE_CLICKS — optional ceiling per click.
        geo_target_constant_ids: Geo constant ids (e.g. 2616 = Poland).
            Empty/None = no geo filter (worldwide).
        language_constant_ids: Language constant ids
            (1045 = Polish, 1000 = English).
        status: PAUSED (default — safer to set up before flipping) | ENABLED.
        network_partner_search: Include Search Partners (default OFF).
        network_content: Include Display Network (default OFF).
    """
    campaign_service = client.get_service("CampaignService")
    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignOperation")
    c = op.create
    c.name = name
    c.advertising_channel_type = getattr(
        client.enums.AdvertisingChannelTypeEnum, advertising_channel_type.upper()
    )
    c.status = getattr(client.enums.CampaignStatusEnum, status.upper())
    c.campaign_budget = budget_service.campaign_budget_path(customer_id, budget_id)

    # Network settings
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = network_partner_search
    c.network_settings.target_content_network = network_content
    c.network_settings.target_partner_search_network = False

    # EU Digital Services Act (DSA) — required since 2024 for ads served in EU
    c.contains_eu_political_advertising = (
        client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    )

    # Bidding strategy — populate the oneof via CopyFrom on a fresh message
    bst = bidding_strategy_type.upper()
    if bst == "MAXIMIZE_CLICKS":
        target_spend = client.get_type("TargetSpend")
        if target_spend_cap_pln is not None:
            target_spend.cpc_bid_ceiling_micros = _to_micros(target_spend_cap_pln)
        c.target_spend = target_spend
    elif bst == "MAXIMIZE_CONVERSIONS":
        c.maximize_conversions = client.get_type("MaximizeConversions")
    elif bst == "MAXIMIZE_CONVERSION_VALUE":
        c.maximize_conversion_value = client.get_type("MaximizeConversionValue")
    elif bst == "MANUAL_CPC":
        manual = client.get_type("ManualCpc")
        manual.enhanced_cpc_enabled = False
        c.manual_cpc = manual
    else:
        raise ValueError(f"Unsupported bidding_strategy_type: {bidding_strategy_type}")

    operations = [op]
    response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=operations
    )
    resource_name = response.results[0].resource_name
    campaign_id = int(resource_name.split("/")[-1])

    # Apply geo/language criteria (separate mutations on CampaignCriterionService)
    if geo_target_constant_ids or language_constant_ids:
        cc_service = client.get_service("CampaignCriterionService")
        gtc_service = client.get_service("GeoTargetConstantService")
        criteria_ops = []
        for geo_id in (geo_target_constant_ids or []):
            crit_op = client.get_type("CampaignCriterionOperation")
            crit = crit_op.create
            crit.campaign = campaign_service.campaign_path(customer_id, campaign_id)
            crit.location.geo_target_constant = gtc_service.geo_target_constant_path(geo_id)
            criteria_ops.append(crit_op)
        for lang_id in (language_constant_ids or []):
            crit_op = client.get_type("CampaignCriterionOperation")
            crit = crit_op.create
            crit.campaign = campaign_service.campaign_path(customer_id, campaign_id)
            crit.language.language_constant = f"languageConstants/{lang_id}"
            criteria_ops.append(crit_op)
        if criteria_ops:
            cc_service.mutate_campaign_criteria(
                customer_id=customer_id, operations=criteria_ops
            )

    return {
        "resource_name": resource_name,
        "id": campaign_id,
        "name": name,
        "status": status,
        "advertising_channel_type": advertising_channel_type,
        "bidding_strategy_type": bidding_strategy_type,
        "budget_id": budget_id,
    }


# ── Ad groups ───────────────────────────────────────────────────────────────
def create_ad_group(
    client,
    customer_id: str,
    campaign_id: int,
    name: str,
    default_bid_pln: Optional[float] = None,
    type_: str = "SEARCH_STANDARD",
    status: str = "ENABLED",
) -> dict:
    """Create an ad group under a campaign."""
    ad_group_service = client.get_service("AdGroupService")
    campaign_service = client.get_service("CampaignService")
    op = client.get_type("AdGroupOperation")
    ag = op.create
    ag.name = name
    ag.campaign = campaign_service.campaign_path(customer_id, campaign_id)
    ag.type_ = getattr(client.enums.AdGroupTypeEnum, type_.upper())
    ag.status = getattr(client.enums.AdGroupStatusEnum, status.upper())
    if default_bid_pln is not None:
        ag.cpc_bid_micros = _to_micros(default_bid_pln)
    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    return {
        "resource_name": resource_name,
        "id": int(resource_name.split("/")[-1]),
        "name": name,
        "campaign_id": campaign_id,
    }


# ── Positive keywords ───────────────────────────────────────────────────────
def add_keyword(
    client,
    customer_id: str,
    ad_group_id: int,
    text: str,
    match_type: str = "EXACT",
    bid_pln: Optional[float] = None,
) -> dict:
    """Add a positive keyword to an ad group."""
    match_type = match_type.upper()
    if match_type not in {"EXACT", "PHRASE", "BROAD"}:
        raise ValueError(f"match_type must be EXACT/PHRASE/BROAD, got {match_type}")
    ad_group_service = client.get_service("AdGroupService")
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    op = client.get_type("AdGroupCriterionOperation")
    crit = op.create
    crit.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
    crit.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
    crit.keyword.text = text
    crit.keyword.match_type = getattr(client.enums.KeywordMatchTypeEnum, match_type)
    if bid_pln is not None:
        crit.cpc_bid_micros = _to_micros(bid_pln)
    response = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    return {
        "resource_name": resource_name,
        "criterion_id": int(resource_name.split("~")[-1]),
        "ad_group_id": ad_group_id,
        "text": text,
        "match_type": match_type,
    }


# ── Responsive Search Ads ───────────────────────────────────────────────────
def create_responsive_search_ad(
    client,
    customer_id: str,
    ad_group_id: int,
    headlines: List[str],
    descriptions: List[str],
    final_url: str,
    path1: Optional[str] = None,
    path2: Optional[str] = None,
    status: str = "ENABLED",
) -> dict:
    """
    Create a Responsive Search Ad (RSA).

    Limits per Google Ads:
      - Headlines: 3-15, each max 30 chars.
      - Descriptions: 2-4, each max 90 chars.
      - final_url: required absolute URL.
      - path1 + path2: optional display URL tokens (max 15 chars each).
    """
    if not (3 <= len(headlines) <= 15):
        raise ValueError(f"headlines count must be 3..15, got {len(headlines)}")
    if not (2 <= len(descriptions) <= 4):
        raise ValueError(f"descriptions count must be 2..4, got {len(descriptions)}")
    for h in headlines:
        if len(h) > 30:
            raise ValueError(f"headline >30 chars: {h!r}")
    for d in descriptions:
        if len(d) > 90:
            raise ValueError(f"description >90 chars: {d!r}")

    ad_group_service = client.get_service("AdGroupService")
    ad_group_ad_service = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")
    aga = op.create
    aga.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
    aga.status = getattr(client.enums.AdGroupAdStatusEnum, status.upper())

    ad = aga.ad
    ad.final_urls.append(final_url)
    if path1:
        ad.responsive_search_ad.path1 = path1
    if path2:
        ad.responsive_search_ad.path2 = path2

    for h in headlines:
        asset = client.get_type("AdTextAsset")
        asset.text = h
        ad.responsive_search_ad.headlines.append(asset)
    for d in descriptions:
        asset = client.get_type("AdTextAsset")
        asset.text = d
        ad.responsive_search_ad.descriptions.append(asset)

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    return {
        "resource_name": resource_name,
        "ad_group_id": ad_group_id,
        "headlines_count": len(headlines),
        "descriptions_count": len(descriptions),
    }


# ── Shared negative keyword sets ────────────────────────────────────────────
def create_shared_negative_set(
    client,
    customer_id: str,
    name: str,
    members: List[dict],
) -> dict:
    """
    Create a shared negative keyword list and populate it.

    members: list of {"keyword_text": str, "match_type": EXACT|PHRASE|BROAD}.
    """
    shared_set_service = client.get_service("SharedSetService")
    shared_criterion_service = client.get_service("SharedCriterionService")

    set_op = client.get_type("SharedSetOperation")
    s = set_op.create
    s.name = name
    s.type_ = client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS

    set_response = shared_set_service.mutate_shared_sets(
        customer_id=customer_id, operations=[set_op]
    )
    set_resource_name = set_response.results[0].resource_name
    set_id = int(set_resource_name.split("/")[-1])

    crit_ops = []
    for m in members:
        op = client.get_type("SharedCriterionOperation")
        crit = op.create
        crit.shared_set = set_resource_name
        crit.keyword.text = m["keyword_text"]
        crit.keyword.match_type = getattr(
            client.enums.KeywordMatchTypeEnum, m.get("match_type", "BROAD").upper()
        )
        crit_ops.append(op)

    if crit_ops:
        shared_criterion_service.mutate_shared_criteria(
            customer_id=customer_id, operations=crit_ops
        )

    return {
        "resource_name": set_resource_name,
        "id": set_id,
        "name": name,
        "members_added": len(crit_ops),
    }


def apply_shared_set_to_campaign(
    client,
    customer_id: str,
    campaign_id: int,
    shared_set_id: int,
) -> dict:
    """Apply a shared negative keyword list to a campaign."""
    campaign_shared_set_service = client.get_service("CampaignSharedSetService")
    campaign_service = client.get_service("CampaignService")
    shared_set_service = client.get_service("SharedSetService")

    op = client.get_type("CampaignSharedSetOperation")
    css = op.create
    css.campaign = campaign_service.campaign_path(customer_id, campaign_id)
    css.shared_set = shared_set_service.shared_set_path(customer_id, shared_set_id)

    response = campaign_shared_set_service.mutate_campaign_shared_sets(
        customer_id=customer_id, operations=[op]
    )
    return {
        "resource_name": response.results[0].resource_name,
        "campaign_id": campaign_id,
        "shared_set_id": shared_set_id,
    }


# ── Helpers (list / find) ───────────────────────────────────────────────────
def list_campaigns(client, customer_id: str, only_enabled: bool = False) -> list:
    ga_service = client.get_service("GoogleAdsService")
    where = "campaign.status != 'REMOVED'"
    if only_enabled:
        where = "campaign.status = 'ENABLED'"
    rows = list(ga_service.search(
        customer_id=customer_id,
        query=f"""
            SELECT
              campaign.id, campaign.name, campaign.status,
              campaign.advertising_channel_type,
              campaign_budget.amount_micros, campaign_budget.id
            FROM campaign
            WHERE {where}
            ORDER BY campaign.id
        """,
    ))
    return [
        {
            "id": int(r.campaign.id),
            "name": r.campaign.name,
            "status": r.campaign.status.name,
            "channel": r.campaign.advertising_channel_type.name,
            "budget_id": int(r.campaign_budget.id),
            "daily_pln": round(int(r.campaign_budget.amount_micros) / 1_000_000.0, 2),
        }
        for r in rows
    ]


def list_ad_groups(client, customer_id: str, campaign_id: Optional[int] = None) -> list:
    ga_service = client.get_service("GoogleAdsService")
    where = "ad_group.status != 'REMOVED'"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"
    rows = list(ga_service.search(
        customer_id=customer_id,
        query=f"""
            SELECT
              ad_group.id, ad_group.name, ad_group.status,
              campaign.id, campaign.name
            FROM ad_group
            WHERE {where}
            ORDER BY ad_group.id
        """,
    ))
    return [
        {
            "id": int(r.ad_group.id),
            "name": r.ad_group.name,
            "status": r.ad_group.status.name,
            "campaign_id": int(r.campaign.id),
            "campaign_name": r.campaign.name,
        }
        for r in rows
    ]


def list_campaign_budgets(client, customer_id: str) -> list:
    ga_service = client.get_service("GoogleAdsService")
    rows = list(ga_service.search(
        customer_id=customer_id,
        query="""
            SELECT
              campaign_budget.id, campaign_budget.name,
              campaign_budget.status, campaign_budget.amount_micros
            FROM campaign_budget
            WHERE campaign_budget.status != 'REMOVED'
            ORDER BY campaign_budget.id
        """,
    ))
    return [
        {
            "id": int(r.campaign_budget.id),
            "name": r.campaign_budget.name,
            "status": r.campaign_budget.status.name,
            "daily_pln": round(int(r.campaign_budget.amount_micros) / 1_000_000.0, 2),
        }
        for r in rows
    ]


def list_shared_sets(client, customer_id: str) -> list:
    ga_service = client.get_service("GoogleAdsService")
    rows = list(ga_service.search(
        customer_id=customer_id,
        query="""
            SELECT
              shared_set.id, shared_set.name, shared_set.type,
              shared_set.status, shared_set.member_count
            FROM shared_set
            WHERE shared_set.status != 'REMOVED'
        """,
    ))
    return [
        {
            "id": int(r.shared_set.id),
            "name": r.shared_set.name,
            "type": r.shared_set.type_.name,
            "members": int(r.shared_set.member_count),
        }
        for r in rows
    ]


def find_geo_targets(client, query_text: str, locale: str = "pl", country_code: str = "PL") -> list:
    """Lookup geo target constants by text (e.g. 'Poland', 'Warszawa')."""
    gtc_service = client.get_service("GeoTargetConstantService")
    req = client.get_type("SuggestGeoTargetConstantsRequest")
    req.locale = locale
    req.country_code = country_code
    req.location_names.names.append(query_text)
    response = gtc_service.suggest_geo_target_constants(request=req)
    return [
        {
            "id": int(s.geo_target_constant.id),
            "name": s.geo_target_constant.name,
            "country_code": s.geo_target_constant.country_code,
            "target_type": s.geo_target_constant.target_type,
            "status": s.geo_target_constant.status.name,
            "reach": int(s.reach) if s.reach else 0,
        }
        for s in response.geo_target_constant_suggestions
    ]
