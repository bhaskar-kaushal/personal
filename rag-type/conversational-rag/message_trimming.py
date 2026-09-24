"""
Smart message trimming for conversational RAG.

Keeps the most recent messages within a token budget while optionally
prepending a one-sentence summary of older messages so context is preserved.

Public API (required by tests):
    get_encoding() -> tiktoken.Encoding
    count_tokens(messages: list[dict]) -> int
    trim_messages(messages, max_history_length=10) -> tuple[list[dict], int]

Example usage:
    python message_trimming.py --test
"""

from __future__ import annotations

import argparse
from typing import List, Dict, Tuple

try:
    import tiktoken

    def get_encoding():
        """Return a tiktoken encoding (cl100k_base, compatible with GPT-4)."""
        return tiktoken.get_encoding("cl100k_base")

except ImportError:
    # Lightweight fallback: split on whitespace
    class _FallbackEncoding:
        def encode(self, text: str) -> list:
            return text.split()

    def get_encoding():  # type: ignore
        return _FallbackEncoding()


def count_tokens(messages: List[Dict[str, str]]) -> int:
    """
    Estimate total token count for a list of chat messages.

    Args:
        messages: List of {'role': ..., 'content': ...} dicts

    Returns:
        int: Estimated token count
    """
    if not messages:
        return 0
    enc = get_encoding()
    total = 0
    for msg in messages:
        # ~4 overhead tokens per message (role, separators)
        total += 4
        total += len(enc.encode(msg.get("content", "")))
    total += 2  # reply priming
    return total


def _summarise_messages(messages: List[Dict[str, str]]) -> str:
    """
    Create a brief plain-text summary of trimmed messages.
    No LLM call — keeps it dependency-free and instant.
    """
    lines = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        # Take first 80 chars of each turn
        snippet = content[:80].replace("\n", " ")
        if len(content) > 80:
            snippet += "…"
        lines.append(f"{role}: {snippet}")
    return "Earlier in our conversation — " + " | ".join(lines)


def trim_messages(
    messages: List[Dict[str, str]],
    max_history_length: int = 10,
    max_tokens: int = 3000,
) -> Tuple[List[Dict[str, str]], int]:
    """
    Trim a message list so it fits within max_history_length pairs
    and max_tokens.

    Strategy:
      1. Keep the last `max_history_length` message pairs (user+assistant).
      2. If remaining tokens still exceed max_tokens, drop oldest pairs one
         at a time until within budget.
      3. Prepend a brief summary of dropped messages as a system message.

    Args:
        messages: Full conversation history
        max_history_length: Max number of message pairs to keep (default 10)
        max_tokens: Soft token ceiling (default 3000)

    Returns:
        (trimmed_messages, total_token_count)
    """
    if not messages:
        return [], 0

    dropped = []

    # Step 1: enforce max_history_length (in pairs)
    max_msgs = max_history_length * 2
    if len(messages) > max_msgs:
        dropped = messages[:-max_msgs]
        messages = messages[-max_msgs:]

    # Step 2: enforce token limit
    while len(messages) > 2 and count_tokens(messages) > max_tokens:
        # Drop oldest pair
        dropped.extend(messages[:2])
        messages = messages[2:]

    # Step 3: prepend summary if anything was dropped
    if dropped:
        summary_text = _summarise_messages(dropped)
        summary_msg = {"role": "system", "content": summary_text}
        messages = [summary_msg] + list(messages)

    total = count_tokens(messages)
    return list(messages), total


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run built-in demo")
    args = parser.parse_args()

    if args.test:
        print("=== Message Trimming Demo ===\n")

        # Build a long history
        history = []
        for i in range(15):
            history.append({"role": "user", "content": f"Question number {i} about RAG systems."})
            history.append({"role": "assistant", "content": f"Answer {i}: RAG stands for retrieval-augmented generation and is widely used in enterprise AI."})

        print(f"Original messages : {len(history)}")
        print(f"Original tokens   : {count_tokens(history)}")

        trimmed, tokens = trim_messages(history, max_history_length=3)
        print(f"\nAfter trim (max_history=3):")
        print(f"  Messages: {len(trimmed)}")
        print(f"  Tokens  : {tokens}")
        for msg in trimmed:
            role = msg["role"]
            snippet = msg["content"][:60].replace("\n", " ")
            print(f"  [{role}] {snippet}…")
