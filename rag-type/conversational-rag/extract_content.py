"""
Web content extraction using LangChain WebBaseLoader.

Handles web scraping, text cleaning, chunking with overlap,
and saving processed chunks with metadata.

Example usage:
    python extract_content.py --url https://en.wikipedia.org/wiki/Retrieval-augmented_generation
"""

import os
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.

    Args:
        text (str): Raw text to clean

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    # Collapse whitespace / newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text (str): Text to chunk
        chunk_size (int): Target size of each chunk (characters)
        overlap (int): Number of characters to overlap between chunks

    Returns:
        list: List of text chunk strings
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap  # slide back by overlap

    return chunks


def extract_content_from_url(url: str) -> List[Dict]:
    """
    Extract and chunk content from a URL using LangChain WebBaseLoader.

    Args:
        url (str): Website URL to extract content from

    Returns:
        list: List of dicts with 'content' and 'metadata' keys
    """
    try:
        from langchain_community.document_loaders import WebBaseLoader
    except ImportError:
        from langchain_core.document_loaders import WebBaseLoader

    print(f"🌐 Loading content from: {url}")
    loader = WebBaseLoader(url)
    raw_docs = loader.load()

    all_chunks = []
    for doc_idx, doc in enumerate(raw_docs):
        raw_text = doc.page_content
        cleaned = clean_text(raw_text)
        if not cleaned:
            print(f"  ⚠️  Document {doc_idx} is empty after cleaning, skipping.")
            continue

        chunks = chunk_text(cleaned, chunk_size=1000, overlap=200)
        print(f"  📄 Document {doc_idx}: {len(cleaned)} chars → {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "content": chunk,
                "metadata": {
                    "source": url,
                    "doc_index": doc_idx,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            })

    print(f"✅ Extracted {len(all_chunks)} total chunks from {url}")
    return all_chunks


def save_chunks(chunks: List[Dict], output_dir: str = "data/extracted_content") -> str:
    """
    Save processed chunks to a JSON file.

    Args:
        chunks (list): List of chunk dicts
        output_dir (str): Directory to save chunks

    Returns:
        str: Path to saved file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_path = os.path.join(output_dir, "chunks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved {len(chunks)} chunks → {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract content from web pages")
    parser.add_argument(
        "--url",
        default=os.getenv("TARGET_URL", "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"),
        help="URL to extract content from",
    )
    parser.add_argument(
        "--output", default="data/extracted_content", help="Output directory"
    )
    args = parser.parse_args()

    chunks = extract_content_from_url(args.url)
    if chunks:
        save_chunks(chunks, args.output)
    else:
        print("❌ No content extracted.")
