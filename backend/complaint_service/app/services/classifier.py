"""
Complaint Classifier — Hybrid LLM + ML/Rule-based classification for civic complaints.

Primary: LLM structured-output classification (OpenRouter / Gemini).
Fallback: scikit-learn TF-IDF + MultinomialNB trained on seed data.
Safe Fallback: Keyword-based matching if sklearn C-extensions have issues.
"""
import json
import logging
from typing import Optional

import httpx

from app.schemas.classification import ClassificationResult, ComplaintCategory
from app.config import settings

logger = logging.getLogger(__name__)

# Try importing sklearn safely
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    HAS_SKLEARN = True
except Exception as e:
    HAS_SKLEARN = False
    logger.warning(f"scikit-learn not available or DLL error: {e}. Rule-based fallback will be used.")

# ── Seed training data ───────────────────────────────────────────────────────
SEED_DATA = [
    # POTHOLE
    ("There is a large pothole on the main road", "POTHOLE"),
    ("Road is broken and full of craters near the bridge", "POTHOLE"),
    ("Deep pothole near school, kids falling", "POTHOLE"),
    ("Road surface damaged after monsoon", "POTHOLE"),
    ("Sadak mein gadda hai bahut bada", "POTHOLE"),
    # WATER_SUPPLY
    ("No water supply since morning", "WATER_SUPPLY"),
    ("Water is dirty brown colour", "WATER_SUPPLY"),
    ("Low water pressure in our colony", "WATER_SUPPLY"),
    ("Paani nahi aa raha 3 din se", "WATER_SUPPLY"),
    ("Water pipeline burst near market", "WATER_SUPPLY"),
    # DRAINAGE
    ("Sewage overflowing on the street", "DRAINAGE"),
    ("Blocked drain causing water logging", "DRAINAGE"),
    ("Nala is overflowing into residential area", "DRAINAGE"),
    ("Drain is choked near temple", "DRAINAGE"),
    # GARBAGE
    ("Garbage not collected for a week", "GARBAGE"),
    ("Huge pile of trash near the park entrance", "GARBAGE"),
    ("Kachra nahi uthaya ja raha", "GARBAGE"),
    ("Dustbin overflowing, stray dogs everywhere", "GARBAGE"),
    ("No garbage van coming to our street", "GARBAGE"),
    # STREETLIGHT
    ("Streetlight not working at night", "STREETLIGHT"),
    ("Dark street, all bulbs are broken", "STREETLIGHT"),
    ("Lane is completely dark, unsafe for women", "STREETLIGHT"),
    ("Street light pole fallen on road", "STREETLIGHT"),
    # POLLUTION
    ("Factory releasing toxic smoke daily", "POLLUTION"),
    ("Open burning of garbage in vacant lot", "POLLUTION"),
    ("Air quality very bad in our area", "POLLUTION"),
    ("River near our locality polluted with chemicals", "POLLUTION"),
    # NOISE
    ("Loud music playing late night from bar", "NOISE"),
    ("Construction noise early in the morning 5am", "NOISE"),
    ("Temple loudspeaker too loud at night", "NOISE"),
    # ENCROACHMENT
    ("Illegal construction on government footpath", "ENCROACHMENT"),
    ("Vendors blocking the entire sidewalk", "ENCROACHMENT"),
    ("Someone built boundary wall on public land", "ENCROACHMENT"),
    # TRAFFIC
    ("Heavy traffic jam every evening at junction", "TRAFFIC"),
    ("Traffic signals not working since two days", "TRAFFIC"),
    ("No traffic police at busy crossing", "TRAFFIC"),
    # ELECTRICITY
    ("Power cut since morning in whole area", "ELECTRICITY"),
    ("Frequent electricity fluctuations damaging appliances", "ELECTRICITY"),
    ("Transformer sparking and making loud noise", "ELECTRICITY"),
    ("Electric wire fallen on road very dangerous", "ELECTRICITY"),
    # PUBLIC_TRANSPORT
    ("Bus didn't show up for two hours", "PUBLIC_TRANSPORT"),
    ("Bus stop has no shelter or seating", "PUBLIC_TRANSPORT"),
    ("Auto rickshaw drivers refusing to go by meter", "PUBLIC_TRANSPORT"),
    # SANITATION
    ("Public toilets are extremely dirty", "SANITATION"),
    ("No cleaning of community toilet for weeks", "SANITATION"),
    ("Open defecation happening near school", "SANITATION"),
    # OTHER
    ("Stray dogs attacking people in colony", "OTHER"),
    ("Abandoned car parked for months blocking road", "OTHER"),
    ("Tree about to fall on house", "OTHER"),
]


