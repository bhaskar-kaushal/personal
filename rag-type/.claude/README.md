# Claude Code Configuration for RAG Project

This directory contains Claude Code configuration files for the RAG (Retrieval-Augmented Generation) project.

## Files Overview

### 1. **CLAUDE.md** (Project Guidance)
Comprehensive documentation for Claude Code when working with this repository.

**Contains:**
- Project overview (2 assignments)
- Complete project structure with descriptions
- Common development commands
- Key files and their roles
- Langfuse observability setup and integration patterns
- Architecture patterns and trace hierarchies
- Common patterns and best practices
- Important notes and guidelines
- Testing procedures
- When to modify files

**Use this when:** You need context about the project structure, available commands, or how components interact.

---

### 2. **conventions.md** (Coding Standards)
Detailed coding conventions and style guide for consistent code quality.

**Contains:**
- Python code style (line length, indentation, imports)
- Naming conventions (functions, classes, files, constants)
- Documentation & comments guidelines
- API conventions (client design, method naming, message format)
- Langfuse instrumentation patterns
- Error handling strategies
- Testing conventions
- Pre-commit checklist

**Sections:**
- **Python Code Style**: Line length (100 chars), imports, type hints, formatting
- **Naming Conventions**: snake_case, PascalCase, prefix rules
- **Documentation**: Docstring style (Google), comment guidance
- **API Conventions**: DIAL client patterns, message formats, parameters
- **Langfuse Instrumentation**: Trace hierarchy, observation naming, captures
- **Error Handling**: Exception types, validation patterns, emoji prefixes
- **Testing**: File naming, test patterns, pre-commit checks

**Use this when:** Writing or reviewing code to ensure it follows project standards.

---

### 3. **settings.json** (Claude Code Configuration)
Machine-readable configuration for Claude Code behavior and rules.

**Contains:**
- **Permissions**: Allowed Bash commands and tools
- **Rules**: Project-specific rules and requirements

**Sections:**

#### Permissions
- Git operations (status, log, diff, show, add, commit, branch)
- File operations (ls, find, grep, curl, cat, head, tail)
- Claude tools (Read, Edit, Write)

#### Rules
- **code_style**: Python formatting and import guidelines
- **langfuse_instrumentation**: Required observability for key files
- **environment_variables**: Required and optional env vars
- **vector_store_management**: Storage paths and supported stores
- **session_management**: Chat session format and naming
- **testing**: Testing requirements and test files
- **assignment_structure**: Assignment separation rules
- **file_modification_guidelines**: What to preserve when modifying
- **documentation_sync**: Files to update together
- **commit_messages**: Commit message format and examples

**Use this when:** Claude Code reads this automatically to enforce project rules.

---

## Quick Reference

### Before Writing Code
1. Read **conventions.md** → understand coding standards
2. Check relevant section in **CLAUDE.md** → understand context
3. Review **settings.json** rules → understand project requirements

### When Making Changes
1. Follow conventions in **conventions.md**
2. Preserve items listed in **file_modification_guidelines**
3. Update documentation as needed (see **documentation_sync**)
4. Follow commit message format from **commit_messages**

### When Running Tests
```bash
# Test Langfuse instrumentation (required before commit)
python test_langfuse_instrumentation.py

# Test vector stores
python basic-rag/vector_store_comparison.py

# Test embeddings
python basic-rag/embedding_comparison.py
```

### When Committing
- Format: `type: description` (e.g., `feat: Add ChromaDB support`)
- Include reasoning in message body
- Run tests before committing
- Check git diff for accuracy

---

## File Relationships

```
CLAUDE.md ──────────────► Project context and guidance
       ↓
conventions.md ─────────► Coding standards to follow
       ↓
settings.json ──────────► Automated rules and permissions
```

- **CLAUDE.md** provides context
- **conventions.md** provides standards
- **settings.json** enforces rules

---

## Key Conventions Summary

### Code Style
- Line length: 100 characters max
- Imports: stdlib → third-party → local
- Type hints: Required on all public functions
- Docstrings: Google style, brief and essential

### Naming
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_prefix`

### Documentation
- Comments explain WHY, not WHAT
- Docstrings for all public functions
- No commented-out code or removed comments
- Commit messages explain reasoning

### API Conventions
- Wrapper class: `DIALClient` around AzureOpenAI
- Methods: `get_completion()`, `analyze_sentiment()`, `generate_response()`
- Errors: Return messages with `❌` prefix
- Langfuse: Always complete observations with `.end()`

### Langfuse Traces
- Top-level: `basic-rag-query` or `conversational-rag-chat`
- Retriever: `retrieve-documents`
- Generation: `dial-completion`
- Always include: model, tokens, latency

### Error Handling
- Specific exception types (AuthenticationError, RateLimitError, etc.)
- Clear error messages with emoji prefixes (✅, ❌, 🔥, 🧪)
- Complete Langfuse observations even on errors

### Testing
- File naming: `test_<module_name>.py`
- Run before commit: `python test_langfuse_instrumentation.py`
- Test both CLI and Streamlit paths

---

## When to Update These Files

### Update CLAUDE.md when:
- Adding new files or directories
- Changing project structure
- Adding new workflows or commands
- Modifying assignment requirements

### Update conventions.md when:
- Changing code style standards
- Adding new API patterns
- Modifying error handling strategy
- Updating testing patterns

### Update settings.json when:
- Adding new environment variables
- Changing permission requirements
- Adding new project rules
- Modifying file modification guidelines

---

## Support & Questions

Refer to the specific file for your question:
- **"How should I name this variable?"** → conventions.md → Naming Conventions
- **"What's the project structure?"** → CLAUDE.md → Project Structure
- **"How do I instrument with Langfuse?"** → conventions.md → Langfuse Instrumentation
- **"What can Claude Code access?"** → settings.json → permissions
- **"How should I write this API client?"** → conventions.md → API Conventions
- **"What files should I preserve?"** → settings.json → file_modification_guidelines

---

## Directory Structure

```
rag-type/.claude/
├── CLAUDE.md              ← Project guidance and context
├── conventions.md         ← Coding standards and style guide
├── settings.json          ← Claude Code configuration and rules
└── README.md              ← This file
```

Last updated: 2026-09-25
