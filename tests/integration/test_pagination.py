"""Integration tests for pagination functionality.

Priority: CRITICAL
Test Suite: Pagination Correctness
Tests data retrieval with pagination for dashboard operations.
"""

from app.service.country_service import CountryService


class TestPagination:
    """Test suite for list operations with pagination."""

    def test_list_countries_default_pagination(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify default pagination parameters work correctly.

        Business rule: list_countries() should return paginated results.
        Expected: First page with default limit returns correct items.
        Why: Dashboard depends on paginated data retrieval.
        """
        result = service_with_250_countries.list_countries()

        assert result.total == 250
        assert result.page == 1
        assert result.pages == 13  # ceil(250 / 20)
        assert len(result.items) == 20  # Default limit
        assert result.limit == 20

    def test_list_countries_custom_page_size(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify custom page size parameter is respected.

        Business rule: limit parameter should control items per page.
        Expected: page=1, limit=50 returns 50 items, 5 total pages.
        Why: Allows flexible pagination for different clients.
        """
        result = service_with_250_countries.list_countries(page=1, limit=50)

        assert result.total == 250
        assert result.page == 1
        assert result.pages == 5  # ceil(250 / 50)
        assert len(result.items) == 50
        assert result.limit == 50

    def test_list_countries_second_page(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify pagination to second page returns different items.

        Business rule: Each page should contain unique items.
        Expected: page=2, limit=20 returns items 21-40.
        Why: Validates proper offset calculation.
        """
        page1 = service_with_250_countries.list_countries(page=1, limit=20)
        page2 = service_with_250_countries.list_countries(page=2, limit=20)

        # Get IDs to verify different items
        page1_ids = {item.id for item in page1.items}
        page2_ids = {item.id for item in page2.items}

        assert page1_ids.isdisjoint(page2_ids), "Pages should have no overlap"
        assert len(page2.items) == 20
        assert page2.page == 2

    def test_list_countries_last_page_partial(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify last page returns remaining items (less than limit).

        Business rule: Last page may have fewer items than limit.
        Expected: page=13, limit=20 returns 10 items (250 % 20).
        Why: Validates correct handling of partial pages.
        """
        last_page = service_with_250_countries.list_countries(page=13, limit=20)

        assert len(last_page.items) == 10  # 250 % 20
        assert last_page.page == 13
        assert last_page.pages == 13

    def test_list_countries_all_items_unique(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify all paginated items are unique across pages.

        Business rule: No item should appear in multiple pages.
        Expected: Iterating all pages yields 250 unique items.
        Why: Prevents data duplication in paginated results.
        """
        all_ids = set()
        limit = 20

        for page in range(1, 14):  # 13 pages total
            result = service_with_250_countries.list_countries(page=page, limit=limit)

            page_ids = {item.id for item in result.items}
            duplicates = all_ids & page_ids

            assert not duplicates, f"Duplicate IDs found on page {page}: {duplicates}"
            all_ids.update(page_ids)

        assert len(all_ids) == 250

    def test_list_countries_with_region_filter(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify region filter works with pagination.

        Business rule: Filter parameter should reduce result set.
        Expected: region='Europe' returns only European countries.
        Why: Dashboard filters depend on this functionality.
        """
        result = service_with_250_countries.list_countries(region="Europe", limit=100)

        # With 250 countries and 5 regions, expect ~50 European countries
        assert result.total == 50
        assert result.pages == 1  # Fits in one page with limit=100

        # Verify all returned items are from specified region
        for item in result.items:
            assert item.region == "Europe"

    def test_list_countries_invalid_page_number(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify handling of invalid page number.

        Business rule: A: definir (behavior for page > max_pages not specified).
        Expected: Either returns empty result or raises error.
        Why: Edge case for client error handling.
        """
        result = service_with_250_countries.list_countries(page=100, limit=20)

        # Either returns empty or error - behavior to be defined in requirements
        assert result.total == 250  # Total should still be correct
        assert result.page == 100

    def test_list_countries_pagination_metadata(
        self, service_with_250_countries: CountryService
    ) -> None:
        """Verify pagination metadata is accurate for all pages.

        Business rule: total, pages, page metadata must be consistent.
        Expected: Metadata correctly reflects dataset and position.
        Why: Frontend pagination controls depend on accurate metadata.
        """
        result = service_with_250_countries.list_countries(page=1, limit=20)

        # Verify math consistency
        assert result.pages == (result.total + result.limit - 1) // result.limit
        assert result.page == 1
        assert result.limit == 20
        assert result.total == 250
