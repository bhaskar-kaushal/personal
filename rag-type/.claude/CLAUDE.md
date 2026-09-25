# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) learning project** with two progressive assignments:

- **Assignment 1 (Basic RAG)**: Build a simple Q&A system that extracts web content, chunks it, embeds it into a vector store, and generates answers using the EPAM DIAL API.
- **Assignment 2 (Conversational RAG)**: Extend Assignment 1 with conversation memory, a Streamlit web UI, and smart message trimming for managing long conversations.

**Key Technologies:**
- LangChain (RAG pipeline and conversation chains)
- Vector Stores: FAISS and ChromaDB
- Embeddings: sentence-transformers
- LLM: EPAM DIAL API (AzureOpenAI-compatible)
- Streamlit (web UI for Assignment 2)
- Langfuse (observability and tracing)

## Project Structure

```
rag-type/
├── README.md                                # Main overview
├── CLAUDE.md                                # This file
├── LANGFUSE_SETUP.md                        # Langfuse instrumentation guide
├── INSTRUMENTATION_SUMMARY.md               # Changes made for Langfuse
├── requirements.txt                         # Root-level dependencies (includes langfuse)
├── test_langfuse_instrumentation.py         # Test script for Langfuse setup
│
├── basic-rag/                               # Assignment 1
│   ├── README.md                            # Assignment 1 instructions
│   ├── requirements.txt                     # Assignment 1 dependencies
│   ├── .env.example                         # Template for environment variables
│   ├── extract_content.py                   # Web content extraction
│   ├── basic_rag.py                         # Main RAG implementation with CLI
│   ├── vector_store_comparison.py           # Compare FAISS vs ChromaDB
│   ├── embedding_comparison.py              # Compare embedding models
│   ├── utils/
│   │   ├── __init__.py
│   │   └── dial_client.py                   # EPAM DIAL API client (instrumented with Langfuse)
│   ├── data/
│   │   ├── extracted_content/               # Processed document chunks
│   │   └── sample_urls.txt
│   └── docs/
│       └── rag_concepts.md
│
├── conversational-rag/                      # Assignment 2
│   ├── README.md                            # Assignment 2 instructions
│   ├── requirements.txt
│   ├── .env                                 # Environment variables (gitignored)
│   ├── app.py                               # Streamlit web UI
│   ├── conversational_rag.py                # LangChain conversation chain
│   ├── conversation_history.py              # Instrumented with Langfuse
│   ├── chat_history.py                      # Chat session management
│   ├── message_trimming.py                  # Smart message trimming
│   ├── extract_content.py                   # Reused from Assignment 1
│   ├── utils/
│   │   ├── __init__.py
│   │   └── dial_client.py                   # EPAM DIAL API client (instrumented)
│   ├── data/
│   │   ├── extracted_content/               # Reused from Assignment 1
│   │   └── chat_sessions/                   # Saved conversation sessions
│   └── docs/
│       └── conversational_concepts.md
│
├── tests/
│   └── test.py
│
├── data/
│   └── chat_sessions/                       # Stored session data
│
└── .git/                                    # Git repository
```

## Common Development Commands

### Setup & Installation

```bash
# Root-level dependencies (includes Langfuse)
pip install -r requirements.txt

# Assignment 1 (Basic RAG)
cd basic-rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with DIAL_API_KEY and TARGET_URL

# Assignment 2 (Conversational RAG)
cd conversational-rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Use .env from template or copy from Assignment 1
```

### Assignment 1: Basic RAG

```bash
cd basic-rag

# Extract content from a website
python extract_content.py --url https://example.com

# Run vector store comparison
python vector_store_comparison.py

# Run embedding model comparison
python embedding_comparison.py

# Test basic RAG with a query
python basic_rag.py --query "What is the main topic?"

# Run with specific vector store (faiss or chromadb)
python basic_rag.py --query "Your question" --vector-store faiss
```

### Assignment 2: Conversational RAG

```bash
cd conversational-rag

# Start Streamlit web UI
streamlit run app.py

# Run conversational RAG from CLI
python conversational_rag.py --session-id test123

# Test message trimming
python message_trimming.py --test

# Export a chat session
python chat_history.py --export session123
```

### Testing & Observability

```bash
# Test Langfuse instrumentation setup
cd /path/to/rag-type
python test_langfuse_instrumentation.py

# After running any RAG workflow, traces appear in Langfuse:
# - Cloud: https://cloud.langfuse.com
# - View traces, sessions, and analytics
```

## Key Files & Their Roles

### Core RAG Implementation

**basic-rag/utils/dial_client.py**
- Wraps EPAM DIAL API (AzureOpenAI-compatible)
- Instrumented with Langfuse generation observations
- Handles message formatting and token counting
- Exception handling for API failures

**basic-rag/basic_rag.py**
- Main RAG pipeline: retrieves documents, generates answers
- Instrumentated with Langfuse traces (top-level span) and retriever observations
- Supports CLI queries with `--query` and `--vector-store` flags
- Methods: `load_vector_store()`, `retrieve_relevant_docs()`, `query()`

**conversational-rag/conversation_history.py**
- Extends basic RAG with conversation memory
- Top-level Langfuse trace includes `session_id` for grouping conversations
- Methods: `chat()` for multi-turn conversations
- Handles context-aware retrieval using conversation history

