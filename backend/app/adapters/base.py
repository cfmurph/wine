from typing import Protocol, runtime_checkable


@runtime_checkable
class WineProviderAdapter(Protocol):
    """Common interface every external wine data provider must implement."""

    async def search_wines(self, query: str, filters: dict) -> list[dict]:
        """Return a list of raw wine dicts matching the query/filters."""
        ...

    async def get_wine_detail(self, external_id: str) -> dict:
        """Return a single raw wine dict for the given provider-specific ID."""
        ...

    async def get_prices(self, external_id: str) -> dict:
        """Return pricing summary dict for the given provider-specific ID."""
        ...
