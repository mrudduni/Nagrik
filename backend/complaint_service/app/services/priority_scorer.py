from datetime import datetime, timezone
from typing import Optional, Tuple
from app.models.complaint import Complaint


class PriorityScorer:
    async def calculate_priority(
        self,
        complaint: Optional[Complaint] = None,
        severity: Optional[int] = None,
        cluster_size: int = 0,
        days_open: int = 0,
    ) -> Tuple[float, str]:
        """
        Calculate priority score (0-100) and priority tier.
        Can be called with an existing Complaint or with raw parameters.
        """
        if complaint is not None:
            sev = complaint.severity or 3
            if complaint.created_at:
                now = datetime.now(timezone.utc)
                created = complaint.created_at
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                days_open = max(0, (now - created).days)
        else:
            sev = severity if severity is not None else 3

        # Formula:
        # Severity component: up to 75 points (1=15, 2=30, 3=45, 4=60, 5=75)
        severity_component = sev * 15

        # Cluster component: up to 15 points (high report volume in cluster)
        cluster_component = min(cluster_size * 3, 15)

        # Age component: up to 10 points (0.5 pt per open day, max 20 days)
        age_component = min(days_open * 0.5, 10.0)

        score = float(min(max(severity_component + cluster_component + age_component, 0), 100))

        if score >= 80:
            tier = "CRITICAL"
        elif score >= 60:
            tier = "HIGH"
        elif score >= 40:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return score, tier
