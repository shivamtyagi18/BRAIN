"""
ZVec-powered persona biography memory.

Indexes a persona's biography text or profile dict as semantic embeddings,
enabling the Memory Agent (Hippocampus) to retrieve relevant life experiences
by meaning rather than keyword matching.
"""

import os
import shutil
import uuid
from typing import List, Dict, Optional

try:
    import zvec
    ZVEC_AVAILABLE = True
except ImportError:
    ZVEC_AVAILABLE = False


class VectorMemory:
    """Semantic vector store for persona biography passages."""

    # Embedding dimension for the default Sentence Transformer model
    _EMBEDDING_DIM = 384

    def __init__(self, storage_dir: Optional[str] = None):
        if not ZVEC_AVAILABLE:
            raise ImportError(
                "zvec is required for VectorMemory. "
                "Install it with: pip install zvec"
            )

        self._storage_dir = storage_dir or os.path.join(
            os.getcwd(), ".brain_vector_store"
        )
        self._collection: Optional[zvec.Collection] = None
        self._embedder: Optional[zvec.DefaultLocalDenseEmbedding] = None

    def _get_embedder(self) -> "zvec.DefaultLocalDenseEmbedding":
        """Lazy-init the embedding model (downloads on first use)."""
        if self._embedder is None:
            self._embedder = zvec.DefaultLocalDenseEmbedding()
        return self._embedder

    def _create_collection(self, name: str) -> "zvec.Collection":
        """Create a new ZVec collection for a persona."""
        collection_path = os.path.join(self._storage_dir, name)

        # If collection already exists, remove it (re-indexing)
        if os.path.exists(collection_path):
            shutil.rmtree(collection_path)
        os.makedirs(self._storage_dir, exist_ok=True)

        schema = zvec.CollectionSchema(
            name=name,
            vectors=[
                zvec.VectorSchema(
                    "embedding",
                    data_type=zvec.DataType.VECTOR_FP32,
                    dimension=self._EMBEDDING_DIM,
                    index_param=zvec.HnswIndexParam(),
                )
            ],
            fields=[
                zvec.FieldSchema("chunk_text", zvec.DataType.STRING),
                zvec.FieldSchema("chunk_type", zvec.DataType.STRING),
            ],
        )
        return zvec.create_and_open(collection_path, schema)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_text(self, text: str, persona_name: str) -> int:
        """Chunk a biography text into paragraphs and index them.

        Returns the number of chunks indexed.
        """
        safe_name = persona_name.lower().replace(" ", "_")[:40]
        self._collection = self._create_collection(safe_name)
        embedder = self._get_embedder()

        # Split into paragraph-level chunks
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        docs = []
        for chunk in chunks:
            embedding = embedder.embed(chunk)
            doc = zvec.Doc(
                id=str(uuid.uuid4()),
                vectors={"embedding": embedding},
                fields={
                    "chunk_text": chunk,
                    "chunk_type": "biography",
                },
            )
            docs.append(doc)

        self._collection.insert(docs)
        self._collection.flush()

        print(f"📚 Indexed {len(docs)} biography passages for {persona_name}")
        return len(docs)

    def index_profile(self, profile: Dict[str, str], persona_name: str) -> int:
        """Index a pre-curated persona profile dict.

        Each profile field (BELIEFS, VALUES, etc.) becomes a searchable chunk.
        Returns the number of chunks indexed.
        """
        safe_name = persona_name.lower().replace(" ", "_")[:40]
        self._collection = self._create_collection(safe_name)
        embedder = self._get_embedder()

        docs = []
        for field, value in profile.items():
            if not value or not value.strip():
                continue
            text = f"{field}: {value}"
            embedding = embedder.embed(text)
            doc = zvec.Doc(
                id=str(uuid.uuid4()),
                vectors={"embedding": embedding},
                fields={
                    "chunk_text": text,
                    "chunk_type": f"profile_{field.lower()}",
                },
            )
            docs.append(doc)

        if docs:
            self._collection.insert(docs)
            self._collection.flush()

        print(f"📚 Indexed {len(docs)} profile fields for {persona_name}")
        return len(docs)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Semantic search over the indexed persona biography.

        Returns a list of relevant passage strings.
        """
        if self._collection is None:
            return []

        embedder = self._get_embedder()
        query_embedding = embedder.embed(query)

        results = self._collection.query(
            vectors=zvec.VectorQuery("embedding", vector=query_embedding),
            topk=top_k,
            output_fields=["chunk_text", "chunk_type"],
        )

        return [doc.field("chunk_text") for doc in results if doc.has_field("chunk_text")]

    def clear(self):
        """Clear the current persona index."""
        if self._collection is not None:
            self._collection.destroy()
            self._collection = None

    @property
    def is_loaded(self) -> bool:
        return self._collection is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk_text(text: str, min_length: int = 50) -> List[str]:
        """Split text into paragraph-level chunks.

        Splits on double newlines (paragraphs), then merges very short
        chunks with their neighbours so each chunk has enough context.
        """
        raw = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Merge short paragraphs
        merged: List[str] = []
        buffer = ""
        for para in raw:
            if buffer:
                buffer += " " + para
            else:
                buffer = para

            if len(buffer) >= min_length:
                merged.append(buffer)
                buffer = ""

        if buffer:
            if merged:
                merged[-1] += " " + buffer
            else:
                merged.append(buffer)

        return merged
