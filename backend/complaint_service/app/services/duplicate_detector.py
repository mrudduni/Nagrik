import math
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.embedder import EmbeddingService
from app.models.complaint import Complaint
from app.schemas.cluster import DuplicateCheckResult, SimilarComplaint
from app.config import settings


class DuplicateDetector:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    async def detect_duplicates(
        self,
        complaint_text: str,
        category: str,
        lat: Optional[float],
        lon: Optional[float],
        db: AsyncSession,
    ) -> DuplicateCheckResult:
        # 1. Search semantically similar vectors via FAISS
        similar_items = self.embedding_service.search_similar(complaint_text, top_k=20)
        if not similar_items:
            return DuplicateCheckResult(is_duplicate=False, similar_complaints=[], suggested_cluster_id=None)

        similar_complaints: List[SimilarComplaint] = []
        suggested_cluster_id: Optional[uuid.UUID] = None
        highest_score = 0.0

        threshold = settings.DUPLICATE_SIMILARITY_THRESHOLD
        category_boost_val = settings.DUPLICATE_CATEGORY_BOOST

        for comp_id_str, sim_score in similar_items:
            try:
                comp_id = uuid.UUID(comp_id_str)
            except (ValueError, TypeError):
                continue

            result = await db.execute(select(Complaint).where(Complaint.id == comp_id))
            existing_comp = result.scalar_one_or_none()
            if not existing_comp:
                continue

            # 2. Category matching boost/penalty
            cat_val = existing_comp.category.value if hasattr(existing_comp.category, "value") else str(existing_comp.category)
            category_boost = category_boost_val if cat_val == category else -0.15

            # 3. Proximity score (if lat/lon available)
            proximity_boost = 0.0
            if (
                lat is not None
                and lon is not None
                and existing_comp.latitude is not None
                and existing_comp.longitude is not None
            ):
                dist_km = self._haversine_distance(lat, lon, existing_comp.latitude, existing_comp.longitude)
                if dist_km <= 2.0:  # Within 2km radius
                    proximity_boost = 0.2 * (1.0 - (dist_km / 2.0))
                else:
                    proximity_boost = -0.05

            final_score = sim_score + category_boost + proximity_boost

            if final_score >= 0.70:
                similar_complaints.append(
                    SimilarComplaint(
                        complaint_id=existing_comp.id,
                        title=existing_comp.title,
                        category=existing_comp.category,
                        similarity_score=round(float(final_score), 3),
                        created_at=existing_comp.created_at,
                    )
                )

                if final_score > highest_score:
                    highest_score = final_score
                    if existing_comp.cluster_id:
                        suggested_cluster_id = existing_comp.cluster_id

        similar_complaints.sort(key=lambda x: x.similarity_score, reverse=True)
        is_duplicate = len(similar_complaints) > 0 and highest_score >= threshold

        return DuplicateCheckResult(
            is_duplicate=is_duplicate,
            similar_complaints=similar_complaints,
            suggested_cluster_id=suggested_cluster_id,
        )

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance in kilometers."""
        r = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return float(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
