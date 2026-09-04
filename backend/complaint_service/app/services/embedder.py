import os
import json
import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except Exception as e:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning(f"sentence_transformers not available: {e}")

try:
    import faiss
    HAS_FAISS = True
except Exception as e:
    HAS_FAISS = False
    logger.warning(f"faiss not available: {e}")


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "data/faiss_index.bin", mapping_path: str = "data/faiss_mapping.json") -> None:
        self.vector_dim = 384
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.model = None
        self.index = None
        self.id_mapping: List[str] = []

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                self.vector_dim = self.model.get_sentence_embedding_dimension()
            except Exception as exc:
                logger.warning(f"Failed to load SentenceTransformer model {model_name}: {exc}")

        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(self.vector_dim)
            self.load_index()

    def generate_embedding(self, text: str) -> np.ndarray:
        if self.model is not None:
            emb = self.model.encode([text])[0]
            if HAS_FAISS:
                faiss.normalize_L2(np.array([emb]))
            return np.array(emb, dtype="float32")
        # Deterministic fallback pseudo-embedding
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(self.vector_dim).astype("float32")
        norm = np.linalg.norm(vec)
        return vec / (norm if norm > 0 else 1.0)

    def add_to_index(self, complaint_id: str, text: str) -> None:
        try:
            emb = self.generate_embedding(text)
            if HAS_FAISS and self.index is not None:
                emb_2d = np.array([emb]).astype("float32")
                self.index.add(emb_2d)
            self.id_mapping.append(str(complaint_id))
            self.save_index()
        except Exception as e:
            logger.error(f"Error adding to index: {e}")

    def search_similar(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not HAS_FAISS or self.index is None or self.index.ntotal == 0:
            return []

        try:
            emb = self.generate_embedding(text)
            emb_2d = np.array([emb]).astype("float32")
            distances, indices = self.index.search(emb_2d, min(top_k, self.index.ntotal))

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1 and idx < len(self.id_mapping):
                    results.append((self.id_mapping[idx], float(dist)))
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []

    def save_index(self) -> None:
        if not HAS_FAISS or self.index is None:
            return
        try:
            os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, "w") as f:
                json.dump(self.id_mapping, f)
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def load_index(self) -> None:
        if not HAS_FAISS:
            return
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, "r") as f:
                    self.id_mapping = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}. Starting fresh.")
                self.index = faiss.IndexFlatIP(self.vector_dim)
                self.id_mapping = []
        else:
            self.index = faiss.IndexFlatIP(self.vector_dim)
            self.id_mapping = []
