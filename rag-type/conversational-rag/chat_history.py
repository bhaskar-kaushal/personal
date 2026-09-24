"""
Chat history management for conversational RAG.

Provides:
  - ChatSession  : per-session history with timestamps
  - ChatHistoryManager : create, retrieve, list, export sessions

Example usage:
    python chat_history.py --export demo_session
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# Single session
# ---------------------------------------------------------------------------

class ChatSession:
    """Stores the message history and metadata for one chat session."""

    def __init__(self, session_id: str, persist_dir: str = "data/chat_sessions"):
        self.session_id = session_id
        self.persist_dir = persist_dir
        self.messages: List[Dict] = []
        self.created_at: str = datetime.utcnow().isoformat()
        self.updated_at: str = self.created_at

        # Attempt to load an existing session from disk
        self._load()

    # ------------------------------------------------------------------
    # Message management
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str) -> Dict:
        """
        Append a message to the session.

        Args:
            role: 'user', 'assistant', or 'system'
            content: Message text

        Returns:
            dict: The appended message entry
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.messages.append(entry)
        self.updated_at = entry["timestamp"]
        self._save()
        return entry

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Return messages in the format expected by the LLM (role + content only)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self):
        """Remove all messages (reset the session)."""
        self.messages = []
        self.updated_at = datetime.utcnow().isoformat()
        self._save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @property
    def _file_path(self) -> Path:
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        return Path(self.persist_dir) / f"{self.session_id}.json"

    def _save(self):
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
        }
        self._file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self):
        if self._file_path.exists():
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
            self.created_at = data.get("created_at", self.created_at)
            self.updated_at = data.get("updated_at", self.updated_at)
            self.messages = data.get("messages", [])

    def export_json(self, output_path: Optional[str] = None) -> str:
        """
        Export the session as a JSON file.

        Args:
            output_path: Where to write; defaults to persist_dir/<session_id>_export.json

        Returns:
            str: Path of the exported file
        """
        if output_path is None:
            output_path = str(
                Path(self.persist_dir) / f"{self.session_id}_export.json"
            )
        Path(output_path).write_text(
            json.dumps(
                {
                    "session_id": self.session_id,
                    "created_at": self.created_at,
                    "updated_at": self.updated_at,
                    "message_count": len(self.messages),
                    "messages": self.messages,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return output_path

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"ChatSession(id={self.session_id!r}, messages={len(self.messages)})"


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------

class ChatHistoryManager:
    """Manage multiple chat sessions."""

    def __init__(self, persist_dir: str = "data/chat_sessions"):
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Retrieve an existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id, self.persist_dir)
        return self._sessions[session_id]

    def list_sessions(self) -> List[Dict]:
        """Return metadata for all persisted sessions."""
        sessions = []
        for fp in Path(self.persist_dir).glob("*.json"):
            if fp.stem.endswith("_export"):
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                sessions.append(
                    {
                        "session_id": data.get("session_id"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "message_count": len(data.get("messages", [])),
                    }
                )
            except Exception:
                pass
        return sorted(sessions, key=lambda s: s.get("updated_at", ""), reverse=True)

    def delete_session(self, session_id: str):
        """Delete a session from memory and disk."""
        self._sessions.pop(session_id, None)
        fp = Path(self.persist_dir) / f"{session_id}.json"
        if fp.exists():
            fp.unlink()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat history management")
    parser.add_argument("--export", metavar="SESSION_ID", help="Export a session to JSON")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    args = parser.parse_args()

    manager = ChatHistoryManager()

    if args.list:
        sessions = manager.list_sessions()
        if not sessions:
            print("No sessions found.")
        for s in sessions:
            print(f"  {s['session_id']}  |  {s['message_count']} msgs  |  updated {s['updated_at']}")

    elif args.export:
        session = manager.get_or_create_session(args.export)
        path = session.export_json()
        print(f"✅ Session exported to: {path}")

    else:
        # Demo
        manager2 = ChatHistoryManager()
        sess = manager2.get_or_create_session("demo_session")
        sess.clear()
        sess.add_message("user", "What is RAG?")
        sess.add_message("assistant", "RAG stands for Retrieval-Augmented Generation.")
        sess.add_message("user", "Can you elaborate?")
        sess.add_message("assistant", "Sure! RAG combines a retrieval step with an LLM generation step.")
        print(f"Demo session: {sess}")
        for m in sess.messages:
            print(f"  [{m['role']}] {m['content'][:60]}")
