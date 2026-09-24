# 💬 Conversational RAG with Streamlit - Assignment 2

**Target Audience:** Intermediate Level Developers  
**Focus:** Extending Basic RAG to Conversational System  
**Prerequisites:** Complete Assignment 1 (Basic RAG)  
**Use Case:** Build a chatbot that remembers conversation history and handles follow-up questions

## 🎯 Learning Objectives

By completing this assignment, you will:
- Build a **Conversational RAG** system using **LangChain**
- Implement **chat history** management and context awareness
- Create a **Streamlit** web interface for user interaction
- Implement **trimmed_messages** for efficient LLM usage
- Practice advanced prompt engineering for conversations

## 📋 Prerequisites

- **MUST COMPLETE**: Assignment 1 (Basic RAG)
- Python 3.11+ experience
- Understanding of RAG concepts from Assignment 1
- Basic knowledge of web interfaces

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd conversational-rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create `.env` file in the project root:
```env
DIAL_API_KEY=your_dial_api_key_here
TARGET_URL=https://example-website.com
MAX_HISTORY_LENGTH=10
```

**Getting your DIAL API Key:**
1. Obtain your API key from the EPAM Support
2. Replace `your_dial_api_key_here` with your actual key

### 3. Run the Conversational RAG
```bash
# Start Streamlit app
streamlit run app.py

# Or run command-line version
python conversational_rag.py
```

## 📁 Project Structure

```
conversational-rag/
├── README.md                 # Assignment documentation
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── app.py                   # Streamlit web interface
├── conversational_rag.py    # LangChain conversational RAG
├── chat_history.py          # Chat history management
├── message_trimming.py      # Trimmed messages implementation
├── vector_store.py          # Vector store from Assignment 1 (enhanced)
├── utils/
│   ├── __init__.py
│   └── dial_client.py       # EPAM DIAL API client
├── data/
│   ├── extracted_content/   # Content from Assignment 1
│   └── chat_sessions/       # Saved chat sessions
└── docs/
    └── conversational_concepts.md
```

## 🏗️ How This Extends Assignment 1

### Assignment 1 Capability:
```
User: "What is the main topic of this website?"
Bot: "The website focuses on machine learning techniques..."
```

### Assignment 2 Enhancement:
```
User: "What is the main topic of this website?"
Bot: "The website focuses on machine learning techniques..."

User: "Can you elaborate on that?"
Bot: "Referring to my previous answer about machine learning, here are more details..."

User: "How does this relate to what we discussed earlier?"
Bot: "Based on our conversation about ML techniques, the connection is..."
```

## 🏗️ Core Requirements

### Phase 1: LangChain Conversational RAG

1. **Extend Assignment 1 Vector Store**
   - Copy your best vector store implementation from Assignment 1
   - **Allow users to switch vector stores** (FAISS/ChromaDB)
   - **Allow users to switch embedding models** via UI
   - Explain the performance impact of each choice

2. **LangChain Conversation Chain**
   - Use LangChain ConversationChain or ConversationalRetrievalChain
   - Add chat history to retrieval context
   - Create conversation-aware prompt templates
   - Handle follow-up questions and context references

### Phase 2: Chat History & Message Trimming

3. **Chat History Management**
   - Store conversation history with timestamps
   - Implement conversation context for better retrieval
   - Add ability to reference previous answers
   - Handle conversation reset and new sessions

4. **Trimmed Messages Implementation**
   - **Implement smart message trimming** to avoid token limits
   - Keep recent messages + summarize older ones
   - Preserve important context while reducing tokens
   - Add configurable trimming strategies

### Phase 3: Streamlit Interface

5. **Web Interface**
   - Create clean Streamlit chat interface
   - Add sidebar for configuration (vector store, embedding model)
   - Show conversation history with timestamps
   - Add download chat session functionality

6. **Advanced Features**
   - Real-time streaming responses
   - Show retrieved documents for each answer
   - Add feedback mechanism (thumbs up/down)
   - Display token usage and cost estimation

## 🔧 Implementation Steps

### Step 1: Extend Vector Store from Assignment 1
```python
# TODO: Copy and enhance vector_store.py from Assignment 1
# - Add runtime switching between FAISS/ChromaDB
# - Add runtime switching between embedding models
# - Add performance monitoring
```

### Step 2: LangChain Conversation Chain
```python
# TODO: Implement in conversational_rag.py
# - Use LangChain ConversationalRetrievalChain
# - Add memory for chat history
# - Implement context-aware retrieval
```

### Step 3: Message Trimming System
```python
# TODO: Implement in message_trimming.py
# - Smart message trimming algorithm
# - Context preservation strategies
# - Configurable trimming options
```

### Step 4: Streamlit Interface
```python
# TODO: Implement in app.py
# - Chat interface with history
# - Configuration sidebar
# - Real-time response streaming
```

## 📝 Submission Requirements

### Required Files
- ✅ `app.py` - Working Streamlit interface
- ✅ `conversational_rag.py` - LangChain conversation implementation
- ✅ `message_trimming.py` - Trimmed messages system
- ✅ `chat_history.py` - Chat session management
- ✅ Analysis document comparing Assignment 1 vs 2 learnings


## 🔧 Development Commands

```bash
# Start Streamlit app
streamlit run app.py

# Test conversational RAG without UI
python conversational_rag.py --session-id test123

# Test message trimming
python message_trimming.py --test

# Export chat session
python chat_history.py --export session123
```

## 🔄 Connection to Assignment 1

This assignment **extends** your Assignment 1 work:

- **Reuse** your vector store comparison insights
- **Enhance** your embedding model knowledge
- **Apply** RAG learnings to conversational context
- **Compare** simple vs conversational RAG performance