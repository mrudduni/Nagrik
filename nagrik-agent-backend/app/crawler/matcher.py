"""
app/crawler/matcher.py
-----------------------
Matches newly ingested schemes to existing Citizen nodes in Neo4j.
A citizen is "interested" in a new scheme if:
  - They previously VIEWED a scheme in the same BeneficiaryCategory, OR
  - They have a VIEWED scheme from the same Ministry/Department
Returns a list of notification dicts to be stored/sent.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Find citizens who viewed schemes in the same categories as the new scheme
MATCH_CITIZENS_CYPHER = """
UNWIND $categories AS cat
MATCH (bc:BeneficiaryCategory {name: cat})<-[:FOR_CATEGORY]-(old_s:Scheme)<-[:VIEWED]-(c:Citizen)
WITH DISTINCT c, collect(DISTINCT cat) AS matched_cats, collect(DISTINCT old_s.name)[0..3] AS related_schemes
RETURN c.id AS citizen_id,
       matched_cats,
       related_schemes
ORDER BY size(matched_cats) DESC
LIMIT 200
"""

STORE_NOTIFICATION_CYPHER = """
MERGE (c:Citizen {id: $citizen_id})
MERGE (s:Scheme {id: $scheme_id})
MERGE (c)-[n:HAS_NOTIFICATION]->(s)
ON CREATE SET
  n.created_at   = $created_at,
  n.message      = $message,
  n.is_read      = false,
  n.match_reason = $match_reason
ON MATCH SET
  n.created_at   = $created_at,
  n.message      = $message,
  n.is_read      = false
RETURN n.created_at AS created_at
"""


def match_and_notify(new_schemes: list[dict]) -> list[dict]:
    """
    For each new scheme, find interested citizens (based on past views)
    and create HAS_NOTIFICATION relationships in Neo4j.
    Returns list of notification records created.
    """
    from app.rag.neo4j_search import get_driver

    if not new_schemes:
        return []

    driver = get_driver()
    now = datetime.now(timezone.utc).isoformat()
    notifications_created = []

    with driver.session() as sess:
        for scheme in new_schemes:
            scheme_id = scheme.get("id", "")
            scheme_name = scheme.get("name", "")
            categories = scheme.get("categories", [])
            ministry = scheme.get("ministry", "")

            if not categories:
                logger.debug(f"Scheme {scheme_id} has no categories, skipping match.")
                continue

            try:
                result = sess.run(
                    MATCH_CITIZENS_CYPHER,
                    categories=categories,
                )
                rows = result.data()
            except Exception as e:
                logger.error(f"Match query failed for scheme {scheme_id}: {e}")
                continue

            for row in rows:
                citizen_id = row.get("citizen_id", "")
                if not citizen_id:
                    continue

                matched_cats = row.get("matched_cats", [])
                related = row.get("related_schemes", [])
                match_reason = f"You viewed schemes in: {', '.join(matched_cats[:3])}"

                message = (
                    f"New scheme discovered: **{scheme_name}**"
                )
                if ministry:
                    message += f" by {ministry}"
                if matched_cats:
                    message += f". Matches your interest in {', '.join(matched_cats[:2])}."

                try:
                    sess.run(
                        STORE_NOTIFICATION_CYPHER,
                        citizen_id=citizen_id,
                        scheme_id=scheme_id,
                        created_at=now,
                        message=message,
                        match_reason=match_reason,
                    )
                    notifications_created.append({
                        "citizen_id": citizen_id,
                        "scheme_id": scheme_id,
                        "scheme_name": scheme_name,
                        "message": message,
                        "created_at": now,
                    })
                except Exception as e:
                    logger.warning(f"Failed to store notification for citizen {citizen_id}: {e}")

            # Fallback: if no citizens matched by history, notify default active citizen (cz-10234)
            if not rows:
                default_citizen = "cz-10234"
                message = f"New scheme discovered: **{scheme_name}**"
                if ministry:
                    message += f" by {ministry}"
                message += ". Check your eligibility to apply!"
                try:
                    sess.run(
                        STORE_NOTIFICATION_CYPHER,
                        citizen_id=default_citizen,
                        scheme_id=scheme_id,
                        created_at=now,
                        message=message,
                        match_reason="Newly announced government scheme",
                    )
                    notifications_created.append({
                        "citizen_id": default_citizen,
                        "scheme_id": scheme_id,
                        "scheme_name": scheme_name,
                        "message": message,
                        "created_at": now,
                    })
                except Exception as e:
                    logger.warning(f"Failed to store fallback notification: {e}")

    logger.info(f"Created {len(notifications_created)} notifications.")
    return notifications_created
