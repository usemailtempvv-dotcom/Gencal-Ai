# Retrieval Benchmark

Run the local hybrid retrieval benchmark from the backend folder:

```powershell
python scripts/eval_retrieval.py
```

What it checks:
- Top-1 source accuracy for representative CSV questions
- Average retrieval latency
- Context size produced by the hybrid retriever

The benchmark uses the existing Django project settings and the local CSV retrievers.