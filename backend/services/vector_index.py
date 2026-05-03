"""Simple FAISS-backed vector index using sentence-transformers.

This module provides a small wrapper to build an in-memory FAISS index
for cosine similarity using normalized embeddings from SentenceTransformer.
If dependencies are missing, the module raises an informative error.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Sequence, Tuple

# Defer heavy imports (sentence_transformers, faiss, numpy, sklearn) until needed
SentenceTransformer = None
faiss = None
np = None
TfidfVectorizer = None


class VectorIndex:
    """Builds a FAISS index from a list of texts and allows querying.

    Usage:
        index = VectorIndex(texts, model_name='all-MiniLM-L6-v2')
        hits = index.search('my query', top_k=5)  # returns list of (doc_idx, score)
    """

    def __init__(self, texts: Sequence[str], model_name: str = 'all-MiniLM-L6-v2', cache_path: str | None = None):
        """Create a vector index. Prefer SentenceTransformer+FAISS; fall back to TF-IDF if model downloads fail.

        The fallback uses `sklearn`'s `TfidfVectorizer` to create dense vectors and compute cosine similarity.
        """
        self._mode = None

        if cache_path:
            loaded = self.load_cache(cache_path)
            if loaded is not None:
                self.__dict__.update(loaded.__dict__)
                return

        # Try sentence-transformers + faiss when available (lazy import)
        try:
            from sentence_transformers import SentenceTransformer as _SentenceTransformer
            import faiss as _faiss
            import numpy as _np
            # attempt to instantiate model and build FAISS index
            model = _SentenceTransformer(model_name)
            embeddings = model.encode(list(texts), convert_to_numpy=True)
            norms = _np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
            embeddings = embeddings / norms
            dim = embeddings.shape[1]
            index = _faiss.IndexFlatIP(dim)
            index.add(embeddings.astype('float32'))
            self.index = index
            self._mode = 'faiss'
            self._model = model
            self._np = _np
            self._n = embeddings.shape[0]
            return
        except Exception:
            # Fall back to TF-IDF approach below
            pass

        # Fallback: TF-IDF vectorizer (lazy import)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer as _TfidfVectorizer
            import numpy as _np
        except Exception:
            raise RuntimeError('Missing vector dependencies. Install sentence-transformers/faiss-cpu or scikit-learn and numpy.')

        # Use word n-grams to improve recall on short queries
        self._vectorizer = _TfidfVectorizer(ngram_range=(1, 2), max_features=8192, analyzer='word')
        X = self._vectorizer.fit_transform(list(texts))
        # Convert to dense normalized numpy array for fast dot products
        X = X.astype('float32')
        X = X.toarray()
        norms = _np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        X = X / norms
        self._tfidf_matrix = X
        self._mode = 'tfidf'
        self._np = _np
        self._n = X.shape[0]

        if cache_path:
            try:
                self.save_cache(cache_path)
            except Exception:
                pass

    def save_cache(self, cache_path: str) -> None:
        path = Path(cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            '_mode': self._mode,
            '_n': getattr(self, '_n', 0),
            '_tfidf_matrix': getattr(self, '_tfidf_matrix', None),
            '_vectorizer': getattr(self, '_vectorizer', None),
        }
        with path.open('wb') as handle:
            pickle.dump(payload, handle)

    @classmethod
    def load_cache(cls, cache_path: str):
        path = Path(cache_path)
        if not path.exists():
            return None
        try:
            with path.open('rb') as handle:
                payload = pickle.load(handle)
            instance = cls.__new__(cls)
            instance.__dict__.update(payload)
            return instance
        except Exception:
            return None

    def search(self, query: str, top_k: int = 8) -> List[Tuple[int, float]]:
        if not query:
            return []

        results = []
        if self._mode == 'faiss':
            q_emb = self._model.encode([query], convert_to_numpy=True)
            q_emb = q_emb / (self._np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-12)
            D, I = self.index.search(q_emb.astype('float32'), top_k)
            for idx, score in zip(I[0].tolist(), D[0].tolist()):
                if idx < 0:
                    continue
                results.append((int(idx), float(score)))
            return results

        if self._mode == 'tfidf':
            q_vec = self._vectorizer.transform([query]).astype('float32')
            q_vec = q_vec.toarray()
            q_vec = q_vec / (self._np.linalg.norm(q_vec, axis=1, keepdims=True) + 1e-12)
            sims = (self._tfidf_matrix @ q_vec.T).flatten().tolist()
            # Get top_k indices sorted by similarity
            idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]
            for i in idxs:
                results.append((int(i), float(sims[i])))
            return results

        return []
