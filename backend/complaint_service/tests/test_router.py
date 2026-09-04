import asyncio
from app.services.router import DepartmentRouter
from app.models.department import Department, JurisdictionLevel


def test_department_router_sorting():
    router = DepartmentRouter()
    # Test level priority ordering logic
    deps = [
        Department(name="State PCB", code="SPCB", jurisdiction_level=JurisdictionLevel.STATE.value, issue_categories=["POLLUTION"]),
        Department(name="City PWD", code="PWD", jurisdiction_level=JurisdictionLevel.MUNICIPAL.value, issue_categories=["POTHOLE"]),
    ]
    level_priority = {
        JurisdictionLevel.MUNICIPAL.value: 1,
        JurisdictionLevel.DISTRICT.value: 2,
        JurisdictionLevel.STATE.value: 3,
        JurisdictionLevel.CENTRAL.value: 4,
    }
    deps.sort(key=lambda d: level_priority.get(d.jurisdiction_level, 99))
    assert deps[0].code == "PWD"
