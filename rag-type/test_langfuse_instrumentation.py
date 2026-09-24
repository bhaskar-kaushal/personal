#!/usr/bin/env python
"""
Simple test script to verify Langfuse instrumentation.

Usage:
    python test_langfuse_instrumentation.py

Note: Requires Langfuse credentials in environment or .env files.
"""

import sys
from pathlib import Path

# Setup paths for imports
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT / "basic-rag"))
sys.path.insert(0, str(_REPO_ROOT / "conversational-rag"))

from dotenv import load_dotenv
load_dotenv()

from basic_rag import BasicRAG
from conversation_history import ConversationalRAG
from langfuse import get_client as get_langfuse_client

langfuse_client = get_langfuse_client()


def test_basic_rag():
    """Test basic RAG instrumentation."""
    print("=" * 60)
    print("Testing Basic RAG Instrumentation")
    print("=" * 60)

    try:
        rag = BasicRAG(vector_store_type="faiss")
        rag.setup()

        # This should create a trace with retriever and generation spans
        answer = rag.query("What is retrieval-augmented generation?", k=2)

        print(f"\n✅ Basic RAG test completed successfully!")
        print(f"Answer: {answer[:200]}...\n")
        return True
    except Exception as e:
        print(f"\n❌ Basic RAG test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_conversational_rag():
    """Test conversational RAG instrumentation."""
    print("=" * 60)
    print("Testing Conversational RAG Instrumentation")
    print("=" * 60)

    try:
        conv_rag = ConversationalRAG(
            session_id="test_session_001",
            vector_store_type="faiss",
        )
        conv_rag.setup()

        # This should create a trace with session_id, retriever, and generation spans
        response = conv_rag.chat("What is RAG?", k=2)

        print(f"\n✅ Conversational RAG test completed successfully!")
        print(f"Response: {response[:200]}...\n")
        return True
    except Exception as e:
        print(f"\n❌ Conversational RAG test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests and flush traces."""
    print("\n" + "=" * 60)
    print("🚀 Langfuse Instrumentation Test")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Basic RAG", test_basic_rag()))
    results.append(("Conversational RAG", test_conversational_rag()))

    # Flush all traces to Langfuse
    print("=" * 60)
    print("Flushing traces to Langfuse...")
    langfuse_client.flush()
    print("✅ Traces flushed!\n")

    # Summary
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! Check Langfuse UI to see your traces.")
        print("Traces URL: https://cloud.langfuse.com (or your self-hosted instance)")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
