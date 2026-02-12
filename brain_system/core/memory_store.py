
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class MemoryStore:
    def __init__(self, filepath: str = None):
        if filepath is None:
            # Store memory in the project root by default
            filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "brain_memory.json")
        self.filepath = os.path.abspath(filepath)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
        else:
            # Validate existing file is valid JSON
            try:
                with open(self.filepath, 'r') as f:
                    json.load(f)
            except (json.JSONDecodeError, ValueError):
                with open(self.filepath, 'w') as f:
                    json.dump([], f)

    def add_memory(self, memory_text: str, tags: List[str] = None):
        """Add a memory entry to LTM."""
        if tags is None:
            tags = []
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": memory_text,
            "tags": tags
        }
        
        try:
            with open(self.filepath, 'r+') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
        except (json.JSONDecodeError, ValueError):
            with open(self.filepath, 'w') as f:
                json.dump([entry], f, indent=4)

    def retrieve_memories(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Naive retrieval: simple keyword matching or just return recent memories.
        In a production system, this would use vector embeddings.
        """
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
        
        # Simple keyword match
        keywords = query.lower().split()
        relevant = []
        for entry in data:
            content = entry['content'].lower()
            score = sum(1 for k in keywords if k in content)
            if score > 0:
                relevant.append((score, entry))
        
        # Sort by relevance score, then recentness
        relevant.sort(key=lambda x: x[0], reverse=True)
        
        # If no keywords found, return most recent
        if not relevant:
            return data[-limit:]
            
        return [r[1] for r in relevant[:limit]]
