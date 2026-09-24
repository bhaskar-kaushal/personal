"""
Streamlit Conversational RAG Web Interface — Assignment 2.

Features:
  - Chat interface with timestamps
  - Sidebar configuration (vector store, embedding model, URL, session)
  - Smart message trimming status
  - Show retrieved document chunks
  - Download chat session as JSON
  - Session reset

Run:
    streamlit run app.py
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Import and initialize Langfuse early (after load_dotenv, before other imports)
from langfuse import get_client as get_langfuse_client
langfuse_client = get_langfuse_client()

# ---------------------------------------------------------------------------
# Path setup so we can import from basic-rag
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "basic-rag"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Conversational RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []  # {role, content, timestamp}
if "conv_rag" not in st.session_state:
    st.session_state.conv_rag = None
if "rag_ready" not in st.session_state:
    st.session_state.rag_ready = False
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def build_conv_rag(session_id, vector_store, embedding_model, target_url, max_history):
    """Build and setup ConversationalRAG (cached per unique config combo)."""
    from conversation_history import ConversationalRAG

    conv = ConversationalRAG(
        session_id=session_id,
        vector_store_type=vector_store,
        embedding_model=embedding_model,
        max_history_length=max_history,
    )
    conv.setup(auto_extract_url=target_url)
    return conv


def reset_rag_cache():
    build_conv_rag.clear()


def format_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return iso


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    st.subheader("📡 Data Source")
    target_url = st.text_input(
        "Target URL",
        value=os.getenv("TARGET_URL", "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"),
        help="Web page to extract knowledge from",
    )

    st.subheader("🗄️ Vector Store")
    vector_store = st.selectbox(
        "Backend",
        ["faiss", "chromadb"],
        help="FAISS is faster; ChromaDB is persistent",
    )

    st.subheader("🔢 Embedding Model")
    embedding_model = st.selectbox(
        "Model",
        ["all-MiniLM-L6-v2", "all-MiniLM-L12-v2", "paraphrase-MiniLM-L3-v2"],
        help="Larger models = better quality, slower speed",
    )

    st.subheader("💬 Session")
    max_history = st.slider("Max history (pairs)", 3, 20, 10)
    session_id = st.text_input("Session ID", value=st.session_state.session_id)

    col1, col2 = st.columns(2)
    with col1:
        init_btn = st.button("🚀 Initialize", use_container_width=True)
    with col2:
        reset_btn = st.button("🔄 Reset Chat", use_container_width=True)

    if init_btn:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        st.session_state.rag_ready = False
        reset_rag_cache()
        with st.spinner("Building RAG system… (first run downloads models)"):
            try:
                st.session_state.conv_rag = build_conv_rag(
                    session_id, vector_store, embedding_model, target_url, max_history
                )
                st.session_state.rag_ready = True
                st.success("✅ RAG ready!")
            except Exception as e:
                st.error(f"❌ Setup failed: {e}")

    if reset_btn:
        st.session_state.messages = []
        if st.session_state.conv_rag:
            st.session_state.conv_rag.reset_session()
        st.rerun()

    st.divider()
    st.subheader("📥 Export")
    if st.button("Download session JSON", use_container_width=True):
        if st.session_state.messages:
            export_data = json.dumps(
                {
                    "session_id": st.session_state.session_id,
                    "messages": st.session_state.messages,
                },
                ensure_ascii=False,
                indent=2,
            )
            st.download_button(
                "⬇️ Save JSON",
                data=export_data,
                file_name=f"{st.session_state.session_id}.json",
                mime="application/json",
            )
        else:
            st.info("No messages to export yet.")

    st.divider()
    st.caption(
        "Assignment 2 — Conversational RAG\n\n"
        "Powered by LangChain + EPAM DIAL API\n\n"
        f"Session: `{st.session_state.session_id}`"
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("🤖 Conversational RAG Chatbot")

if not st.session_state.rag_ready:
    st.info(
        "👈 Configure settings in the sidebar and click **Initialize** to get started.\n\n"
        "The first run will download embedding models (~100 MB) and extract the target URL."
    )
else:
    # Status bar
    status_cols = st.columns(4)
    status_cols[0].metric("Vector Store", vector_store.upper())
    status_cols[1].metric("Embedding", embedding_model.split("/")[-1])
    status_cols[2].metric("Messages", len(st.session_state.messages))
    status_cols[3].metric("Max History", f"{max_history} pairs")

    st.divider()

    # Chat history display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            ts = format_ts(msg.get("timestamp", ""))
            avatar = "🧑" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content)
                st.caption(ts)

    # Retrieved chunks expander (last turn)
    if st.session_state.last_chunks:
        with st.expander(f"📄 Retrieved chunks ({len(st.session_state.last_chunks)})", expanded=False):
            for i, doc in enumerate(st.session_state.last_chunks, 1):
                source = doc.metadata.get("source", "unknown")
                st.markdown(f"**Chunk {i}** — `{source}`")
                st.text(doc.page_content[:400] + ("…" if len(doc.page_content) > 400 else ""))
                if i < len(st.session_state.last_chunks):
                    st.divider()

    # Chat input
    user_input = st.chat_input("Ask a question about the content…")
    if user_input:
        ts_now = datetime.utcnow().isoformat()

        # Show user message immediately
        with chat_container:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)
                st.caption(format_ts(ts_now))

        st.session_state.messages.append(
            {"role": "user", "content": user_input, "timestamp": ts_now}
        )

        # Get response
        with st.spinner("Thinking…"):
            try:
                # Retrieve docs for display
                search_query = st.session_state.conv_rag._build_standalone_query(user_input)
                retrieved = st.session_state.conv_rag.rag.retrieve_relevant_docs(search_query, k=3)
                st.session_state.last_chunks = retrieved

                response = st.session_state.conv_rag.chat(user_input)
                resp_ts = datetime.utcnow().isoformat()

            except Exception as e:
                response = f"❌ Error: {e}"
                resp_ts = datetime.utcnow().isoformat()

        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(response)
                st.caption(format_ts(resp_ts))

        st.session_state.messages.append(
            {"role": "assistant", "content": response, "timestamp": resp_ts}
        )

        # Flush Langfuse traces before rerun (important for Streamlit's script execution model)
        langfuse_client.flush()

        st.rerun()
