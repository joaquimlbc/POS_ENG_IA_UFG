"""Service layer for business logic and orchestration.

This layer contains business rules, domain logic, and service orchestration.
It acts as the bridge between API/controllers and data access layer (repository).

Architecture:
    API Layer → Service Layer → Repository Layer → Database

Services are the single entry point for all business operations.
Controllers should not directly access repositories; they go through services.
"""

from app.service.country_service import CountryService, CountrySyncResult
from app.service.priority_advisor import (
    DataQuality,
    PriorityAdvisor,
    SyncPriority,
    CountryQualityScore,
)

__all__ = [
    # Services
    "CountryService",
    "CountrySyncResult",
    # Priority Advisor
    "PriorityAdvisor",
    "SyncPriority",
    "DataQuality",
    "CountryQualityScore",
]
