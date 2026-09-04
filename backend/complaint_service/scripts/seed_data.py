"""
Seed Data Script for Nagrik Complaint Service
Populates:
1. 15 Real Indian Municipal Departments
2. SLA Rules per Category and Severity
3. 50 Realistic Civic Complaints (with clusters in Koramangala Bangalore, Dwarka Delhi, Andheri Mumbai)
4. Event Timelines for complaints
"""
import os
import sys
import uuid
import asyncio
from datetime import datetime, timedelta, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, async_session_maker
from app.models.department import Department, JurisdictionLevel
from app.models.sla_config import SLAConfig
from app.models.complaint import Complaint, ComplaintCategory, PriorityTier, ComplaintStatus
from app.models.complaint_cluster import ComplaintCluster, ClusterStatus
from app.models.complaint_event import ComplaintEvent, EventType
from sqlalchemy import select


DEPARTMENTS_DATA = [
    {
        "name": "Public Works Department (PWD)",
        "code": "PWD",
        "description": "Roads, bridges, public infrastructure, and stormwater drains.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["POTHOLE", "DRAINAGE", "ENCROACHMENT"],
        "contact_email": "helpdesk@pwd.gov.in",
        "contact_phone": "+91-11-23345678",
    },
    {
        "name": "Bangalore Water Supply and Sewerage Board (BWSSB)",
        "code": "BWSSB",
        "description": "Water supply, sewage systems, and water quality testing.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["WATER_SUPPLY", "DRAINAGE"],
        "contact_email": "support@bwssb.gov.in",
        "contact_phone": "+91-80-22221188",
    },
    {
        "name": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "code": "BBMP",
        "description": "Solid waste, sanitation, streetlights, civic infrastructure.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION", "STREETLIGHT", "ENCROACHMENT", "POTHOLE"],
        "contact_email": "commissioner@bbmp.gov.in",
        "contact_phone": "+91-80-22660000",
    },
    {
        "name": "Solid Waste Management Cell (SWM)",
        "code": "SWM",
        "description": "Door-to-door garbage collection, waste segregation, and disposal.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION"],
        "contact_email": "swm-cell@urban.gov.in",
        "contact_phone": "+91-80-22975555",
    },
    {
        "name": "Traffic Police Department",
        "code": "TRAFFIC_POLICE",
        "description": "Traffic control, signals, parking enforcement, and congestion.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["TRAFFIC"],
        "contact_email": "traffic@police.gov.in",
        "contact_phone": "103",
    },
    {
        "name": "Bangalore Electricity Supply Company (BESCOM)",
        "code": "BESCOM",
        "description": "Power distribution, transformer maintenance, and street electric poles.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["ELECTRICITY", "STREETLIGHT"],
        "contact_email": "helpline@bescom.co.in",
        "contact_phone": "1912",
    },
    {
        "name": "State Pollution Control Board (SPCB)",
        "code": "SPCB",
        "description": "Air quality, industrial effluents, noise pollution, and water pollution monitoring.",
        "jurisdiction_level": JurisdictionLevel.STATE.value,
        "issue_categories": ["POLLUTION", "NOISE"],
        "contact_email": "pcb-enquiry@spcb.gov.in",
        "contact_phone": "+91-80-25589112",
    },
    {
        "name": "Metropolitan Transport Corporation (BMTC)",
        "code": "BMTC",
        "description": "Public bus routes, scheduling, bus shelters, and fleet operations.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["PUBLIC_TRANSPORT"],
        "contact_email": "grievance@mybmtc.com",
        "contact_phone": "+91-80-22483777",
    },
    {
        "name": "Municipal Corporation of Delhi (MCD)",
        "code": "MCD",
        "description": "Sanitation, public health, parks, local roads, and building bylaws.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION", "POTHOLE", "DRAINAGE", "STREETLIGHT", "ENCROACHMENT"],
        "contact_email": "controlroom@mcd.gov.in",
        "contact_phone": "+91-11-155305",
    },
    {
        "name": "Delhi Jal Board (DJB)",
        "code": "DJB",
        "description": "Potable water supply and wastewater management across NCT Delhi.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["WATER_SUPPLY", "DRAINAGE"],
        "contact_email": "djbcomplaints@delhi.gov.in",
        "contact_phone": "1916",
    },
    {
        "name": "Delhi Transport Corporation (DTC)",
        "code": "DTC",
        "description": "City bus network, electric buses, and depot facilities.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["PUBLIC_TRANSPORT"],
        "contact_email": "complaints@dtc.gov.in",
        "contact_phone": "+91-11-23370233",
    },
    {
        "name": "Brihanmumbai Municipal Corporation (BMC)",
        "code": "BMC",
        "description": "Greater Mumbai civic amenities, water pipeline, solid waste, disaster management.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION", "POTHOLE", "DRAINAGE", "STREETLIGHT", "WATER_SUPPLY"],
        "contact_email": "mc@mcgm.gov.in",
        "contact_phone": "1916",
    },
    {
        "name": "Greater Chennai Corporation (GCC)",
        "code": "GCC",
        "description": "Civic services, stormwater drains, solid waste, and roads in Chennai.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION", "POTHOLE", "DRAINAGE", "STREETLIGHT", "WATER_SUPPLY"],
        "contact_email": "commr@chennaicorporation.gov.in",
        "contact_phone": "1913",
    },
    {
        "name": "Kolkata Municipal Corporation (KMC)",
        "code": "KMC",
        "description": "Water supply, drainage, building approval, lighting in Kolkata.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["GARBAGE", "SANITATION", "POTHOLE", "DRAINAGE", "STREETLIGHT", "WATER_SUPPLY"],
        "contact_email": "mayor@kmcgov.in",
        "contact_phone": "+91-33-22861000",
    },
    {
        "name": "General Public Grievance Cell",
        "code": "GENERAL",
        "description": "Centralized citizen grievance cell for inter-departmental issues.",
        "jurisdiction_level": JurisdictionLevel.MUNICIPAL.value,
        "issue_categories": ["OTHER", "NOISE", "ENCROACHMENT"],
        "contact_email": "grievance@nagrik.gov.in",
        "contact_phone": "1800-111-222",
    },
]

