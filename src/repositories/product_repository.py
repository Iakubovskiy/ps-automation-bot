"""Stub repository for fetching product data from Google Sheets.

This module will be implemented later with actual Google Sheets integration.
"""


async def fetch_product_from_sheet(product_id: str) -> dict:
    """Fetch a product row from Google Sheets by product ID.

    Args:
        product_id: The unique identifier of the product in the sheet.

    Returns:
        A dict whose keys match the Sheets-sourced fields of ProductData,
        e.g. {"price": "1200", "steel": "D2", "photo_links": [...], ...}

    Raises:
        NotImplementedError: Always — this is a stub to be filled in later.
    """
    raise NotImplementedError(
        "Google Sheets integration is not implemented yet. "
        "Implement this function to query the sheet by product_id."
    )
