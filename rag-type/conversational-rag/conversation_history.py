"""
Conversational RAG system built on top of the Basic RAG from Assignment 1.

Extends BasicRAG with:
  - Full chat history context injected into every retrieval query
  - Smart message trimming to stay within token limits
  - Per-session persistence via ChatHistoryManager

Example usage:
    python conversational_rag.py --session-id mytest
"""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Allow imports from basic-rag sibling directory
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "basic-rag"))

load_dotenv()

from basic_rag import BasicRAG  # noqa: E402 — must come after sys.path update
from chat_history import ChatHistoryManager  # noqa: E402
from message_trimming import trim_messages  # noqa: E402
from utils.dial_client import DIALClient  # noqa: E402
from langfuse import get_client as get_langfuse_client  # noqa: E402

langfuse_client = get_langfuse_client()


class ConversationalRAG:
    """
    Wraps BasicRAG with conversational memory.

    The chat history is injected into the LLM prompt so the model can
    answer follow-up questions in context.  Message trimming keeps token
    usage bounded for long conversations.
    """

    def __init__(
        self,
        session_id: str = "default",
        vector_store_type: str = "faiss",
        embedding_model: str = "all-MiniLM-L6-v2",
        content_dir: str = None,
        max_history_length: int = None,
    ):
        self.session_id = session_id
        self.vector_store_type = vector_store_type
        self.embedding_model = embedding_model

        # Resolve content dir (prefer basic-rag/data if not overridden)
        if content_dir is None:
            content_dir = str(_REPO_ROOT / "basic-rag" / "data" / "extracted_content")
        self.content_dir = content_dir

        self.max_history_length = max_history_length or int(
            os.getenv("MAX_HISTORY_LENGTH", "10")
        )

        # Initialise components
        os.environ["EMBEDDING_MODEL"] = embedding_model
        self.rag = BasicRAG(
            vector_store_type=vector_store_type,
            content_dir=self.content_dir,
        )
        self.history_manager = ChatHistoryManager()
        self.session = self.history_manager.get_or_create_session(session_id)
        self.dial_client = DIALClient()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self, auto_extract_url: str = None):
        """
        Load documents and build the vector store.

        If chunks.json is missing and auto_extract_url is provided,
        content will be extracted automatically.
        """
        chunks_path = Path(self.content_dir) / "chunks.json"
        if not chunks_path.exists():
            url = auto_extract_url or os.getenv(
                "TARGET_URL",
                "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
            )
            print(f"📥 chunks.json not found — extracting from {url}")
            from extract_content import extract_content_from_url, save_chunks
            chunks = extract_content_from_url(url)
            save_chunks(chunks, self.content_dir)

        self.rag.setup()
        print(f"✅ ConversationalRAG ready (session: {self.session_id})")

    # ------------------------------------------------------------------
    # Core chat
    # ------------------------------------------------------------------

    def _build_standalone_query(self, user_message: str) -> str:
        """
        Rewrite the user message as a standalone search query by appending
        a brief digest of recent conversation context.
        """
        llm_msgs = self.session.get_messages_for_llm()
        trimmed, _ = trim_messages(llm_msgs, max_history_length=self.max_history_length)

        if len(trimmed) <= 1:
            return user_message  # No prior context to incorporate

        # Use the last few turns as context hint (no extra LLM call)
        recent = trimmed[-4:] if len(trimmed) >= 4 else trimmed
        context_hint = " ".join(
            m["content"][:60] for m in recent if m.get("role") != "system"
        )
        return f"{user_message} [Context: {context_hint}]"

    def chat(self, user_message: str, k: int = 3) -> str:
        """
        Process a user message and return the assistant's response.

        Args:
            user_message: The user's query or follow-up question
            k: Number of chunks to retrieve

        Returns:
            str: Assistant's response
        """
        if self.rag.vector_store is None:
            return "❌ RAG not set up yet. Call setup() first."

        # Create top-level trace for conversation tracking with session_id
        with langfuse_client.start_as_current_observation(
            as_type="span",
            name="conversational-rag-chat",
            input={"user_message": user_message},
            session_id=self.session_id,
        ) as trace:
            # Record the user turn
            self.session.add_message("user", user_message)

            # Build a context-aware search query
            search_query = self._build_standalone_query(user_message)

            # Retrieve relevant documents (this creates its own retriever span)
            retrieved_docs = self.rag.retrieve_relevant_docs(search_query, k=k)

            # Build context string
            if retrieved_docs:
                ctx_parts = []
                for i, doc in enumerate(retrieved_docs, 1):
                    source = doc.metadata.get("source", "unknown")
                    ctx_parts.append(f"[Chunk {i} | {source}]\n{doc.page_content}")
                context = "\n\n".join(ctx_parts)
            else:
                context = "No relevant context found."

            # Build trimmed history for the prompt
            llm_msgs = self.session.get_messages_for_llm()
            trimmed_history, _ = trim_messages(
                llm_msgs[:-1],  # exclude the current user message (added separately)
                max_history_length=self.max_history_length,
            )

            system_msg = {
                "role": "system",
                "content": (
                    "You are a helpful conversational assistant. "
                    "Answer questions using the provided document context. "
                    "You also have access to prior conversation history to handle follow-up questions. "
                    "If the context doesn't contain an answer, say so clearly. "
                    "Do not fabricate facts."
                ),
            }

            context_msg = {
                "role": "system",
                "content": f"Document context:\n{context}",
            }

            messages = [system_msg] + trimmed_history + [context_msg] + [
                {"role": "user", "content": user_message}
            ]

            # Generate response (this creates its own generation span via DIALClient)
            response = self.dial_client.get_completion(messages)

            # Record assistant turn
            self.session.add_message("assistant", response)

            trace.update(output={"response": response})

        return response

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def reset_session(self):
        """Clear the current session's message history."""
        self.session.clear()
        print(f"🔄 Session '{self.session_id}' cleared.")

    def get_history(self) -> list:
        """Return all messages in the current session."""
        return self.session.messages

    def export_session(self, path: str = None) -> str:
        """Export current session to a JSON file."""
        out = self.session.export_json(path)
        print(f"💾 Session exported: {out}")
        return out


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conversational RAG CLI")
    parser.add_argument("--session-id", default="cli_session", help="Session identifier")
    parser.add_argument(
        "--vector-store", default="faiss", choices=["faiss", "chromadb"]
    )
    args = parser.parse_args()

    conv_rag = ConversationalRAG(
        session_id=args.session_id,
        vector_store_type=args.vector_store,
    )
    conv_rag.setup()

    print("\n💬 Conversational RAG — type 'quit' to exit, 'reset' to clear history\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            conv_rag.reset_session()
            continue

        response = conv_rag.chat(user_input)
        print(f"\nAssistant: {response}\n")
