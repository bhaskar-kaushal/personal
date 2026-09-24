# Langfuse Observability Setup

This RAG project is now instrumented with **Langfuse** for full observability and tracing of your RAG pipeline.

## Quick Start

### 1. Get Langfuse Credentials

If you don't have a Langfuse account:
- Create one free at [https://langfuse.com/cloud](https://langfuse.com/cloud)

Get your API keys:
1. Log into Langfuse
2. Go to **Settings → API Keys**
3. Create a new project API key pair (if you don't have one)
4. Copy the **Public Key** and **Secret Key**

### 2. Set Environment Variables

Add your Langfuse credentials to the `.env` files:

**For Basic RAG:**
```bash
# basic-rag/.env
DIAL_API_KEY=your_dial_api_key_here
TARGET_URL=https://example-website.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**For Conversational RAG:**
```bash
# conversational-rag/.env
DIAL_API_KEY=your_dial_api_key_here
TARGET_URL=https://example-website.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

> **Note:** `.env` files are gitignored for security. Replace the placeholder values with your actual credentials.

### 3. Install Dependencies

Make sure Langfuse is installed:
```bash
pip install -r requirements.txt
```

The latest version of `langfuse` (>=3.0.0) is already in `requirements.txt`.

## What's Instrumented

### ✅ Basic RAG (`basic-rag/basic_rag.py`)

- **Trace**: `basic-rag-query` — top-level RAG pipeline
  - **Retriever Span**: `retrieve-documents` — vector store similarity search
  - **Generation Span**: `dial-completion` — LLM API call (nested under retriever via context)

**Input captured:**
- User query
- Number of documents to retrieve (k)

**Output captured:**
- Retrieved document sources and previews
- Generated answer text

**Metadata captured:**
- Model name (gpt-4, etc.)
- Token counts (input/output)
- Timing for each step

### ✅ Conversational RAG (`conversational-rag/conversation_history.py`)

- **Trace**: `conversational-rag-chat` — single turn in conversation
  - **Session ID**: Links all turns in a conversation together
  - **Retriever Span**: `retrieve-documents` — context-aware retrieval
  - **Generation Span**: `dial-completion` — LLM response generation

**Input captured:**
- User message
- Session ID (for conversation grouping)

**Output captured:**
- Assistant response

**Metadata captured:**
- Session ID (enables Sessions view in Langfuse UI)
- Model name and token counts
- Retrieval quality metrics

### ✅ LLM Integration (`basic-rag/utils/dial_client.py`)

- **Generation Observation**: `dial-completion`
  - Captures every LLM API call to DIAL
  - Includes input messages, output content, and token usage
  - Works with AzureOpenAI client (EPAM DIAL)

## Testing Your Setup

### 1. Quick Test

Run the test script to verify instrumentation:
```bash
cd /Users/bhaskarkaushal/Documents/personal/rag-type
python test_langfuse_instrumentation.py
```

This will:
1. Run basic RAG with a sample query
2. Run conversational RAG with a sample message
3. Flush all traces to Langfuse
4. Print results

### 2. View Traces in Langfuse UI

After running either:
- Basic RAG: `python basic-rag/basic_rag.py --query "What is RAG?"`
- Conversational RAG Streamlit: `streamlit run conversational-rag/app.py`
- Test script: `python test_langfuse_instrumentation.py`

Visit your Langfuse dashboard:
- **Cloud**: https://cloud.langfuse.com
- **Self-hosted**: Your instance URL

Navigate to:
- **Traces** → See individual requests with full hierarchy
- **Sessions** → See conversation flows (conversational RAG only)
- **Dashboard** → Create custom dashboards with filters

## What Each View Shows

### Traces View
Each trace shows:
- Full request hierarchy (trace → retriever → generation)
- Latency for each step
- Token usage and costs
- Input/output data
- Model name
- Error details (if any)

**Example trace flow:**
```
conversational-rag-chat [500ms]
├── retrieve-documents [50ms]
│   └── (vector search results shown)
└── dial-completion [450ms]
    └── (LLM response and tokens shown)
```

### Sessions View
Groups all messages in a conversation by `session_id`:
- See the full conversation flow
- Track token usage across turns
- Analyze conversation quality
- Debug multi-turn interactions

## Architecture

```
App Layer
  ├─ conversational-rag/app.py (Streamlit UI)
  │   └─ calls ConversationalRAG.chat()
  │
  ├─ basic-rag/basic_rag.py (CLI)
  │   └─ calls BasicRAG.query()
  │
Instrumentation Layer
  ├─ Langfuse @observe decorators & spans
  │   ├─ Trace: top-level operation (session_id for conversational)
  │   ├─ Retriever span: vector search
  │   └─ Generation span: LLM call
  │
LLM/Vector Layer
  ├─ basic-rag/utils/dial_client.py (LLM calls)
  └─ LangChain embeddings & vector stores (FAISS/ChromaDB)
```

## Troubleshooting

### Traces not appearing in Langfuse UI?

1. **Check credentials** in `.env`:
   ```bash
   grep LANGFUSE conversational-rag/.env
   ```

2. **Verify Langfuse SDK is installed**:
   ```bash
   python -c "from langfuse import get_client; print(get_client())"
   ```

3. **Check network connectivity** to Langfuse host:
   ```bash
   curl https://cloud.langfuse.com -I
   ```

4. **Enable Langfuse debug logging**:
   ```python
   import os
   os.environ["LANGFUSE_DEBUG"] = "true"
   ```

### "LANGFUSE credentials not set" error?

Make sure you've:
1. Created a Langfuse project and API key
2. Set environment variables in `.env` or shell
3. Restarted your terminal/Python process after setting vars

### Wrong endpoint (not cloud.langfuse.com)?

If self-hosting Langfuse, update `LANGFUSE_HOST` to your instance:
```bash
LANGFUSE_HOST=https://your-langfuse-instance.com
```

## Next Steps

### Monitor Quality
- View traces to understand where time/tokens are spent
- Check retrieval quality by inspecting document chunks
- Monitor LLM response quality over time

### Add Custom Metrics
- Add feedback scores to conversations (thumbs up/down)
- Track specific metrics (relevance, accuracy, latency)
- Create dashboards for continuous monitoring

### Set Up Alerts
- Monitor token usage and costs
- Track error rates
- Create custom alerting rules

## Documentation

- **Langfuse Docs**: https://langfuse.com/docs
- **Python SDK Reference**: https://python.reference.langfuse.com
- **Tracing Guide**: https://langfuse.com/docs/observability/get-started
- **Instrumentation Patterns**: https://langfuse.com/docs/observability/sdk/instrumentation

## Support

For issues or questions:
1. Check Langfuse docs: https://langfuse.com/docs
2. GitHub Issues: https://github.com/langfuse/langfuse/issues
3. Discord Community: https://discord.gg/7NXusKCVnd
