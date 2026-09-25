# Coding Conventions for RAG Project

This file documents the coding conventions and standards for the RAG (Retrieval-Augmented Generation) project.

## Table of Contents
1. [Python Code Style](#python-code-style)
2. [Naming Conventions](#naming-conventions)
3. [Documentation & Comments](#documentation--comments)
4. [API Conventions](#api-conventions)
5. [Langfuse Instrumentation](#langfuse-instrumentation)
6. [Error Handling](#error-handling)
7. [Testing Conventions](#testing-conventions)

---

## Python Code Style

### General Guidelines

- **Line Length**: Maximum 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8
- **Imports**: Follow PEP 8 grouping
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
  
  Separate each group with a blank line.

```python
# ✅ GOOD
import os
import sys
from typing import List, Dict, Any, Optional

from langchain import LLMChain
from openai import AzureOpenAI
from dotenv import load_dotenv

from utils.dial_client import DIALClient
from data.loader import load_vector_store
```

### Type Hints

- **Required**: Public functions and methods
- **Optional**: Private methods and simple functions
- Use `typing` module for complex types

```python
# ✅ GOOD - Public method
def query(self, question: str) -> str:
    """Execute a RAG query and return the answer."""
    pass

def retrieve_relevant_docs(
    self, 
    query: str, 
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve top-k relevant documents."""
    pass

# ❌ AVOID - Missing type hints on public method
def query(question):
    pass
```

### Formatting

- **Blank Lines**: 2 lines between top-level functions/classes, 1 line between methods
- **String Quotes**: Use double quotes (`"`) for strings
- **F-strings**: Preferred for string formatting

```python
# ✅ GOOD
name = "Alice"
message = f"Hello, {name}!"

# ❌ AVOID
message = "Hello, " + name + "!"
message = "Hello, {}!".format(name)
```

### Line Wrapping

Break long lines at logical points:

```python
# ✅ GOOD
response = self.client.chat.completions.create(
    model=model_used,
    messages=messages,
    temperature=float(os.getenv("DIAL_TEMPERATURE", "0.7"))
)

# ✅ GOOD - Long function call
retrieved_docs = self.retrieve_relevant_docs(
    query=user_query,
    top_k=5,
    vector_store_type="faiss"
)
```

---

## Naming Conventions

### Variables & Functions

- **Functions & Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with single underscore `_private_method()`
- **Magic**: Prefix/suffix with double underscore `__dunder__` (only for Python special cases)

```python
# ✅ GOOD
def get_completion(messages: List[Dict]) -> str:
    pass

max_retries = 3
DIAL_API_TIMEOUT = 30

def _internal_helper():
    pass

# ❌ AVOID
def GetCompletion(messages):
    pass

MaxRetries = 3
DIAL_api_timeout = 30
```

### Classes

- **PascalCase** (CapitalizedWords)
- **Descriptive names** for clarity

```python
# ✅ GOOD
class DIALClient:
    pass

class VectorStoreManager:
    pass

class ConversationHistory:
    pass

# ❌ AVOID
class dialClient:
    pass

class VSM:
    pass
```

### Files & Modules

- **snake_case** for filenames
- **Descriptive, singular or plural** appropriately

```
# ✅ GOOD
dial_client.py
vector_store_manager.py
conversation_history.py
utils/
data/

# ❌ AVOID
DIALClient.py
vector_store.py
histories.py
```

### Constants

Environment variable prefixes and global constants:

```python
# ✅ GOOD
DIAL_API_KEY = os.getenv("DIAL_API_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")
DEFAULT_MODEL = "gpt-4"
DEFAULT_VECTOR_STORE = "faiss"

# ❌ AVOID
api_key = os.getenv("DIAL_API_KEY")
langfuse_host = os.getenv("LANGFUSE_HOST")
```

---

## Documentation & Comments

### Docstrings

- **Style**: Google-style docstrings for clarity
- **Required for**: Public functions, classes, and methods
- **Keep brief**: Only document non-obvious logic

```python
# ✅ GOOD
def get_completion(
    self, 
    messages: List[Dict[str, str]], 
    model: Optional[str] = None
) -> str:
    """
    Get completion from DIAL API.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Override default model for this request.

    Returns:
        Response content from the model.

    Raises:
        APIError: If API call fails after retries.
    """
    pass

# ❌ AVOID - Over-documented
def get_completion(messages, model=None):
    # This function gets a completion
    # It takes messages and model
    # It returns a string
    pass
```

### Comments

- **Only when WHY is non-obvious**, not WHAT
- **Explain reasoning**, not just describe code
- **Avoid obvious comments**

```python
# ✅ GOOD - Explains reasoning
# Load dotenv before Langfuse init so credentials are available to SDK
load_dotenv()
langfuse_client = get_langfuse_client()

# ✅ GOOD - Explains workaround
# Retry with exponential backoff for rate limit errors (API returns 429)
if isinstance(e, RateLimitError):
    time.sleep(2 ** attempt)

# ❌ AVOID - Obvious comments
# Increment counter
count += 1

# This is the DIALClient class
class DIALClient:
    pass
```

### No Comments for:

- **What the code does** (variable names should be clear)
- **Current task references** (use commit messages instead)
- **Removed code** (use git history)

---

## API Conventions

### Client Design

**Pattern**: Wrapper class around Azure OpenAI SDK

```python
class DIALClient:
    """Client for EPAM DIAL API (Azure OpenAI-compatible)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize DIAL client with credentials."""
        self.api_key = api_key or os.getenv("DIAL_API_KEY")
        self.model = model
        self.azure_endpoint = "https://ai-proxy.lab.epam.com"
        self.api_version = "2024-02-01"
        
        # Validate and initialize
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint
            )
            if not self.api_key or self.api_key == "<YOUR_API_KEY_HERE>":
                print("🚨 DIAL API Key not found.")
                self.client = None
            else:
                print("✅ DIAL Client initialized!")
        except Exception as e:
            print(f"🔥 Error initializing DIAL: {e}")
            self.client = None
```

### Method Naming

- **Verb + Object**: `get_completion()`, `analyze_sentiment()`, `generate_response()`
- **Private helpers**: `_format_messages()`, `_validate_input()`

```python
# ✅ GOOD - Clear method names
def get_completion(self, messages: List[Dict]) -> str:
    pass

def analyze_sentiment(self, text: str) -> str:
    pass

def generate_response(self, context: str, query: str) -> str:
    pass

def _format_messages(self, messages: List[Dict]) -> List[Dict]:
    pass
```

### Message Format

```python
# ✅ GOOD - Proper OpenAI format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is RAG?"}
]

# For multi-turn conversations
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "First question"},
    {"role": "assistant", "content": "First answer"},
    {"role": "user", "content": "Follow-up question"}
]
```

### Parameter Conventions

```python
# ✅ GOOD - Load from environment
DIAL_TEMPERATURE = float(os.getenv("DIAL_TEMPERATURE", "0.7"))
DIAL_MAX_TOKENS = int(os.getenv("DIAL_MAX_TOKENS", "2000"))

# ✅ GOOD - Allow override per request
def get_completion(
    self, 
    messages: List[Dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None
) -> str:
    model_used = model or self.model
    temp_used = temperature or DIAL_TEMPERATURE
    pass
```

### Error Messages

Prefix error messages with emoji for visibility:

```python
# ✅ GOOD - Clear error prefixes
print("❌ Error calling DIAL API: {e}")
print("🚨 API Key not found. Please set DIAL_API_KEY.")
print("✅ DIAL Client initialized successfully!")
print("🧪 Testing DIAL API connection...")
print("🔥 Critical error in Langfuse initialization.")
```

---

## Langfuse Instrumentation

### Trace Hierarchy

**Basic RAG**:
```
basic-rag-query (top-level trace)
├── retrieve-documents (retriever span)
└── dial-completion (generation span)
```

**Conversational RAG**:
```
conversational-rag-chat (top-level, session_id="...")
├── retrieve-documents (retriever span)
└── dial-completion (generation span)
```

### Observation Naming

- **Top-level trace**: Descriptive of operation: `basic-rag-query`, `conversational-rag-chat`
- **Retriever span**: `retrieve-documents`
- **Generation span**: `dial-completion`

```python
# ✅ GOOD - Top-level trace
trace = langfuse_client.start_trace(
    name="basic-rag-query",
    input={"query": user_query},
    session_id=None  # None for basic RAG
)

# ✅ GOOD - Conversational trace with session_id
trace = langfuse_client.start_trace(
    name="conversational-rag-chat",
    input={"query": user_query},
    session_id=session_id
)

# ✅ GOOD - Retriever span
retriever_span = langfuse_client.start_observation(
    name="retrieve-documents",
    as_type="retrieval",
    trace_id=trace.id,
    input={"query": query}
)

# ✅ GOOD - Generation span
generation = langfuse_client.start_observation(
    name="dial-completion",
    as_type="generation",
    input={"messages": messages}
)
generation.update(model=model_used)
```

### Required Captures

```python
# ✅ GOOD - Complete observation capture
generation = langfuse_client.start_observation(
    name="dial-completion",
    as_type="generation",
    input={"messages": messages}
)
generation.update(model=model_used)

response = self.client.chat.completions.create(
    model=model_used,
    messages=messages,
    temperature=temperature
)

content = response.choices[0].message.content

generation.update(
    output={"content": content},
    usage={
        "input": response.usage.prompt_tokens,
        "output": response.usage.completion_tokens
    }
)
generation.end()
```

### Error Handling in Traces

```python
# ✅ GOOD - Complete observation even on error
generation = None
try:
    generation = langfuse_client.start_observation(
        name="dial-completion",
        as_type="generation",
        input={"messages": messages}
    )
    
    response = self.client.chat.completions.create(...)
    # ... process response
    generation.end()
    
except Exception as e:
    if generation:
        generation.update(level="error")
        generation.end()
    # Handle error appropriately
    return f"❌ Error: {e}"
```

---

## Error Handling

### Exception Types & Handling

```python
from openai import (
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIError
)

# ✅ GOOD - Specific exception handling
try:
    response = self.client.chat.completions.create(...)
except AuthenticationError as e:
    print(f"🚨 Authentication failed: Check DIAL_API_KEY")
    if 'generation' in locals():
        generation.update(level="error")
        generation.end()
    return "❌ API authentication failed"
except RateLimitError as e:
    print(f"⏱️ Rate limited: Retrying with backoff...")
    time.sleep(2 ** attempt_count)
    # Retry logic
except APIConnectionError as e:
    print(f"🔥 Connection error: {e}")
    if 'generation' in locals():
        generation.update(level="error")
        generation.end()
    return "❌ Network connection failed"
except APIError as e:
    print(f"🔥 API error: {e}")
    if 'generation' in locals():
        generation.update(level="error")
        generation.end()
    return "❌ API error occurred"
```

### Validation Pattern

```python
# ✅ GOOD - Validate at API boundaries
def get_completion(self, messages: List[Dict]) -> str:
    """Get completion from DIAL API."""
    
    # Validate client initialization
    if not self.client:
        return "❌ DIAL client not initialized. Check API key."
    
    # Validate input
    if not messages or not isinstance(messages, list):
        return "❌ Invalid messages format"
    
    # Proceed with API call...
```

---

## Testing Conventions

### Test File Naming

- `test_<module_name>.py` for unit tests
- `test_langfuse_instrumentation.py` for integration tests

```python
# ✅ GOOD - Test file naming
test_dial_client.py
test_vector_store.py
test_langfuse_instrumentation.py
```

### Test Function Naming

```python
# ✅ GOOD - Clear test names
def test_dial_connection():
    """Test DIAL API connection and basic functionality."""
    pass

def test_dial_authentication_error():
    """Test handling of authentication errors."""
    pass

def test_langfuse_trace_hierarchy():
    """Test that trace hierarchy matches expected structure."""
    pass

def test_retriever_with_faiss():
    """Test retriever with FAISS vector store."""
    pass
```

### Test Pattern

```python
# ✅ GOOD - Simple test pattern
def test_dial_connection():
    """Test DIAL API connection."""
    client = DIALClient()
    
    if not client.client:
        print("❌ DIAL client initialization failed")
        return False
    
    test_messages = [
        {"role": "user", "content": "Explain technical debt in one sentence."}
    ]
    
    response = client.get_completion(test_messages)
    
    if "Error" not in response:
        print("✅ DIAL API test successful!")
        return True
    else:
        print("❌ DIAL API test failed")
        return False
```

### Testing Before Commit

Run these tests before committing:

```bash
# Test Langfuse instrumentation end-to-end
python test_langfuse_instrumentation.py

# Test vector store implementations
python basic-rag/vector_store_comparison.py

# Test embedding models
python basic-rag/embedding_comparison.py

# Git status and diff review
git status
git diff
```

---

## Summary Checklist

### Before Submitting Code

- [ ] Line length ≤ 100 characters
- [ ] Type hints on all public functions
- [ ] Docstrings (Google style) on public functions
- [ ] Comments only explain WHY, not WHAT
- [ ] Naming follows snake_case for functions/variables, PascalCase for classes
- [ ] Imports organized: stdlib → third-party → local
- [ ] Error handling with proper exception types
- [ ] Langfuse observations complete (even on errors)
- [ ] No trailing whitespace
- [ ] Environment variables use `DIAL_*` prefix
- [ ] Tests pass: `python test_langfuse_instrumentation.py`
- [ ] Commit message follows: `type: description`

### Code Review Questions

- Is the code **readable** without needing comments?
- Are **error messages** clear and actionable?
- Are **Langfuse traces** complete and hierarchical?
- Is the code **testable** with minimal mocking?
- Does it follow the project's **architecture patterns**?
