"""
Basic RAG system using FAISS or ChromaDB vector stores and EPAM DIAL API.

Pipeline:
  1. Load processed chunks from extract_content.py output
  2. Embed chunks and store in a vector store
  3. Retrieve top-k relevant chunks for a query
  4. Build a prompt with retrieved context
  5. Generate a response via EPAM DIAL API

Example usage:
    python basic_rag.py --query "What is retrieval-augmented generation?"
    python basic_rag.py --query "What is RAG?" --vector-store chromadb
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from utils.dial_client import DIALClient
from langfuse import get_client as get_langfuse_client

langfuse_client = get_langfuse_client()


class BasicRAG:
    def __init__(self, vector_store_type: str = "faiss", content_dir: str = "data/extracted_content"):
        """
        Initialize the RAG system.

        Args:
            vector_store_type (str): 'faiss' or 'chromadb'
            content_dir (str): Directory with extracted content (chunks.json)
        """
        self.vector_store_type = vector_store_type.lower()
        self.content_dir = content_dir
        self.dial_client = DIALClient()
        self.vector_store = None
        self.embeddings = None

        self._init_embeddings()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_embeddings(self):
        """Load a local sentence-transformers embedding model."""
        from langchain_community.embeddings import HuggingFaceEmbeddings

        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        print(f"🔢 Loading embedding model: {model_name}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("✅ Embeddings ready.")

    # ------------------------------------------------------------------
    # Document loading
    # ------------------------------------------------------------------

    def load_documents(self, content_dir: str = None) -> list:
        """
        Load processed documents from a chunks.json file.

        Args:
            content_dir (str): Directory containing chunks.json

        Returns:
            list[Document]: LangChain Document objects

        Raises:
            FileNotFoundError: If chunks.json does not exist
        """
        from langchain_core.documents import Document

        dir_path = content_dir or self.content_dir
        chunks_path = Path(dir_path) / "chunks.json"

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"chunks.json not found in '{dir_path}'. "
                "Run extract_content.py first."
            )

        with open(chunks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            return []

        docs = [
            Document(page_content=item["content"], metadata=item.get("metadata", {}))
            for item in data
            if item.get("content")
        ]
        print(f"📂 Loaded {len(docs)} documents from {chunks_path}")
        return docs

    # ------------------------------------------------------------------
    # Vector store
    # ------------------------------------------------------------------

    def create_vector_store(self, documents: list):
        """
        Embed documents and build the vector store.

        Args:
            documents (list): LangChain Document objects
        """
        if not documents:
            raise ValueError("No documents provided to create_vector_store.")

        if self.vector_store_type == "chromadb":
            self._create_chroma(documents)
        else:
            self._create_faiss(documents)

    def _create_faiss(self, documents: list):
        from langchain_community.vectorstores import FAISS

        print(f"⚙️  Building FAISS index with {len(documents)} documents…")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        print("✅ FAISS index ready.")

    def _create_chroma(self, documents: list):
        from langchain_community.vectorstores import Chroma
        import shutil

        persist_dir = "data/chroma_db"
        # Fresh start each run to avoid ID conflicts
        if Path(persist_dir).exists():
            shutil.rmtree(persist_dir)
        print(f"⚙️  Building ChromaDB collection with {len(documents)} documents…")
        self.vector_store = Chroma.from_documents(
            documents,
            self.embeddings,
            persist_directory=persist_dir,
        )
        print("✅ ChromaDB collection ready.")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve_relevant_docs(self, query: str, k: int = 3) -> list:
        """
        Retrieve the top-k most relevant documents for a query.

        Args:
            query (str): User query
            k (int): Number of documents to retrieve

        Returns:
            list[Document]: Retrieved documents
        """
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialised. Call create_vector_store() first.")

        # Create a Langfuse retriever observation
        retriever_span = langfuse_client.start_observation(
            name="retrieve-documents",
            as_type="retriever",
            input={"query": query, "k": k},
        )

        docs = self.vector_store.similarity_search(query, k=k)

        # Extract doc metadata for output
        retrieved_sources = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "content_preview": doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else "")
            }
            for doc in docs
        ]

        retriever_span.update(output={"documents": retrieved_sources, "count": len(docs)})
        retriever_span.end()

        return docs

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate_response(self, query: str, retrieved_docs: list) -> str:
        """
        Build a RAG prompt and get a response from DIAL API.

        Args:
            query (str): User query
            retrieved_docs (list): Retrieved Document objects

        Returns:
            str: Generated answer
        """
        if not retrieved_docs:
            context = "No relevant context found."
        else:
            context_parts = []
            for i, doc in enumerate(retrieved_docs, 1):
                source = doc.metadata.get("source", "unknown")
                context_parts.append(f"[Chunk {i} | Source: {source}]\n{doc.page_content}")
            context = "\n\n".join(context_parts)

        system_prompt = (
            "You are a helpful assistant that answers questions based strictly on the "
            "provided context. If the context does not contain enough information to "
            "answer the question, say so clearly. Do not fabricate facts."
        )
        user_prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.dial_client.get_completion(messages)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def query(self, user_query: str, k: int = 3) -> str:
        """
        End-to-end RAG pipeline: retrieve → generate.

        Args:
            user_query (str): The user's question
            k (int): Number of chunks to retrieve

        Returns:
            str: Generated answer
        """
        # Create a top-level trace for this RAG query
        trace = langfuse_client.start_as_current_observation(
            as_type="span",
            name="basic-rag-query",
            input={"query": user_query, "k": k},
        )

        print(f"\n🔍 Retrieving top-{k} chunks for: \"{user_query}\"")
        docs = self.retrieve_relevant_docs(user_query, k=k)
        print(f"   Retrieved {len(docs)} chunk(s).")
        answer = self.generate_response(user_query, docs)

        trace.update(output={"answer": answer})
        trace.end()

        return answer

    # ------------------------------------------------------------------
    # Setup shortcut
    # ------------------------------------------------------------------

    def setup(self):
        """Load documents and build vector store in one call."""
        docs = self.load_documents()
        self.create_vector_store(docs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic RAG Question Answering")
    parser.add_argument("--query", required=True, help="Question to ask")
    parser.add_argument(
        "--vector-store",
        default="faiss",
        choices=["faiss", "chromadb"],
        help="Vector store backend",
    )
    parser.add_argument(
        "--content-dir",
        default="data/extracted_content",
        help="Directory with chunks.json",
    )
    args = parser.parse_args()

    rag = BasicRAG(vector_store_type=args.vector_store, content_dir=args.content_dir)

    # Auto-extract if chunks.json missing
    chunks_path = Path(args.content_dir) / "chunks.json"
    if not chunks_path.exists():
        url = os.getenv("TARGET_URL", "https://en.wikipedia.org/wiki/Retrieval-augmented_generation")
        print(f"📥 chunks.json not found — extracting from {url}")
        from extract_content import extract_content_from_url, save_chunks
        chunks = extract_content_from_url(url)
        save_chunks(chunks, args.content_dir)

    rag.setup()
    answer = rag.query(args.query)
    print(f"\n💬 Answer:\n{answer}")