class ComplaintClassifier:
    """Classifies civic complaints into category, severity, and sub-category."""

    def __init__(self) -> None:
        self.ml_pipeline = self._train_ml_classifier() if HAS_SKLEARN else None

    # ── Public API ────────────────────────────────────────────────────────────
    async def classify(self, text: str) -> ClassificationResult:
        """Classify complaint text. Tries LLM first, falls back to ML / rules."""
        try:
            result = await self._classify_with_llm(text)
            if result.confidence and result.confidence >= 0.5:
                return result
            logger.info("LLM confidence too low, falling back to ML/rules")
        except Exception as exc:
            logger.warning(f"LLM classification failed: {exc}. Falling back to ML/rules.")

        return self._classify_with_ml(text)

    # ── LLM-based classification ──────────────────────────────────────────────
    async def _classify_with_llm(self, text: str) -> ClassificationResult:
        api_key = (
            settings.OPENROUTER_API_KEY
            if settings.LLM_PROVIDER == "openrouter"
            else settings.GEMINI_API_KEY
        )
        if not api_key:
            raise ValueError("No LLM API key configured")

        if settings.LLM_PROVIDER == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        else:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{settings.LLM_MODEL}:generateContent?key={api_key}"
            )
            headers = {"Content-Type": "application/json"}

        categories = ", ".join(c.value for c in ComplaintCategory)
        system_prompt = (
            "You are an expert civic complaint classifier for Indian government services. "
            "Given a citizen complaint, output ONLY valid JSON with these keys:\n"
            f'  "category": one of [{categories}]\n'
            '  "sub_category": a specific sub-category string\n'
            '  "severity": integer 1-5 (1=minor, 5=critical/dangerous)\n'
            '  "confidence": float 0.0-1.0\n'
            '  "keywords": list of key terms\n'
            '  "reasoning": one sentence explaining your choice\n'
        )

        if settings.LLM_PROVIDER == "openrouter":
            payload = {
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'Classify this complaint:\n"{text}"'},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }
        else:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\n\nClassify this complaint:\n\"{text}\""}
                        ]
                    }
                ],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if settings.LLM_PROVIDER == "openrouter":
            content = data["choices"][0]["message"]["content"]
        else:
            content = data["candidates"][0]["content"]["parts"][0]["text"]

        result = json.loads(content)

        return ClassificationResult(
            category=result.get("category", "OTHER"),
            sub_category=result.get("sub_category"),
            severity=max(1, min(5, int(result.get("severity", 3)))),
            confidence=float(result.get("confidence", 0.7)),
            keywords=result.get("keywords", []),
            reasoning=result.get("reasoning"),
        )

    # ── ML-based classification (fallback) ────────────────────────────────────
    def _train_ml_classifier(self):
        try:
            X, y = zip(*SEED_DATA)
            pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
                ("clf", MultinomialNB(alpha=0.1)),
            ])
            pipeline.fit(list(X), list(y))
            return pipeline
        except Exception as e:
            logger.warning(f"Could not initialize sklearn pipeline: {e}")
            return None

    def _classify_with_ml(self, text: str) -> ClassificationResult:
        if self.ml_pipeline is not None:
            try:
                category = self.ml_pipeline.predict([text])[0]
                probas = self.ml_pipeline.predict_proba([text])[0]
                confidence = float(max(probas))
                severity = self._get_severity_from_text(text, category)

                return ClassificationResult(
                    category=category,
                    sub_category="General",
                    severity=severity,
                    confidence=confidence,
                    keywords=[],
                    reasoning="Classified by fallback ML model (TF-IDF + NaiveBayes)",
                )
            except Exception as e:
                logger.warning(f"ML classification failed: {e}. Using rule matching.")

        # Keyword-based fallback
        category = self._classify_by_keywords(text)
        severity = self._get_severity_from_text(text, category)
        return ClassificationResult(
            category=category,
            sub_category="General",
            severity=severity,
            confidence=0.8,
            keywords=[],
            reasoning="Classified by rule-based keyword matching",
        )

    def _classify_by_keywords(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["pothole", "gadda", "road", "crater", "asphalt"]):
            return "POTHOLE"
        if any(w in t for w in ["water", "paani", "tap", "pipeline", "leak"]):
            return "WATER_SUPPLY"
        if any(w in t for w in ["drain", "nala", "sewage", "gutter", "waterlogging"]):
            return "DRAINAGE"
        if any(w in t for w in ["garbage", "kachra", "trash", "dustbin", "waste"]):
            return "GARBAGE"
        if any(w in t for w in ["light", "streetlight", "bulb", "dark", "pole"]):
            return "STREETLIGHT"
        if any(w in t for w in ["smoke", "pollution", "air", "smog", "toxic"]):
            return "POLLUTION"
        if any(w in t for w in ["noise", "loudspeaker", "music", "dj"]):
            return "NOISE"
        if any(w in t for w in ["encroach", "illegal", "footpath", "stall", "hawker"]):
            return "ENCROACHMENT"
        if any(w in t for w in ["traffic", "jam", "signal"]):
            return "TRAFFIC"
        if any(w in t for w in ["power", "electricity", "transformer", "bijli", "voltage"]):
            return "ELECTRICITY"
        if any(w in t for w in ["bus", "bmtc", "dtc", "transport", "auto"]):
            return "PUBLIC_TRANSPORT"
        if any(w in t for w in ["toilet", "sanitation", "cleaning", "washroom"]):
            return "SANITATION"
        return "OTHER"

    @staticmethod
    def _get_severity_from_text(text: str, category: str) -> int:
        t = text.lower()
        if any(w in t for w in ["urgent", "emergency", "fatal", "dangerous", "collapse", "fire", "flood", "electrocution"]):
            return 5
        if any(w in t for w in ["severe", "major", "completely", "blocking", "days", "weeks", "attack", "fallen"]):
            return 4
        if any(w in t for w in ["many", "daily", "frequently", "smells", "unsafe", "broken"]):
            return 3
        if category in ("WATER_SUPPLY", "ELECTRICITY", "DRAINAGE"):
            return 3
        return 2
