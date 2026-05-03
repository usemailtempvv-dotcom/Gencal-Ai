"""Precompute and persist local retrieval vectors for CSV rows.

This builds the same row text set used by the hybrid retriever and writes a
cache file that is loaded on startup to avoid recomputing vectors.

Usage:
    python backend/scripts/build_embeddings.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gencall_backend.settings')
django.setup()

from calls.views import _get_local_hybrid_index, _retrieval_cache_path  # noqa: E402


def main() -> int:
    index = _get_local_hybrid_index()
    if index is None:
        print('Failed to build the local hybrid index.')
        return 1

    vector_index = getattr(index, '_vector_index', None)
    if vector_index is None:
        print('Vector index is not available; nothing to cache.')
        return 2

    try:
        vector_index.save_cache(str(_retrieval_cache_path))
        print(f'Wrote vector cache to {_retrieval_cache_path}')
        print(f'Documents cached: {len(index.documents)}')
        return 0
    except Exception as exc:
        print(f'Failed to write cache: {exc}')
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
