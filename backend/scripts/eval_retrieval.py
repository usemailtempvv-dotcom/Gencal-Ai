"""Benchmark local hybrid retrieval over the university CSV data.

Usage:
    python scripts/eval_retrieval.py

The script reports top-1 source accuracy and average retrieval latency for a
small built-in set of representative questions.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gencall_backend.settings')
django.setup()

from calls.views import _get_local_hybrid_index  # noqa: E402


TEST_CASES = [
    {'query': 'Where is the main campus located?', 'expected_source': 'campuses_info'},
    {'query': 'What phone number can I use to contact the campus?', 'expected_source': 'campuses_info'},
    {'query': 'What library and lab facilities are available?', 'expected_source': 'facilities'},
    {'query': 'Do you provide transport and medical facilities?', 'expected_source': 'facilities'},
    {'query': 'Tell me about hostel wifi and security.', 'expected_source': 'hostal'},
    {'query': 'What accommodation features are in the hostel?', 'expected_source': 'hostal'},
    {'query': 'When is admission last date?', 'expected_source': 'admission'},
    {'query': 'What documents are required for admission?', 'expected_source': 'admission'},
    {'query': 'Which scholarships are available for merit students?', 'expected_source': 'scholarship_policy'},
    {'query': 'Is BS Computer Science offered?', 'expected_source': 'programs'},
]


def main() -> int:
    index = _get_local_hybrid_index()
    if index is None:
        print('Failed to initialize the local hybrid index.')
        return 1

    total_latency = 0.0
    correct_top1 = 0
    total_context_chars = 0

    print('Local Hybrid Retrieval Benchmark')
    print('-' * 40)

    for case in TEST_CASES:
        query = case['query']
        expected_source = case['expected_source']
        started = time.perf_counter()
        hits = index.search(query, top_k=5)
        context = index.build_context(query, top_k=5, max_chars=2000)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        total_latency += elapsed_ms
        total_context_chars += len(context)

        top_source = hits[0]['source_name'] if hits else 'none'
        top_score = hits[0]['score'] if hits else 0.0
        hit_ok = top_source == expected_source
        correct_top1 += 1 if hit_ok else 0

        print(f'Q: {query}')
        print(f'Expected: {expected_source}')
        print(f'Top-1: {top_source} (score={top_score}, {elapsed_ms:.1f} ms)')
        print(f'Context chars: {len(context)}')
        if hits:
            print('Top hits:')
            for hit in hits[:3]:
                print(f"  - {hit['source_name']} | score={hit['score']} | {hit['text'][:160]}")
        print('PASS' if hit_ok else 'FAIL')
        print('-' * 40)

    count = len(TEST_CASES)
    avg_latency = total_latency / count if count else 0.0
    avg_context = total_context_chars / count if count else 0.0
    accuracy = correct_top1 / count if count else 0.0

    print('Summary')
    print(f'Top-1 source accuracy: {accuracy:.2%}')
    print(f'Average retrieval latency: {avg_latency:.1f} ms')
    print(f'Average context size: {avg_context:.0f} chars')

    return 0 if accuracy >= 0.7 else 2


if __name__ == '__main__':
    raise SystemExit(main())
