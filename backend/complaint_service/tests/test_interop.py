from app.schemas.complaint import ComplaintCreate


def test_complaint_create_standard():
    payload = {
        "citizen_id": "cit_123",
        "title": "Broken pipe",
        "description": "Pipe leaking on 4th street",
        "latitude": 12.9345,
        "longitude": 77.6265,
        "ward": "Ward 4",
        "district": "Bengaluru",
        "state": "Karnataka",
        "evidence_urls": ["http://example.com/photo.jpg"],
    }
    c = ComplaintCreate(**payload)
    assert c.citizen_id == "cit_123"
    assert c.description == "Pipe leaking on 4th street"
    assert c.latitude == 12.9345


def test_complaint_create_navya_interop():
    # Payload format sent by Navya's Person3Client:
    # { "citizen_id": citizen_id, "text": text, "location": location, "media_refs": media_refs }
    payload = {
        "citizen_id": "cit_navya_01",
        "text": "Huge pothole on road near Sony World signal",
        "location": {"lat": 12.9348, "lng": 77.6268, "city": "Bangalore"},
        "media_refs": ["https://s3.amazonaws.com/evidence/1.png"],
    }
    c = ComplaintCreate(**payload)
    assert c.citizen_id == "cit_navya_01"
    assert c.text == "Huge pothole on road near Sony World signal"
    assert c.location["lat"] == 12.9348
    assert len(c.media_refs) == 1
