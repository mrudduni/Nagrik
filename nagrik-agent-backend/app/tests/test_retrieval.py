from app.rag.retriever import tree_rag_search

queries = [
    "PM Vishwakarma",
    "PM Vishwakarma scheme",
    "Atal Amrit Abhiyan Scheme",
]

for query in queries:
    print("\n" + "=" * 70)
    print("QUERY:", query)
    print("=" * 70)

    result = tree_rag_search(query)

    print("FOUND:", result["found"])

    if not result["found"]:
        print(result["message"])
        continue

    for i, chunk in enumerate(result["chunks"], 1):
        print(f"\n--- RESULT {i} ---")
        print("Scheme:", chunk.get("scheme"))
        print("Page:", chunk.get("page"))
        print("Distance:", chunk.get("distance"))
        print("Text:")
        print(chunk["text"][:1000])