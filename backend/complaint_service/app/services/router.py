from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.department import Department, JurisdictionLevel


class DepartmentRouter:
    async def route_complaint(
        self,
        category: str,
        state: Optional[str],
        district: Optional[str],
        db: AsyncSession,
    ) -> Optional[Department]:
        """
        Route complaint to appropriate department based on category and jurisdiction.
        """
        # 1. Fetch all active departments
        query = select(Department).where(Department.is_active == True)
        result = await db.execute(query)
        departments = result.scalars().all()

        if not departments:
            return None

        # 2. Find departments matching category in their issue_categories
        matching_deps = []
        for d in departments:
            if d.issue_categories and category in d.issue_categories:
                matching_deps.append(d)

        if not matching_deps:
            # Fallback: General complaints cell or first available
            for d in departments:
                if d.code == "GENERAL" or "OTHER" in (d.issue_categories or []):
                    return d
            return departments[0]

        # 3. Prefer MUNICIPAL > DISTRICT > STATE > CENTRAL
        level_priority = {
            JurisdictionLevel.MUNICIPAL.value: 1,
            JurisdictionLevel.DISTRICT.value: 2,
            JurisdictionLevel.STATE.value: 3,
            JurisdictionLevel.CENTRAL.value: 4,
            "MUNICIPAL": 1,
            "DISTRICT": 2,
            "STATE": 3,
            "CENTRAL": 4,
        }

        matching_deps.sort(key=lambda d: level_priority.get(d.jurisdiction_level, 99))
        return matching_deps[0]
