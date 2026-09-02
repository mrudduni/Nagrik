"""
Tree-RAG retrieval tests.
"""

from app.rag.retriever import tree_rag_search


def fake_store_query(
    text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> dict:

    documents = [
        "PM Vishwakarma Scheme provides financial support, "
        "skill training, and toolkit incentives to traditional "
        "artisans and craftspeople.",

        "PM Vishwakarma Scheme eligibility and benefits.",

        "Mukhyamantri Kisaan Kalyaan Yojana provides support "
        "to farmers.",

        "Chocolate cake needs flour, cocoa, and sugar.",
    ]

    metadatas = [
        {
            "ministry": "Ministry of MSME",
            "department": "MSME",
            "scheme": "PM Vishwakarma",
            "source_url": "https://pmvishwakarma.gov.in",
            "source_file": "pm-vishwakarma.pdf",
            "page": 2,
        },
        {
            "ministry": "Ministry of MSME",
            "department": "MSME",
            "scheme": "PM Vishwakarma",
            "source_url": "https://pmvishwakarma.gov.in",
            "source_file": "pm-vishwakarma.pdf",
            "page": 3,
        },
        {
            "ministry": "Government",
            "department": "Agriculture",
            "scheme": "Mukhyamantri Kisaan Kalyaan Yojana",
            "source_url": "",
            "source_file": "kisan.pdf",
            "page": 1,
        },
        {
            "ministry": "",
            "department": "",
            "scheme": "Recipe",
            "source_url": "",
            "source_file": "recipe.pdf",
            "page": 1,
        },
    ]

    distances = [0.6, 0.65, 0.7, 1.4]

    # Simulate Chroma metadata filtering.
    if where and "scheme" in where:
        target = where["scheme"]

        filtered = [
            (doc, meta, distance)
            for doc, meta, distance in zip(
                documents,
                metadatas,
                distances,
            )
            if meta.get("scheme") == target
        ]

        documents = [x[0] for x in filtered]
        metadatas = [x[1] for x in filtered]
        distances = [x[2] for x in filtered]

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def test_exact_scheme_query_returns_only_that_scheme(monkeypatch):

    monkeypatch.setattr(
        "app.rag.retriever.store.query",
        fake_store_query,
    )

    result = tree_rag_search(
        "What is PM Vishwakarma scheme?"
    )

    assert result["found"] is True

    assert len(result["chunks"]) > 0

    assert all(
        c["scheme"] == "PM Vishwakarma"
        for c in result["chunks"]
    )


def test_scheme_benefits_query(monkeypatch):

    monkeypatch.setattr(
        "app.rag.retriever.store.query",
        fake_store_query,
    )

    result = tree_rag_search(
        "What are the benefits of PM Vishwakarma scheme?"
    )

    assert result["found"] is True

    assert all(
        c["scheme"] == "PM Vishwakarma"
        for c in result["chunks"]
    )


def test_general_query_can_return_multiple_schemes(monkeypatch):

    monkeypatch.setattr(
        "app.rag.retriever.store.query",
        fake_store_query,
    )

    result = tree_rag_search(
        "What schemes help farmers?"
    )

    assert result["found"] is True

    assert len(result["chunks"]) > 0


def test_out_of_scope_query_returns_not_found(monkeypatch):

    monkeypatch.setattr(
        "app.rag.retriever.store.query",
        lambda text, n_results=5, where=None: {
            "documents": [[
                "A completely unrelated document about astronomy."
            ]],
            "metadatas": [[
                {
                    "scheme": "Astronomy",
                    "page": 1,
                }
            ]],
            "distances": [[1.5]],
        },
    )

    result = tree_rag_search(
        "What is the recipe for chocolate cake?"
    )

    assert result["found"] is False


def test_hindi_query_does_not_crash(monkeypatch):

    monkeypatch.setattr(
        "app.rag.retriever.store.query",
        fake_store_query,
    )

    result = tree_rag_search(
        "पीएम विश्वकर्मा योजना क्या है?"
    )

    assert isinstance(result, dict)
    assert "found" in result