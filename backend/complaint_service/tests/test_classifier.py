import asyncio
from app.services.classifier import ComplaintClassifier


def test_ml_classifier_pothole():
    classifier = ComplaintClassifier()
    result = classifier._classify_with_ml("There is a massive pothole in the road near the market")
    assert result.category == "POTHOLE"
    assert result.severity in [2, 3, 4, 5]


def test_ml_classifier_water_supply():
    classifier = ComplaintClassifier()
    result = classifier._classify_with_ml("No drinking water supply since 3 days in our colony")
    assert result.category == "WATER_SUPPLY"
    assert result.severity >= 3


def test_ml_classifier_garbage():
    classifier = ComplaintClassifier()
    result = classifier._classify_with_ml("Kachra nahi uthaya ja raha hai, dustbin is overflowing")
    assert result.category == "GARBAGE"


def test_severity_keywords():
    classifier = ComplaintClassifier()
    sev_urgent = classifier._get_severity_from_text("Urgent dangerous open flood water", "DRAINAGE")
    assert sev_urgent == 5

    sev_normal = classifier._get_severity_from_text("Streetlight bulb is dim", "STREETLIGHT")
    assert sev_normal in [2, 3]
