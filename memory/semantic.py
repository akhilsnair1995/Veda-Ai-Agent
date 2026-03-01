# memory/semantic.py
# This is your chatbot's long-term semantic memory.
# It stores knowledge as mathematical "embeddings" so it can
# find relevant information based on meaning, not just keywords.

import chromadb
from pathlib import Path

# Use a relative path so it works on both Windows and WSL
BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = str(BASE_DIR / "memory" / "vectorstore")


class SemanticMemory:
    def __init__(self):
        # Connect to (or create) the persistent vector database
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

        # A "collection" is like a table in a regular database
        self.collection = self.client.get_or_create_collection(
            name="veda_knowledge",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity for search
        )
        self._id_counter = self.collection.count()

    def store(self, text: str, metadata: dict = None):
        """
        Store a piece of text in semantic memory.
        ChromaDB automatically converts it to an embedding vector.
        """
        self._id_counter += 1
        # Default metadata if empty or None
        if not metadata:
            metadata = {"source": "veda_memory"}
            
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[f"doc_{self._id_counter}"]
        )

    def search(self, query: str, top_k: int = 4) -> list[str]:
        """
        Search for semantically similar stored texts.
        Returns the most relevant pieces of knowledge for the given query.
        """
        if self.collection.count() == 0:
            return []  # Nothing stored yet

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )
        return results['documents'][0] if results['documents'] else []

    def store_note(self, title: str, content: str):
        """Store a note in semantic memory for retrieval."""
        self.store(
            text=f"Note titled '{title}': {content}",
            metadata={"type": "note", "title": title}
        )

    def store_conversation_summary(self, summary: str):
        """Store a summary of a past conversation."""
        self.store(
            text=summary,
            metadata={"type": "conversation_summary"}
        )
