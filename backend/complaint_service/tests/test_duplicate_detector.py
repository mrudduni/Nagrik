from unittest.mock import MagicMock
from app.services.duplicate_detector import DuplicateDetector


def test_haversine_distance():
    mock_embedder = MagicMock()
    detector = DuplicateDetector(mock_embedder)

    # Coordinates for Koramangala 4th Block and Sony World Junction (~300 meters)
    lat1, lon1 = 12.9345, 77.6265
    lat2, lon2 = 12.9348, 77.6268

    dist = detector._haversine_distance(lat1, lon1, lat2, lon2)
    assert 0.0 < dist < 0.5  # Should be less than 500 meters

    # Distance between Bangalore and Delhi (~1740 km)
    blr_lat, blr_lon = 12.9716, 77.5946
    del_lat, del_lon = 28.7041, 77.1025
    dist_blr_del = detector._haversine_distance(blr_lat, blr_lon, del_lat, del_lon)
    assert 1700 < dist_blr_del < 1800