**conversational-rag/app.py**
- Streamlit web UI for conversational RAG
- Initializes Langfuse client early (after `load_dotenv()`)
- Calls `langfuse_client.flush()` before `st.rerun()` to send traces
- Sidebar for configuration (vector store, embedding model selection)

### Supporting Files

**extract_content.py**
- Web scraping using LangChain `WebBaseLoader`
- Document chunking with configurable overlap
- Metadata extraction (source URL, chunk index)

**vector_store_comparison.py**
- Sets up both FAISS and ChromaDB
- Benchmarks indexing time, retrieval speed, and storage
- Documents trade-offs and use-case recommendations

**embedding_comparison.py**
- Tests multiple embedding models (sentence-transformers, OpenAI)
- Compares quality, speed, and cost
- Generates comparison report

**message_trimming.py**
- Implements smart message trimming to avoid token limits
- Keeps recent messages + summarizes older ones
- Preserves important context while reducing token usage

**chat_history.py**
- Stores and retrieves chat sessions with timestamps
- Manages conversation state and session metadata
- Supports session export/import

## Langfuse Observability Integration

**Status:** ✅ Fully instrumented

### What's Traced

1. **Basic RAG (`basic_rag.py`)**
   - Top-level trace: `basic-rag-query` (includes user query and answer)
   - Retriever span: `retrieve-documents` (vector similarity search results)
   - Generation span: `dial-completion` (LLM call with token counts)

2. **Conversational RAG (`conversation_history.py`)**
   - Top-level trace: `conversational-rag-chat` with `session_id` (groups multi-turn conversations)
   - Retriever and generation spans nested as above

3. **LLM Calls (`dial_client.py`)**
   - Generation observation: `dial-completion`
   - Captures input messages, output content, model name, token usage

### Setup

```bash
# 1. Create free Langfuse account at https://langfuse.com/cloud
# 2. Get API keys (Public Key, Secret Key)
# 3. Set in .env:
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# 4. Credentials are loaded via load_dotenv() before Langfuse client init
# 5. Test with: python test_langfuse_instrumentation.py
```

### Viewing Traces

- **Traces view:** Full request hierarchy with latency and token counts
- **Sessions view:** Multi-turn conversations grouped by `session_id`
- **Custom dashboards:** Filter by model, cost, latency, etc.

See `LANGFUSE_SETUP.md` and `INSTRUMENTATION_SUMMARY.md` for full details.

## Architecture Patterns

### Trace Hierarchy (Langfuse)

```
basic-rag-query [top-level]
├── retrieve-documents [retriever]
│   └── vector similarity search results
└── dial-completion [generation]
    └── LLM response + token usage

conversational-rag-chat [top-level, session_id="..."]
├── retrieve-documents [retriever]
└── dial-completion [generation]
```

### Token Management

- `message_trimming.py` keeps recent messages and summarizes older context
- Configurable token limits to avoid LLM API errors
- Langfuse traces show actual token usage for optimization

### Error Handling

- `dial_client.py` catches API failures and logs at error level
- Traces complete even on errors (explicit `.end()` calls)
- `.env` missing: Clear error prompting Langfuse credentials setup

## Common Patterns & Best Practices

### Adding a New Vector Store

1. Implement in `vector_store_comparison.py` (or new file)
2. Follow the same interface as FAISS/ChromaDB (embed, add, search)
3. Add to CLI argument choices in `basic_rag.py` and `app.py`
4. Document trade-offs and when to use

### Adding a New Embedding Model

1. Implement in `embedding_comparison.py`
2. Add to embedding model registry in `app.py` sidebar
3. Ensure compatibility with LangChain's embedding interface
4. Document quality metrics and latency

### Extending Conversation Memory

- `conversation_history.py` is the central point for multi-turn context
- Modify `retrieve_with_conversation_context()` to change how history influences retrieval
- Message trimming happens before sending to DIAL API

### Adding Langfuse Observations

All files already have Langfuse instrumentation. To add more:
1. Import: `from langfuse import get_client as get_langfuse_client`
2. Initialize after `load_dotenv()`: `langfuse_client = get_langfuse_client()`
3. Start observation: `span = langfuse_client.start_observation(...)`
4. Update and end: `span.update(...); span.end()`

## Important Notes

- **Assignment 1 is a prerequisite** for Assignment 2. Assignment 2 reuses the vector store and embedding logic.
- **Streamlit reloads the entire script** on each interaction; Langfuse `flush()` is called before `st.rerun()` to ensure traces are sent.
- **DIAL API key** must be set in `.env` for any LLM calls to work.
- **Vector store persistence:** `basic_rag.py` saves/loads vector stores from `data/extracted_content/`
- **Session storage:** Conversational RAG saves sessions to `data/chat_sessions/` by default.

## Testing

- `tests/test.py` contains general test cases
- `test_langfuse_instrumentation.py` verifies Langfuse setup end-to-end
- Run via: `python test_langfuse_instrumentation.py` from project root

## When Making Changes

1. **Preserve Langfuse instrumentation** — traces are valuable for debugging
2. **Keep Assignment 1 and 2 loosely coupled** — Assignment 2 copies/imports from Assignment 1 but stays independent
3. **Update both .env.example templates** when adding new config variables
4. **Test CLI and Streamlit paths** separately (different initialization flows)
5. **Verify token counting** after prompt changes (impacts cost and LLM limits)
