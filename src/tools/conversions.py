"""
Google Ads conversion management.

Three operations:
  1. create_conversion_action  - define a new conversion (e.g. Booking, Lead).
  2. list_conversion_actions   - read all conversions on the account.
  3. upload_offline_conversion - send a conversion from CRM (HubSpot deal won)
                                  back to Google Ads with gclid + real value.

The third operation is the foundation of LTV-aware Smart Bidding: once a deal
closes in HubSpot we replay it as an offline conversion with the actual contract
value, so the Ads algorithm bids against real revenue, not lead proxies.
"""

from typing import List, Optional


# Conversion categories we actually use. See
# https://developers.google.com/google-ads/api/reference/rpc/latest/ConversionActionCategoryEnum
SUPPORTED_CATEGORIES = {
    "DEFAULT",
    "LEAD",
    "SUBMIT_LEAD_FORM",
    "BOOK_APPOINTMENT",
    "REQUEST_QUOTE",
    "QUALIFIED_LEAD",
    "CONVERTED_LEAD",
    "CONTACT",
    "SIGNUP",
    "PURCHASE",
}


def create_conversion_action(
    client,
    customer_id: str,
    name: str,
    default_value: float,
    category: str = "SUBMIT_LEAD_FORM",
    currency_code: str = "PLN",
    counting_type: str = "ONE_PER_CLICK",
) -> dict:
    """
    Create a new conversion action.

    Returns the resource_name, numeric id, and the snippet pieces (conversion_id
    + conversion_label) needed to wire a GTM tag.
    """
    category = category.upper()
    if category not in SUPPORTED_CATEGORIES:
        raise ValueError(
            f"category must be one of {sorted(SUPPORTED_CATEGORIES)}, got {category!r}"
        )

    conversion_action_service = client.get_service("ConversionActionService")
    op = client.get_type("ConversionActionOperation")
    ca = op.create
    ca.name = name
    ca.type_ = client.enums.ConversionActionTypeEnum.WEBPAGE
    ca.category = getattr(client.enums.ConversionActionCategoryEnum, category)
    ca.status = client.enums.ConversionActionStatusEnum.ENABLED
    ca.value_settings.default_value = default_value
    ca.value_settings.default_currency_code = currency_code
    ca.value_settings.always_use_default_value = False
    ca.counting_type = getattr(
        client.enums.ConversionActionCountingTypeEnum, counting_type.upper()
    )

    response = conversion_action_service.mutate_conversion_actions(
        customer_id=customer_id, operations=[op]
    )
    resource_name = response.results[0].resource_name
    conversion_id_str = resource_name.split("/")[-1]

    # Read back to get tag_snippets so we can return the GTM-ready conversion
    # label without a second round-trip from the caller.
    snippet_query = f"""
        SELECT
          conversion_action.id,
          conversion_action.tag_snippets
        FROM conversion_action
        WHERE conversion_action.resource_name = '{resource_name}'
    """
    ga_service = client.get_service("GoogleAdsService")
    snippet_rows = list(ga_service.search(customer_id=customer_id, query=snippet_query))
    snippets = [
        {
            "type": s.type_.name,
            "page_format": s.page_format.name,
            "global_site_tag": s.global_site_tag,
            "event_snippet": s.event_snippet,
        }
        for row in snippet_rows
        for s in row.conversion_action.tag_snippets
    ]

    return {
        "resource_name": resource_name,
        "id": int(conversion_id_str),
        "name": name,
        "category": category,
        "default_value": default_value,
        "currency_code": currency_code,
        "tag_snippets": snippets,
    }


def list_conversion_actions(client, customer_id: str) -> List[dict]:
    """List all conversion actions on the account."""
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          conversion_action.id,
          conversion_action.name,
          conversion_action.status,
          conversion_action.category,
          conversion_action.type,
          conversion_action.counting_type,
          conversion_action.value_settings.default_value,
          conversion_action.value_settings.default_currency_code,
          conversion_action.value_settings.always_use_default_value
        FROM conversion_action
        ORDER BY conversion_action.id
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    return [
        {
            "id": row.conversion_action.id,
            "name": row.conversion_action.name,
            "status": row.conversion_action.status.name,
            "category": row.conversion_action.category.name,
            "type": row.conversion_action.type_.name,
            "counting_type": row.conversion_action.counting_type.name,
            "default_value": row.conversion_action.value_settings.default_value,
            "currency_code": row.conversion_action.value_settings.default_currency_code,
            "always_use_default_value": row.conversion_action.value_settings.always_use_default_value,
        }
        for row in response
    ]


def upload_offline_conversion(
    client,
    customer_id: str,
    conversion_action_id: int,
    gclid: str,
    conversion_value: float,
    conversion_date_time: str,
    currency_code: str = "PLN",
    order_id: Optional[str] = None,
) -> dict:
    """
    Upload a single offline conversion.

    conversion_date_time format: "YYYY-MM-DD HH:MM:SS+HH:MM" (e.g. timezone-aware).
    Example: "2026-05-18 14:30:00+02:00"
    """
    conversion_upload_service = client.get_service("ConversionUploadService")
    conversion_action_service = client.get_service("ConversionActionService")

    click_conversion = client.get_type("ClickConversion")
    click_conversion.conversion_action = (
        conversion_action_service.conversion_action_path(
            customer_id, conversion_action_id
        )
    )
    click_conversion.gclid = gclid
    click_conversion.conversion_value = conversion_value
    click_conversion.conversion_date_time = conversion_date_time
    click_conversion.currency_code = currency_code
    if order_id:
        click_conversion.order_id = order_id

    response = conversion_upload_service.upload_click_conversions(
        customer_id=customer_id,
        conversions=[click_conversion],
        partial_failure=True,
    )

    results = []
    for result in response.results:
        results.append(
            {
                "gclid": result.gclid,
                "conversion_action": result.conversion_action,
                "conversion_date_time": result.conversion_date_time,
            }
        )

    partial_failure_error = None
    if response.partial_failure_error and response.partial_failure_error.message:
        partial_failure_error = {
            "message": response.partial_failure_error.message,
            "code": response.partial_failure_error.code,
        }

    return {
        "uploaded": len(results),
        "results": results,
        "partial_failure_error": partial_failure_error,
    }
