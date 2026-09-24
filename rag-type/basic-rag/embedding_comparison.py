"""
Compare different sentence-transformer embedding models.

Measures:
  - Embedding speed (docs/sec)
  - Embedding dimension
  - Semantic similarity quality on a small benchmark
  - Memory footprint estimate

Example usage:
    python embedding_comparison.py
"""

import time
from typing import List, Dict, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# Benchmark data
# ---------------------------------------------------------------------------

SIMILAR_PAIRS: List[Tuple[str, str]] = [
    ("How does machine learning work?", "Explain the fundamentals of ML."),
    ("What is natural language processing?", "Define NLP in AI."),
    ("How do neural networks learn?", "What is backpropagation?"),
    ("What is a vector database?", "Explain vector stores for embeddings."),
    ("How does RAG improve LLMs?", "What is retrieval-augmented generation?"),
]

DISSIMILAR_PAIRS: List[Tuple[str, str]] = [
    ("How does machine learning work?", "What is the capital of France?"),
    ("What is natural language processing?", "How do you bake a chocolate cake?"),
    ("How do neural networks learn?", "What are the rules of chess?"),
]

TEST_CORPUS: List[str] = [
    "Retrieval-Augmented Generation combines a retrieval step with language model generation.",
    "Vector databases store high-dimensional embeddings for fast similarity search.",
    "Sentence transformers encode sentences into dense vector representations.",
    "FAISS is a library for efficient similarity search of dense vectors.",
    "ChromaDB is an open-source embedding store optimised for AI applications.",
    "Embeddings capture semantic meaning, so similar texts have similar vectors.",
    "Large language models are pre-trained on huge corpora and fine-tuned for tasks.",
    "The attention mechanism enables transformers to model long-range dependencies.",
]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two 1-D numpy arrays."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class EmbeddingComparison:
    """Compare multiple sentence-transformer embedding models."""

    MODELS = [
        "all-MiniLM-L6-v2",       # Fast, 384-dim, strong baseline
        "all-MiniLM-L12-v2",      # Slightly larger, 384-dim
        "paraphrase-MiniLM-L3-v2", # Smallest / fastest, 384-dim
    ]

    def __init__(self):
        """Initialise storage for loaded models."""
        self._loaded: Dict[str, object] = {}

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_sentence_transformers_model(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Load (and cache) a sentence-transformers model.

        Args:
            model_name (str): HuggingFace model id

        Returns:
            SentenceTransformer: loaded model
        """
        if model_name not in self._loaded:
            from sentence_transformers import SentenceTransformer
            print(f"  📦 Loading {model_name}…", end=" ", flush=True)
            self._loaded[model_name] = SentenceTransformer(model_name)
            print("done")
        return self._loaded[model_name]

    def load_other_embedding_models(self) -> Dict[str, object]:
        """
        Load all comparison models.

        Returns:
            dict: {model_name: SentenceTransformer}
        """
        for name in self.MODELS:
            self.load_sentence_transformers_model(name)
        return self._loaded

    # ------------------------------------------------------------------
    # Speed measurement
    # ------------------------------------------------------------------

    def measure_embedding_speed(self, texts: List[str], model_name: str) -> float:
        """
        Benchmark embedding throughput.

        Args:
            texts (List[str]): Texts to embed
            model_name (str): Model to benchmark

        Returns:
            float: Documents per second
        """
        model = self.load_sentence_transformers_model(model_name)
        # Warm-up
        model.encode(texts[:2], show_progress_bar=False)

        start = time.perf_counter()
        model.encode(texts, show_progress_bar=False)
        elapsed = time.perf_counter() - start

        docs_per_sec = len(texts) / elapsed if elapsed > 0 else float("inf")
        return docs_per_sec

    # ------------------------------------------------------------------
    # Quality evaluation
    # ------------------------------------------------------------------

    def evaluate_embedding_quality(self, model_name: str) -> Dict[str, float]:
        """
        Evaluate semantic similarity quality.

        Scores:
          - avg_similar_sim  : average cosine sim for semantically similar pairs (higher = better)
          - avg_dissimilar_sim: average cosine sim for unrelated pairs (lower = better)
          - separation       : difference between the two (higher = better)

        Args:
            model_name (str): Model to evaluate

        Returns:
            dict: Quality metrics
        """
        model = self.load_sentence_transformers_model(model_name)

        similar_sims = []
        for a, b in SIMILAR_PAIRS:
            ea, eb = model.encode([a, b], show_progress_bar=False)
            similar_sims.append(cosine_similarity(ea, eb))

        dissimilar_sims = []
        for a, b in DISSIMILAR_PAIRS:
            ea, eb = model.encode([a, b], show_progress_bar=False)
            dissimilar_sims.append(cosine_similarity(ea, eb))

        avg_sim = float(np.mean(similar_sims))
        avg_dissim = float(np.mean(dissimilar_sims))
        return {
            "avg_similar_sim": round(avg_sim, 4),
            "avg_dissimilar_sim": round(avg_dissim, 4),
            "separation": round(avg_sim - avg_dissim, 4),
        }

    # ------------------------------------------------------------------
    # Dimension comparison
    # ------------------------------------------------------------------

    def compare_embedding_dimensions(self) -> Dict[str, int]:
        """
        Report embedding dimensionality for each model.

        Returns:
            dict: {model_name: dim}
        """
        dims = {}
        for name in self.MODELS:
            model = self.load_sentence_transformers_model(name)
            vec = model.encode(["test"], show_progress_bar=False)[0]
            dims[name] = len(vec)
        return dims

    # ------------------------------------------------------------------
    # Full report
    # ------------------------------------------------------------------

    def run_comparison(self):
        """Run the complete embedding model comparison and print a report."""
        print("\n" + "=" * 60)
        print("       EMBEDDING MODEL COMPARISON REPORT")
        print("=" * 60)

        print("\n📦 Loading all models…")
        self.load_other_embedding_models()

        # --- Dimensions ---
        print("\n📐 Embedding Dimensions")
        print("-" * 40)
        dims = self.compare_embedding_dimensions()
        for name, dim in dims.items():
            print(f"  {name:<35} {dim} dims")

        # --- Speed ---
        print("\n⚡ Embedding Speed (docs/sec on test corpus)")
        print("-" * 40)
        speeds: Dict[str, float] = {}
        for name in self.MODELS:
            dps = self.measure_embedding_speed(TEST_CORPUS, name)
            speeds[name] = dps
            print(f"  {name:<35} {dps:.1f} docs/sec")

        # --- Quality ---
        print("\n🎯 Semantic Similarity Quality")
        print("-" * 60)
        header = f"  {'Model':<35} {'SimilarSim':>10} {'DissimSim':>10} {'Separation':>11}"
        print(header)
        print("  " + "-" * 56)
        qualities: Dict[str, Dict] = {}
        for name in self.MODELS:
            q = self.evaluate_embedding_quality(name)
            qualities[name] = q
            print(
                f"  {name:<35}"
                f" {q['avg_similar_sim']:>10.4f}"
                f" {q['avg_dissimilar_sim']:>10.4f}"
                f" {q['separation']:>11.4f}"
            )

        # --- Recommendation ---
        print("\n📋 Recommendations")
        print("-" * 60)
        best_quality = max(qualities, key=lambda m: qualities[m]["separation"])
        best_speed = max(speeds, key=lambda m: speeds[m])
        print(f"  🥇 Best semantic quality : {best_quality}")
        print(f"  ⚡ Fastest              : {best_speed}")
        print()
        print("  General guidance:")
        print("  • all-MiniLM-L6-v2  — best balance of quality and speed; ideal default")
        print("  • all-MiniLM-L12-v2 — slightly better quality, ~20% slower; use when")
        print("    retrieval precision matters more than throughput")
        print("  • paraphrase-MiniLM-L3-v2 — smallest model; use for real-time or edge")
        print("    deployments where latency is critical")
        print("=" * 60)


if __name__ == "__main__":
    comparison = EmbeddingComparison()
    comparison.run_comparison()