ESCALATION_LEVELS = [
    {"level": 1, "hours_after_deadline": 24, "notify": "department_head"},
    {"level": 2, "hours_after_deadline": 72, "notify": "district_authority"},
    {"level": 3, "hours_after_deadline": 168, "notify": "state_dashboard"},
]


async def seed_data():
    print("Initializing tables...")
    await init_db()

    async with async_session_maker() as db:
        print("Checking existing departments...")
        existing_dept = await db.execute(select(Department))
        dept_map = {}

        if not existing_dept.scalars().first():
            print(f"Seeding {len(DEPARTMENTS_DATA)} departments...")
            for d_data in DEPARTMENTS_DATA:
                dept = Department(
                    id=uuid.uuid4(),
                    name=d_data["name"],
                    code=d_data["code"],
                    description=d_data["description"],
                    jurisdiction_level=d_data["jurisdiction_level"],
                    issue_categories=d_data["issue_categories"],
                    contact_email=d_data["contact_email"],
                    contact_phone=d_data["contact_phone"],
                    is_active=True,
                )
                db.add(dept)
                dept_map[d_data["code"]] = dept
            await db.commit()
            print("Departments seeded successfully.")
        else:
            all_deps = (await db.execute(select(Department))).scalars().all()
            for d in all_deps:
                dept_map[d.code] = d

        # 2. SLA Configs
        print("Checking SLA configs...")
        existing_sla = await db.execute(select(SLAConfig))
        if not existing_sla.scalars().first():
            print("Seeding SLA configurations...")
            categories = [c.value for c in ComplaintCategory]
            sla_rules = [
                ("POTHOLE", 1, 48, 336),
                ("POTHOLE", 2, 48, 336),
                ("POTHOLE", 3, 24, 168),
                ("POTHOLE", 4, 24, 168),
                ("POTHOLE", 5, 12, 72),
                ("WATER_SUPPLY", 1, 24, 168),
                ("WATER_SUPPLY", 2, 24, 168),
                ("WATER_SUPPLY", 3, 6, 48),
                ("WATER_SUPPLY", 4, 6, 48),
                ("WATER_SUPPLY", 5, 4, 24),
                ("GARBAGE", 1, 24, 72),
                ("GARBAGE", 2, 24, 72),
                ("GARBAGE", 3, 24, 72),
                ("GARBAGE", 4, 12, 48),
                ("GARBAGE", 5, 6, 24),
                ("ELECTRICITY", 1, 12, 48),
                ("ELECTRICITY", 2, 12, 48),
                ("ELECTRICITY", 3, 8, 24),
                ("ELECTRICITY", 4, 4, 12),
                ("ELECTRICITY", 5, 2, 6),
            ]
            for cat, sev, ack, res in sla_rules:
                sla = SLAConfig(
                    id=uuid.uuid4(),
                    category=cat,
                    severity=sev,
                    max_acknowledgement_hours=ack,
                    max_resolution_hours=res,
                    escalation_levels=ESCALATION_LEVELS,
                    is_active=True,
                )
                db.add(sla)

            # Fallbacks for all other combinations
            for cat in categories:
                for sev in range(1, 6):
                    existing = [r for r in sla_rules if r[0] == cat and r[1] == sev]
                    if not existing:
                        db.add(
                            SLAConfig(
                                id=uuid.uuid4(),
                                category=cat,
                                severity=sev,
                                max_acknowledgement_hours=24,
                                max_resolution_hours=120,
                                escalation_levels=ESCALATION_LEVELS,
                                is_active=True,
                            )
                        )
            await db.commit()
            print("SLA configs seeded successfully.")

        # 3. Seed Clusters & Realistic Complaints
        print("Checking existing complaints...")
        existing_comp = await db.execute(select(Complaint))
        if not existing_comp.scalars().first():
            print("Seeding 50 realistic complaints across India...")
            now = datetime.now(timezone.utc)

            # Cluster 1: Bangalore Koramangala Potholes
            cluster_kora = ComplaintCluster(
                id=uuid.uuid4(),
                category="POTHOLE",
                centroid_lat=12.9346,
                centroid_lon=77.6266,
                complaint_count=6,
                avg_severity=4.2,
                status=ClusterStatus.ACTIVE.value,
            )
            db.add(cluster_kora)

            # Cluster 2: Delhi Dwarka Water Shortage
            cluster_dwarka = ComplaintCluster(
                id=uuid.uuid4(),
                category="WATER_SUPPLY",
                centroid_lat=28.5922,
                centroid_lon=77.0461,
                complaint_count=4,
                avg_severity=4.5,
                status=ClusterStatus.ACTIVE.value,
            )
            db.add(cluster_dwarka)

            # Cluster 3: Mumbai Andheri Garbage Accumulation
            cluster_andheri = ComplaintCluster(
                id=uuid.uuid4(),
                category="GARBAGE",
                centroid_lat=19.1197,
                centroid_lon=72.8464,
                complaint_count=3,
                avg_severity=3.7,
                status=ClusterStatus.ACTIVE.value,
            )
            db.add(cluster_andheri)
            await db.flush()

            # Predefined complaints
            bbmp_dept = dept_map.get("BBMP") or dept_map.get("PWD")
            djb_dept = dept_map.get("DJB") or dept_map.get("BWSSB")
            bmc_dept = dept_map.get("BMC") or dept_map.get("SWM")
            bescom_dept = dept_map.get("BESCOM")
            traffic_dept = dept_map.get("TRAFFIC_POLICE")
            spcb_dept = dept_map.get("SPCB")
            gen_dept = dept_map.get("GENERAL")

            seed_complaints = [
                # Koramangala Pothole Cluster (Bangalore)
                (
                    "Deep dangerous pothole on 80 Feet Road Koramangala",
                    "A massive crater near Sony World Signal is causing frequent vehicle damage and skidding.",
                    "POTHOLE", 4, 75.0, "HIGH", "IN_PROGRESS", bbmp_dept, 12.9345, 77.6265, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),
                (
                    "Car axle damaged in Koramangala pothole",
                    "My car broke its suspension due to this unlit deep crater on 80ft road.",
                    "POTHOLE", 4, 70.0, "HIGH", "ACKNOWLEDGED", bbmp_dept, 12.9348, 77.6268, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),
                (
                    "Biker injured due to road cave-in",
                    "Biker fell on 80ft road Sony World junction. Urgent patching required before a fatal accident.",
                    "POTHOLE", 5, 90.0, "CRITICAL", "IN_PROGRESS", bbmp_dept, 12.9346, 77.6264, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),
                (
                    "Sadak me bahut bada gadda hai Sony World ke paas",
                    "Koramangala 4th block me gadda hai, traffic jam ho raha hai.",
                    "POTHOLE", 3, 50.0, "MEDIUM", "SUBMITTED", bbmp_dept, 12.9344, 77.6266, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),
                (
                    "Pothole repaired poorly, washed away in rain",
                    "Asphalt filled yesterday washed away in morning drizzle. Poor quality work.",
                    "POTHOLE", 4, 65.0, "HIGH", "REOPENED", bbmp_dept, 12.9350, 77.6270, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),
                (
                    "Road caving in near drainage line",
                    "The side of 80ft road is sinking into the drain below. Very hazardous.",
                    "POTHOLE", 5, 85.0, "CRITICAL", "ASSIGNED", bbmp_dept, 12.9342, 77.6265, "Koramangala", "Bengaluru Urban", "Karnataka", cluster_kora.id
                ),

                # Dwarka Water Supply Cluster (Delhi)
                (
                    "No drinking water supply since 4 days in Sector 12 Dwarka",
                    "Completely dry taps in Sector 12 pocket 4. Tankers are charging exorbitant amounts.",
                    "WATER_SUPPLY", 5, 95.0, "CRITICAL", "IN_PROGRESS", djb_dept, 28.5921, 77.0460, "Dwarka", "South West Delhi", "Delhi", cluster_dwarka.id
                ),
                (
                    "Water pipeline burst near Sector 12 DDA market",
                    "Fresh water gushing onto the street while homes receive zero supply.",
                    "WATER_SUPPLY", 4, 75.0, "HIGH", "ASSIGNED", djb_dept, 28.5923, 77.0458, "Dwarka", "South West Delhi", "Delhi", cluster_dwarka.id
                ),
                (
                    "Muddy brown water coming from taps",
                    "Sewage water seems to be leaking into the main drinking pipeline in Sector 12.",
                    "WATER_SUPPLY", 5, 90.0, "CRITICAL", "ASSIGNED", djb_dept, 28.5920, 77.0462, "Dwarka", "South West Delhi", "Delhi", cluster_dwarka.id
                ),
                (
                    "Low pressure water supply not reaching 2nd floor",
                    "Water pressure barely reaches the ground floor sump in Dwarka Sec 12.",
                    "WATER_SUPPLY", 3, 50.0, "MEDIUM", "SUBMITTED", djb_dept, 28.5925, 77.0465, "Dwarka", "South West Delhi", "Delhi", cluster_dwarka.id
                ),

                # Andheri Garbage Cluster (Mumbai)
                (
                    "Overflowing garbage heap outside Andheri Station East",
                    "Massive mountain of rotting garbage blocking pedestrian walkway outside platform 1.",
                    "GARBAGE", 4, 65.0, "HIGH", "IN_PROGRESS", bmc_dept, 19.1197, 72.8464, "Andheri East", "Mumbai Suburban", "Maharashtra", cluster_andheri.id
                ),
                (
                    "Stray animals scattering open garbage on Station Road",
                    "Cows and dogs ripping open plastic bags across the road. Stench unbearable.",
                    "GARBAGE", 3, 55.0, "MEDIUM", "ASSIGNED", bmc_dept, 19.1195, 72.8466, "Andheri East", "Mumbai Suburban", "Maharashtra", cluster_andheri.id
                ),
                (
                    "Commercial waste dumped illegally at night",
                    "Restaurants dumping rotting food waste in open vacant spot near station.",
                    "GARBAGE", 4, 70.0, "HIGH", "RESOLUTION_CLAIMED", bmc_dept, 19.1199, 72.8462, "Andheri East", "Mumbai Suburban", "Maharashtra", cluster_andheri.id
                ),
            ]

            # Additional 37 complaints across different categories and cities
            other_complaints_data = [
                ("Streetlights flickering in Indiranagar 100ft road", "STREETLIGHT", 2, "LOW", "RESOLVED", bescom_dept, 12.9784, 77.6408, "Indiranagar", "Bengaluru", "Karnataka"),
                ("High voltage fluctuation burned home inverter", "ELECTRICITY", 4, "HIGH", "IN_PROGRESS", bescom_dept, 12.9800, 77.6420, "Indiranagar", "Bengaluru", "Karnataka"),
                ("Traffic signal malfunctioning at Silk Board Junction", "TRAFFIC", 5, "CRITICAL", "ASSIGNED", traffic_dept, 12.9177, 77.6238, "BTM Layout", "Bengaluru", "Karnataka"),
                ("Sewage water overflowing into basements in Bellandur", "DRAINAGE", 4, "HIGH", "IN_PROGRESS", bbmp_dept, 12.9304, 77.6784, "Bellandur", "Bengaluru", "Karnataka"),
                ("Loud loudspeaker music post midnight from banquet hall", "NOISE", 2, "LOW", "CLOSED", spcb_dept, 12.9698, 77.7500, "Whitefield", "Bengaluru", "Karnataka"),
                ("Open toxic burning of rubber and waste in industrial area", "POLLUTION", 4, "HIGH", "ASSIGNED", spcb_dept, 12.9912, 77.7025, "Mahadevapura", "Bengaluru", "Karnataka"),
                ("Footpath illegally encroached by vegetable stalls", "ENCROACHMENT", 3, "MEDIUM", "SUBMITTED", bbmp_dept, 12.9250, 77.5938, "Jayanagar", "Bengaluru", "Karnataka"),
                ("Public bus AC not working and doors jammed", "PUBLIC_TRANSPORT", 2, "LOW", "CLOSED", dept_map.get("BMTC"), 12.9767, 77.5713, "Majestic", "Bengaluru", "Karnataka"),
                ("Public toilet at bus stand locked and unusable", "SANITATION", 3, "MEDIUM", "ACKNOWLEDGED", bbmp_dept, 12.9770, 77.5720, "Majestic", "Bengaluru", "Karnataka"),
                ("Stray dog pack biting morning walkers in park", "OTHER", 3, "MEDIUM", "ASSIGNED", bbmp_dept, 12.9352, 77.5840, "Lalbagh", "Bengaluru", "Karnataka"),
                # Delhi Complaints
                ("Air pollution severe smog near Anand Vihar ISBT", "POLLUTION", 5, "CRITICAL", "IN_PROGRESS", spcb_dept, 28.6469, 77.3160, "Anand Vihar", "East Delhi", "Delhi"),
                ("DTC bus broke down in middle of ITO junction causing jam", "TRAFFIC", 4, "HIGH", "CLOSED", traffic_dept, 28.6300, 77.2400, "ITO", "Central Delhi", "Delhi"),
                ("No street lighting along Ring Road stretch", "STREETLIGHT", 3, "MEDIUM", "ASSIGNED", dept_map.get("MCD"), 28.5672, 77.2100, "Lajpat Nagar", "South Delhi", "Delhi"),
                ("Open drain emitting unbearable stench near government school", "DRAINAGE", 4, "HIGH", "IN_PROGRESS", djb_dept, 28.7000, 77.1400, "Rohini", "North West Delhi", "Delhi"),
                ("Illegal parking mafia occupying public service lane", "ENCROACHMENT", 3, "MEDIUM", "SUBMITTED", dept_map.get("MCD"), 28.6500, 77.2300, "Chandni Chowk", "North Delhi", "Delhi"),
                # Mumbai Complaints
                ("Flooding on Western Express Highway during rain", "DRAINAGE", 4, "HIGH", "ASSIGNED", bmc_dept, 19.0600, 72.8500, "Bandra", "Mumbai", "Maharashtra"),
                ("Pothole on Dadar TT flyover causing traffic bottleneck", "POTHOLE", 4, "HIGH", "IN_PROGRESS", bmc_dept, 19.0178, 72.8478, "Dadar", "Mumbai", "Maharashtra"),
                ("Marine Drive promenade lighting fixtures vandalized", "STREETLIGHT", 2, "LOW", "CLOSED", bmc_dept, 18.9438, 72.8231, "Marine Drive", "South Mumbai", "Maharashtra"),
                ("Construction dust blowing without green screen protection", "POLLUTION", 3, "MEDIUM", "ACKNOWLEDGED", spcb_dept, 19.0700, 72.8800, "BKC", "Mumbai", "Maharashtra"),
                ("BEST bus skipping bus stop regularly during rush hour", "PUBLIC_TRANSPORT", 2, "LOW", "RESOLVED", bmc_dept, 19.1300, 72.8300, "Juhu", "Mumbai", "Maharashtra"),
                # Chennai Complaints
                ("Water logging in T Nagar during moderate shower", "DRAINAGE", 4, "HIGH", "ASSIGNED", dept_map.get("GCC"), 13.0418, 80.2341, "T Nagar", "Chennai", "Tamil Nadu"),
                ("Garbage bins not emptied in Mylapore for 3 days", "GARBAGE", 3, "MEDIUM", "SUBMITTED", dept_map.get("GCC"), 13.0368, 80.2676, "Mylapore", "Chennai", "Tamil Nadu"),
                ("Streetlights unlit on Marina Beach service road", "STREETLIGHT", 2, "LOW", "RESOLVED", dept_map.get("GCC"), 13.0500, 80.2824, "Marina Beach", "Chennai", "Tamil Nadu"),
                ("Power cut for 6 hours in Velachery without notice", "ELECTRICITY", 3, "MEDIUM", "CLOSED", gen_dept, 12.9800, 80.2200, "Velachery", "Chennai", "Tamil Nadu"),
                ("Buses overcrowded and conductors overcharging", "PUBLIC_TRANSPORT", 2, "LOW", "SUBMITTED", gen_dept, 13.0800, 80.2700, "Central", "Chennai", "Tamil Nadu"),
                # Kolkata Complaints
                ("Open manhole on Park Street sidewalk", "DRAINAGE", 5, "CRITICAL", "IN_PROGRESS", dept_map.get("KMC"), 22.5500, 88.3500, "Park Street", "Kolkata", "West Bengal"),
                ("Garbage dumping along Hooghly river bank", "GARBAGE", 4, "HIGH", "ASSIGNED", dept_map.get("KMC"), 22.5700, 88.3400, "Howrah Ghat", "Kolkata", "West Bengal"),
                ("Tram tracks loose creating bicycle hazard", "POTHOLE", 3, "MEDIUM", "ACKNOWLEDGED", dept_map.get("KMC"), 22.5350, 88.3650, "Gariahat", "Kolkata", "West Bengal"),
                ("Streetlights dark on Ballygunge circular road", "STREETLIGHT", 2, "LOW", "RESOLVED", dept_map.get("KMC"), 22.5280, 88.3600, "Ballygunge", "Kolkata", "West Bengal"),
                ("Defective water meter showing 10x consumption", "WATER_SUPPLY", 2, "LOW", "CLOSED", dept_map.get("KMC"), 22.5800, 88.3700, "Salt Lake", "Kolkata", "West Bengal"),
                # More pan-India
                ("Illegal hoarding blocking traffic signal visibility", "ENCROACHMENT", 3, "MEDIUM", "ASSIGNED", bbmp_dept, 12.9300, 77.6100, "Koramangala", "Bengaluru", "Karnataka"),
                ("Loud drilling noise on Sunday afternoon", "NOISE", 1, "LOW", "CLOSED", gen_dept, 12.9400, 77.6200, "Koramangala", "Bengaluru", "Karnataka"),
                ("Open electrical transformer box sparking during rains", "ELECTRICITY", 5, "CRITICAL", "ASSIGNED", bescom_dept, 12.9350, 77.6250, "Koramangala", "Bengaluru", "Karnataka"),
                ("Drunk driver damaged road divider and ran away", "TRAFFIC", 3, "MEDIUM", "CLOSED", traffic_dept, 12.9360, 77.6270, "Koramangala", "Bengaluru", "Karnataka"),
                ("Community dustbin broken, garbage spilling on road", "GARBAGE", 2, "LOW", "RESOLVED", bbmp_dept, 12.9370, 77.6280, "Koramangala", "Bengaluru", "Karnataka"),
                ("Footpath tiles broken causing trip hazards for seniors", "POTHOLE", 2, "LOW", "SUBMITTED", bbmp_dept, 12.9380, 77.6290, "Koramangala", "Bengaluru", "Karnataka"),
                ("Foul smell from stormwater drain", "DRAINAGE", 3, "MEDIUM", "ACKNOWLEDGED", bbmp_dept, 12.9390, 77.6300, "Koramangala", "Bengaluru", "Karnataka"),
            ]

            all_to_insert = []
            # Add predefined cluster complaints
            for item in seed_complaints:
                title, desc_t, cat, sev, p_score, tier, st, d_obj, lat, lon, ward, dist, state, cid = item
                days_back = int(sev) * 2
                created = now - timedelta(days=days_back)
                c = Complaint(
                    id=uuid.uuid4(),
                    citizen_id=f"cit_{uuid.uuid4().hex[:8]}",
                    title=title,
                    description=desc_t,
                    raw_input=desc_t,
                    category=cat,
                    severity=sev,
                    priority_score=p_score,
                    priority_tier=tier,
                    status=st,
                    department_id=d_obj.id if d_obj else None,
                    latitude=lat,
                    longitude=lon,
                    ward=ward,
                    district=dist,
                    state=state,
                    cluster_id=cid,
                    escalation_level=1 if tier == "CRITICAL" else 0,
                    created_at=created,
                    sla_deadline=created + timedelta(hours=72),
                )
                all_to_insert.append(c)

            # Add remaining complaints
            for idx, item in enumerate(other_complaints_data):
                title, cat, sev, tier, st, d_obj, lat, lon, ward, dist, state = item
                p_score = sev * 15.0 + 10.0
                created = now - timedelta(days=idx % 20 + 1)
                c = Complaint(
                    id=uuid.uuid4(),
                    citizen_id=f"cit_{uuid.uuid4().hex[:8]}",
                    title=title,
                    description=f"Citizen reported: {title}. Location near {ward}, {dist}.",
                    raw_input=f"Citizen reported: {title}",
                    category=cat,
                    severity=sev,
                    priority_score=p_score,
                    priority_tier=tier,
                    status=st,
                    department_id=d_obj.id if d_obj else None,
                    latitude=lat,
                    longitude=lon,
                    ward=ward,
                    district=dist,
                    state=state,
                    cluster_id=None,
                    escalation_level=0,
                    created_at=created,
                    sla_deadline=created + timedelta(hours=96),
                )
                all_to_insert.append(c)

            db.add_all(all_to_insert)
            await db.flush()

            # Add events
            for c in all_to_insert:
                e1 = ComplaintEvent(
                    id=uuid.uuid4(),
                    complaint_id=c.id,
                    event_type=EventType.CREATED.value,
                    actor="CITIZEN",
                    details="Complaint registered via Nagrik digital assistant.",
                    created_at=c.created_at,
                )
                db.add(e1)
                if c.status != ComplaintStatus.SUBMITTED.value:
                    e2 = ComplaintEvent(
                        id=uuid.uuid4(),
                        complaint_id=c.id,
                        event_type=c.status,
                        actor="OFFICER",
                        details=f"Status progressed to {c.status}",
                        created_at=c.created_at + timedelta(hours=6),
                    )
                    db.add(e2)

            await db.commit()
            print(f"Successfully seeded {len(all_to_insert)} complaints with clusters and event histories.")


if __name__ == "__main__":
    asyncio.run(seed_data())
