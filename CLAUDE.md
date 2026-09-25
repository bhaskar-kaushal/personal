# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

All code lives in `rag-type/`, a two-part RAG learning assignment (EPAM GenAI bootcamp):

- `rag-type/basic-rag/` — Assignment 1: single-shot RAG (load chunks → embed → FAISS/ChromaDB → retrieve top-k → prompt → LLM).
- `rag-type/conversational-rag/` — Assignment 2: wraps Assignment 1 with chat history, message trimming and a Streamlit UI.

The assignment READMEs (`rag-type/README.md` and each sub-README) are the spec. Grading is concept-focused (loading, chunking, embedding, retrieval, context injection), out of 100 with 70 to pass. Some file names in the READMEs don't match the code (see "Gotchas").

## Commands

Run all of these from `rag-type/` unless noted. There is no linter or build config.

```bash
pip install -r requirements.txt            # superset of both sub-projects' deps (incl. langfuse, tiktoken)

# Unit tests (stdlib unittest; covers extract_content + message_trimming only, no API calls)
python -m unittest tests.test
python -m unittest tests.test.TestChunkText.test_short_text_returns_single_chunk   # single test

# Assignment 1 (run from rag-type/basic-rag/)
python basic_rag.py --query "What is RAG?" [--vector-store faiss|chromadb] [--content-dir DIR]
python embedding_comparison.py
python vector_store_comparison.py          # still a TODO stub

# Assignment 2 (run from rag-type/conversational-rag/)
streamlit run app.py
python conversation_history.py --session-id test123   # CLI chat
python extract_content.py --url https://...
python message_trimming.py --test
python chat_history.py --list | --export SESSION_ID

# Langfuse smoke test (makes real API calls; needs credentials)
python test_langfuse_instrumentation.py
```

## Configuration

`.env` files (gitignored) are loaded with `python-dotenv` from the current working directory; the Langfuse test script loads `conversational-rag/.env` explicitly.

- `DIAL_API_KEY`: EPAM DIAL key. Without it the client prints a warning and `get_completion` returns an error string. It does not raise.
- `TARGET_URL`: page to scrape when `chunks.json` is missing (defaults to the Wikipedia RAG article).
- `EMBEDDING_MODEL`: HuggingFace/sentence-transformers model (default `all-MiniLM-L6-v2`).
- `MAX_HISTORY_LENGTH` (default 10), `DIAL_TEMPERATURE` (default 0.7).
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`: see `rag-type/LANGFUSE_SETUP.md`.

## Architecture

**LLM access**: `utils/dial_client.py::DIALClient` wraps `openai.AzureOpenAI` pointed at `https://ai-proxy.lab.epam.com` (api-version `2024-02-01`, default model `gpt-4`). All generation goes through `get_completion(messages)`, which takes OpenAI-style message dicts. Embeddings are local (`HuggingFaceEmbeddings`, CPU), not DIAL.

**Assignment 1 pipeline** (`basic-rag/basic_rag.py::BasicRAG`): `setup()` = `load_documents()` from `<content_dir>/chunks.json`, then `create_vector_store()` (FAISS in memory or Chroma). `query()` = `retrieve_relevant_docs()` + `generate_response()`. If `chunks.json` is missing, the CLI auto-extracts from `TARGET_URL`. `chunks.json` is the handoff format between extraction and RAG: a list of dicts with text + metadata (source URL, chunk index).

**Assignment 2 reuses Assignment 1 through `sys.path`, not packaging.** `conversational-rag/conversation_history.py::ConversationalRAG` (this is the README's "conversational_rag.py") inserts `../basic-rag` into `sys.path`, imports `BasicRAG`, and by default reads `basic-rag/data/extracted_content/chunks.json`. It picks the embedding model by setting `os.environ["EMBEDDING_MODEL"]` before it builds `BasicRAG`. On each turn it:
1. builds a standalone retrieval query from the recent (trimmed) history, using string concatenation rather than an extra LLM call
2. retrieves docs through `BasicRAG`
3. sends the system prompt, the trimmed history and the context-augmented user message to DIAL
4. persists both turns through `chat_history.ChatHistoryManager`

- `message_trimming.trim_messages(messages, max_history_length)` returns `(trimmed, removed_count)`. It keeps the most recent messages and prepends a summary of older ones. Its public API (`get_encoding`, `count_tokens`, `trim_messages`) is pinned by the tests. Tokens are counted with tiktoken `cl100k_base`, falling back to a whitespace split.
- `chat_history.ChatSession` persists each session as `<persist_dir>/<session_id>.json` (default `data/chat_sessions`, **relative to CWD**). That is why stray `data/chat_sessions/` dirs exist at several levels of the repo.
- `app.py` caches one `ConversationalRAG` per config combo with `@st.cache_resource`. The sidebar switches vector store, embedding model and target URL.

**Observability**: Langfuse v3 (`langfuse.get_client()`) is initialized at module import in `basic_rag.py`, `conversation_history.py`, `app.py` and `basic-rag/utils/dial_client.py`. `load_dotenv()` must run *before* `get_client()`, so keep that import order. The DIAL call is recorded as a `generation` observation. Session grouping uses `trace_context` / context-manager spans. See `rag-type/INSTRUMENTATION_SUMMARY.md`.

## Gotchas

- **Two different `utils` packages.** `basic-rag/utils/dial_client.py` has Langfuse instrumentation; `conversational-rag/utils/dial_client.py` does not. Which one `from utils.dial_client import DIALClient` resolves to depends on `sys.path` order: when running from `conversational-rag/` (or in `tests/test.py`, which inserts `conversational-rag` last, at index 0), the conversational copy wins even inside `basic_rag.py`. Change both copies, or be deliberate about which one you mean.
- `extract_content.py` exists only in `conversational-rag/`, although `basic_rag.py` and the tests import it as if it were in `basic-rag/`. The import only works because of `sys.path`. Running `basic_rag.py` from `basic-rag/` without an existing `chunks.json` will fail to import it.
- `vector_store_comparison.py` is still an unimplemented TODO skeleton.
