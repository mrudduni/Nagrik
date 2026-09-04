import uuid
from datetime import datetime, timedelta, timezone
from typing import List
import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.complaint import Complaint
from app.models.complaint_cluster import ComplaintCluster, ClusterStatus
from app.services.embedder import EmbeddingService
from app.config import settings


class ComplaintClusterer:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    async def run_clustering(self, db: AsyncSession) -> int:
        """Run DBSCAN clustering on recent active unclustered complaints."""
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        query = select(Complaint).where(
            and_(
                Complaint.cluster_id == None,
                Complaint.status.not_in(["CLOSED", "CITIZEN_VERIFIED"]),
                Complaint.created_at >= thirty_days_ago,
            )
        )
        result = await db.execute(query)
        complaints = result.scalars().all()

        if len(complaints) < 3:
            return 0

        embeddings = []
        valid_complaints: List[Complaint] = []

        for c in complaints:
            try:
                emb = self.embedding_service.generate_embedding(c.description or c.title)
                embeddings.append(emb)
                valid_complaints.append(c)
            except Exception:
                continue

        if len(embeddings) < 3:
            return 0

        x = np.array(embeddings)
        clustering = DBSCAN(eps=0.35, min_samples=2, metric="cosine").fit(x)
        labels = clustering.labels_

        unique_labels = set(labels)
        new_clusters_count = 0

        for label in unique_labels:
            if label == -1:
                continue

            cluster_complaints = [valid_complaints[i] for i, l in enumerate(labels) if l == label]
            if not cluster_complaints:
                continue

            main_category = cluster_complaints[0].category
            cat_val = main_category.value if hasattr(main_category, "value") else str(main_category)

            cluster = ComplaintCluster(
                id=uuid.uuid4(),
                representative_complaint_id=cluster_complaints[0].id,
                category=cat_val,
                status=ClusterStatus.ACTIVE.value,
                complaint_count=len(cluster_complaints),
                avg_severity=float(np.mean([c.severity for c in cluster_complaints])),
            )
            db.add(cluster)
            new_clusters_count += 1

            for c in cluster_complaints:
                c.cluster_id = cluster.id

            await db.flush()
            await self.update_cluster_stats(cluster.id, db)

        await db.commit()
        return new_clusters_count

    async def update_cluster_stats(self, cluster_id: uuid.UUID, db: AsyncSession) -> None:
        """Update cluster statistics based on member complaints."""
        query = select(Complaint).where(Complaint.cluster_id == cluster_id)
        result = await db.execute(query)
        complaints = result.scalars().all()

        if not complaints:
            return

        total_severity = sum(c.severity for c in complaints if c.severity)
        avg_severity = total_severity / len(complaints) if complaints else 3.0

        lats = [c.latitude for c in complaints if c.latitude is not None]
        lons = [c.longitude for c in complaints if c.longitude is not None]

        centroid_lat = sum(lats) / len(lats) if lats else None
        centroid_lon = sum(lons) / len(lons) if lons else None

        cluster_query = select(ComplaintCluster).where(ComplaintCluster.id == cluster_id)
        cluster_result = await db.execute(cluster_query)
        cluster = cluster_result.scalar_one_or_none()

        if cluster:
            cluster.complaint_count = len(complaints)
            cluster.avg_severity = float(avg_severity)
            cluster.centroid_lat = centroid_lat
            cluster.centroid_lon = centroid_lon

        await db.commit()
