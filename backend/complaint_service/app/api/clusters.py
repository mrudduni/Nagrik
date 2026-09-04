import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.complaint import Complaint
from app.models.complaint_cluster import ComplaintCluster
from app.schemas.cluster import ClusterInfo, ClusterDetail, SimilarComplaint
from app.services.clusterer import ComplaintClusterer

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("/", response_model=List[ClusterInfo])
async def list_clusters(
    cluster_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    min_count: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """List complaint clusters with optional status, category, and size filters."""
    query = select(ComplaintCluster)

    if cluster_status:
        query = query.where(ComplaintCluster.status == cluster_status)
    if category:
        query = query.where(ComplaintCluster.category == category)
    if min_count > 1:
        query = query.where(ComplaintCluster.complaint_count >= min_count)

    query = query.order_by(desc(ComplaintCluster.complaint_count))
    result = await db.execute(query)
    clusters = result.scalars().all()

    return [
        ClusterInfo(
            id=c.id,
            category=c.category,
            centroid_lat=c.centroid_lat,
            centroid_lon=c.centroid_lon,
            complaint_count=c.complaint_count,
            avg_severity=c.avg_severity,
            status=c.status,
            representative_complaint=c.representative_complaint_id,
        )
        for c in clusters
    ]


@router.get("/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(cluster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific cluster, including member complaints."""
    query = (
        select(ComplaintCluster)
        .options(selectinload(ComplaintCluster.complaints))
        .where(ComplaintCluster.id == cluster_id)
    )
    result = await db.execute(query)
    cluster = result.scalar_one_or_none()

    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    member_complaints = [
        SimilarComplaint(
            complaint_id=c.id,
            title=c.title,
            category=c.category,
            similarity_score=1.0,
            created_at=c.created_at,
        )
        for c in (cluster.complaints or [])
    ]

    return ClusterDetail(
        id=cluster.id,
        category=cluster.category,
        centroid_lat=cluster.centroid_lat,
        centroid_lon=cluster.centroid_lon,
        complaint_count=cluster.complaint_count,
        avg_severity=cluster.avg_severity,
        status=cluster.status,
        representative_complaint=cluster.representative_complaint_id,
        member_complaints=member_complaints,
    )


@router.post("/rerun")
async def rerun_clustering(db: AsyncSession = Depends(get_db)):
    """Trigger manual re-clustering of unclustered complaints using DBSCAN."""
    from app.main import get_embedding_service

    embedding_svc = get_embedding_service()
    clusterer = ComplaintClusterer(embedding_svc)
    new_clusters = await clusterer.run_clustering(db)
    return {"status": "success", "new_clusters_created": new_clusters}
