"""Fast hybrid retrieval over local CSV sources.

This module builds a tiny in-memory retrieval index from pandas DataFrames and
returns top-ranked rows using a mix of lexical overlap and TF-IDF cosine
similarity. It is designed to be fast enough for small-to-medium CSV datasets
without adding heavyweight dependencies.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

_WORD_RE = re.compile(r"[a-z0-9]+")

# Basic keyword map to bias retrieval toward the correct CSV for short, explicit queries.
SOURCE_KEYWORDS = {
    'campuses_info': ['campus', 'campus_name', 'address', 'location', 'phone', 'contact', 'phone_number', 'contact_number'],
    'facilities': ['facility', 'facilities', 'library', 'lab', 'transport', 'medical', 'sports', 'parking'],
    'hostal': ['hostel', 'hostal', 'accommodation', 'room', 'wifi', 'internet', 'security'],
    'admission': ['admission', 'apply', 'deadline', 'last_date', 'requirements', 'documents', 'eligibility'],
    'scholarship_policy': ['scholarship', 'grant', 'financial', 'fee waiver', 'merit', 'scholarships'],
    'programs': ['program', 'programs', 'degree', 'bs', 'ms', 'bachelor', 'master', 'major'],
}


@dataclass(frozen=True)
class IndexedDocument:
    source_name: str
    source_label: str
    row_index: int
    text: str
    payload: dict
    tokens: tuple


class LocalHybridRetrievalIndex:
    """Hybrid lexical + semantic retrieval for local CSV rows."""

    def __init__(self, documents: Sequence[IndexedDocument]):
        self.documents = list(documents)
        self._doc_freq = self._build_document_frequencies(self.documents)
        self._doc_weights = [self._build_tfidf_weights(doc.tokens) for doc in self.documents]
        self._doc_norms = [self._vector_norm(weights) for weights in self._doc_weights]
        # Optional vector index will be attached by caller when available
        self._vector_index: Any = None

    @staticmethod
    def _normalize_text(text: object) -> str:
        value = str(text or "").lower()
        value = value.replace("&", " and ")
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    @classmethod
    def _tokenize(cls, text: object) -> tuple:
        normalized = cls._normalize_text(text)
        return tuple(_WORD_RE.findall(normalized))

    @staticmethod
    def _vector_norm(weights: Mapping[str, float]) -> float:
        return math.sqrt(sum(weight * weight for weight in weights.values())) or 1.0

    @staticmethod
    def _build_document_frequencies(documents: Sequence[IndexedDocument]) -> Counter:
        freq = Counter()
        for document in documents:
            freq.update(set(document.tokens))
        return freq

    def _build_tfidf_weights(self, tokens: Sequence[str]) -> dict:
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        weights = {}
        doc_count = max(len(self.documents), 1)
        for token, count in tf.items():
            idf = math.log((1 + doc_count) / (1 + self._doc_freq.get(token, 0))) + 1.0
            weights[token] = (count / total) * idf
        return weights

    def _query_weights(self, query: str) -> dict:
        tokens = self._tokenize(query)
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        weights = {}
        doc_count = max(len(self.documents), 1)
        for token, count in tf.items():
            idf = math.log((1 + doc_count) / (1 + self._doc_freq.get(token, 0))) + 1.0
            weights[token] = (count / total) * idf
        return weights

    @staticmethod
    def _cosine(query_weights: Mapping[str, float], doc_weights: Mapping[str, float], doc_norm: float) -> float:
        if not query_weights or not doc_weights:
            return 0.0
        numerator = 0.0
        for token, q_weight in query_weights.items():
            d_weight = doc_weights.get(token)
            if d_weight:
                numerator += q_weight * d_weight
        query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values())) or 1.0
        return numerator / (query_norm * doc_norm)

    def search(self, query: str, top_k: int = 8, source_name: Optional[str] = None) -> List[dict]:
        """Return the best matching rows for a query."""
        clean_query = self._normalize_text(query)
        if not clean_query:
            return []

        query_weights = self._query_weights(clean_query)
        query_tokens = set(self._tokenize(clean_query))
        scored = []

        # Prepare vector scores if a vector index is attached
        vector_scores_map = {}
        try:
            if getattr(self, '_vector_index', None):
                vec_hits = self._vector_index.search(clean_query, top_k=top_k)
                vector_scores_map = {doc_idx: float(score) for doc_idx, score in vec_hits}
        except Exception:
            vector_scores_map = {}

        # Quick forced routing for high-confidence scholarship queries (avoid noise)
        if 'scholar' in clean_query or 'merit' in clean_query:
            forced = []
            for i, (document, doc_weights, doc_norm) in enumerate(zip(self.documents, self._doc_weights, self._doc_norms)):
                if document.source_name != 'scholarship_policy':
                    continue
                doc_text = document.text.lower()
                doc_tokens = set(document.tokens)
                overlap = len(query_tokens & doc_tokens)
                lexical = (overlap / max(len(query_tokens), 1)) if query_tokens else 0.0
                if clean_query in doc_text:
                    lexical += 0.35
                elif overlap:
                    lexical += min(0.25, overlap * 0.05)
                lexical_weight = 0.45
                semantic = self._cosine(query_weights, doc_weights, doc_norm)
                base_score = (lexical_weight * lexical) + ((1.0 - lexical_weight) * semantic)
                vector_score = max(0.0, vector_scores_map.get(i, 0.0))
                if vector_score:
                    score = (0.4 * base_score) + (0.6 * vector_score)
                else:
                    score = base_score
                if score <= 0:
                    continue
                forced.append({
                    "source_name": document.source_name,
                    "source_label": document.source_label,
                    "row_index": document.row_index,
                    "score": round(score, 6),
                    "text": document.text,
                    "payload": document.payload,
                })
            if forced:
                forced.sort(key=lambda item: (item["score"], len(item["text"])), reverse=True)
                return forced[:top_k]

        # Determine a hinted source from keywords to boost exact-source matches
        hinted_source = None
        for source, keywords in SOURCE_KEYWORDS.items():
            for kw in keywords:
                if kw in clean_query or kw in query_tokens:
                    hinted_source = source
                    break
            if hinted_source:
                break

        # Extra direct fallbacks for common stems / plural forms
        if not hinted_source:
            if 'scholar' in clean_query or 'merit' in clean_query:
                hinted_source = 'scholarship_policy'
            elif 'hostel' in clean_query or 'hostal' in clean_query:
                hinted_source = 'hostal'
            elif 'campus' in clean_query or 'phone' in clean_query or 'address' in clean_query:
                hinted_source = 'campuses_info'
            elif 'program' in clean_query or 'bs ' in clean_query or 'ms ' in clean_query:
                hinted_source = 'programs'
            elif 'admission' in clean_query or 'deadline' in clean_query or 'apply' in clean_query:
                hinted_source = 'admission'

        # Strong hint keywords that should route directly to a single source
        STRONG_HINTS = {'scholarship', 'merit', 'admission', 'deadline', 'hostel', 'hostel', 'campus', 'phone', 'program', 'degree'}
        strong_hint = False
        for kw in STRONG_HINTS:
            if kw in clean_query or kw in query_tokens:
                strong_hint = True
                break

        # If strong hint present and we detected a source, force searching only in that source
        effective_source = source_name
        if strong_hint and hinted_source and not source_name:
            effective_source = hinted_source

        for i, (document, doc_weights, doc_norm) in enumerate(zip(self.documents, self._doc_weights, self._doc_norms)):
            if effective_source and document.source_name != effective_source:
                continue

            doc_text = document.text.lower()
            doc_tokens = set(document.tokens)

            overlap = len(query_tokens & doc_tokens)
            lexical = (overlap / max(len(query_tokens), 1)) if query_tokens else 0.0
            if clean_query in doc_text:
                lexical += 0.35
            elif overlap:
                lexical += min(0.25, overlap * 0.05)

            # Short queries should favor lexical matches (exact/keyword lookup)
            if len(query_tokens) <= 4:
                lexical_weight = 0.65
            else:
                lexical_weight = 0.45

            semantic = self._cosine(query_weights, doc_weights, doc_norm)
            base_score = (lexical_weight * lexical) + ((1.0 - lexical_weight) * semantic)

            # If vector scores available, blend vector similarity with base score
            vector_score = max(0.0, vector_scores_map.get(i, 0.0))
            if vector_score:
                # Favor vector similarity for semantic matching; tuned weights: 60% vector, 40% base
                score = (0.4 * base_score) + (0.6 * vector_score)
            else:
                score = base_score

            # Apply hint boost if a keyword map suggested a source
            if hinted_source and document.source_name == hinted_source:
                score += 0.25

            if score <= 0:
                continue

            scored.append({
                "source_name": document.source_name,
                "source_label": document.source_label,
                "row_index": document.row_index,
                "score": round(score, 6),
                "text": document.text,
                "payload": document.payload,
            })

        scored.sort(key=lambda item: (item["score"], len(item["text"])), reverse=True)
        return scored[:top_k]

    def build_context(self, query: str, top_k: int = 8, max_chars: int = 3500) -> str:
        """Create a compact prompt context from top-ranked documents."""
        hits = self.search(query, top_k=top_k)
        if not hits:
            return ""

        parts = []
        total_chars = 0
        seen = set()

        for hit in hits:
            key = (hit["source_name"], hit["row_index"])
            if key in seen:
                continue
            seen.add(key)

            block = [f"SOURCE: {hit['source_label']}"]
            for line in self._format_payload(hit["payload"]):
                block.append(f"- {line}")
            text = "\n".join(block)
            if total_chars + len(text) > max_chars and parts:
                break
            parts.append(text)
            total_chars += len(text)

        return "\n\n".join(parts)[:max_chars]

    @staticmethod
    def _format_payload(payload: Mapping[str, object]) -> List[str]:
        lines = []
        for key, value in payload.items():
            if value is None:
                continue
            value_text = str(value).strip()
            if not value_text or value_text.lower() == "nan":
                continue
            lines.append(f"{key}: {value_text}")
        return lines


def _row_to_payload(row: pd.Series, preferred_columns: Optional[Iterable[str]] = None) -> dict:
    payload = {}
    preferred = list(preferred_columns or [])
    columns = preferred + [column for column in row.index if column not in preferred]
    for column in columns:
        value = row.get(column)
        if pd.isna(value):
            continue
        value_text = str(value).strip()
        if value_text and value_text.lower() != "nan":
            payload[str(column).strip()] = value_text
    return payload


def _row_to_text(payload: Mapping[str, object]) -> str:
    return " | ".join(f"{key}: {value}" for key, value in payload.items())


def _build_documents_from_dataframe(
    source_name: str,
    source_label: str,
    dataframe: pd.DataFrame,
    preferred_columns: Optional[Iterable[str]] = None,
) -> List[IndexedDocument]:
    documents = []
    if dataframe is None or dataframe.empty:
        return documents

    for row_index, (_, row) in enumerate(dataframe.iterrows()):
        payload = _row_to_payload(row, preferred_columns=preferred_columns)
        if not payload:
            continue
        text = _row_to_text(payload)
        tokens = LocalHybridRetrievalIndex._tokenize(text)
        documents.append(
            IndexedDocument(
                source_name=source_name,
                source_label=source_label,
                row_index=row_index,
                text=text,
                payload=payload,
                tokens=tokens,
            )
        )
    return documents


def build_local_hybrid_index(source_specs: Sequence[Mapping[str, object]]) -> LocalHybridRetrievalIndex:
    """Build an index directly from live DataFrames."""
    documents: List[IndexedDocument] = []
    for spec in source_specs:
        source_name = str(spec.get("source_name", "unknown_source"))
        source_label = str(spec.get("source_label", source_name))
        dataframe = spec.get("dataframe")
        preferred_columns = spec.get("preferred_columns")
        documents.extend(
            _build_documents_from_dataframe(
                source_name=source_name,
                source_label=source_label,
                dataframe=dataframe,
                preferred_columns=preferred_columns,
            )
        )
    return LocalHybridRetrievalIndex(documents)
