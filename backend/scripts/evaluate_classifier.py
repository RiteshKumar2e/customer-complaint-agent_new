"""
Measure the offline (fallback) classifier on the labelled examples in Training_data/.

    python scripts/evaluate_classifier.py            # offline keyword/TF-IDF analyser only
    python scripts/evaluate_classifier.py --llm      # also the configured LLM pipeline (uses API quota)

Caveat printed with the results: these ~40 examples are small and were written
by the project authors (the keyword lists come from the same files), so the
numbers are an optimistic sanity check, not a benchmark.
"""
import argparse
import asyncio
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "Training_data"))


def dataset():
    from enhanced_training_data import HINGLISH_COMPLAINT_EXAMPLES
    from training_data import COMPLAINT_EXAMPLES

    rows = []
    for category, items in COMPLAINT_EXAMPLES.items():
        rows += [(i["text"], category, i.get("priority"), "english") for i in items]
    for category, items in HINGLISH_COMPLAINT_EXAMPLES.items():
        rows += [(i["complaint"], i.get("category", category), i.get("priority"), "hinglish") for i in items]
    return rows


def report(name, rows, predict):
    cat_ok = pri_ok = pri_n = 0
    confusion = Counter()
    for text, category, priority, _lang in rows:
        pred = predict(text)
        cat_ok += pred["category"] == category
        confusion[(category, pred["category"])] += 1
        if priority in ("High", "Medium", "Low"):
            pri_n += 1
            pri_ok += pred["priority"] == priority
    print(f"\n{name}: {len(rows)} examples")
    print(f"  category accuracy: {cat_ok}/{len(rows)} = {cat_ok / len(rows):.1%}")
    if pri_n:
        print(f"  priority accuracy: {pri_ok}/{pri_n} = {pri_ok / pri_n:.1%}")
    misses = [(t, p, n) for (t, p), n in confusion.items() if t != p]
    if misses:
        print("  misclassifications (true -> predicted: count):")
        for t, p, n in sorted(misses):
            print(f"    {t} -> {p}: {n}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true")
    args = parser.parse_args(argv)
    os.environ.setdefault("TURSO_DATABASE_URL", "file::memory:")
    from app.agents import local_analysis

    rows = dataset()
    report("Offline analyser (keyword + TF-IDF)", rows, lambda t: local_analysis.analyze(t))
    for lang in ("english", "hinglish"):
        subset = [r for r in rows if r[3] == lang]
        report(f"  - {lang} subset", subset, lambda t: local_analysis.analyze(t))
    if args.llm:
        from app.agents.orchestrator import run_agent_pipeline

        report("LLM pipeline", rows, lambda t: asyncio.run(run_agent_pipeline(t)))
    print("\nCaveat: small, author-written examples; treat as a sanity check, not a benchmark.")


if __name__ == "__main__":
    main()
