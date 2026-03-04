"""
ZVec-powered persona biography memory.

Indexes a persona's biography text or profile dict as semantic embeddings,
enabling the Memory Agent (Hippocampus) to retrieve relevant life experiences
by meaning rather than keyword matching.
"""

import os
import re
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

    # Chunking parameters for full books
    CHUNK_SIZE = 500        # target characters per chunk
    CHUNK_OVERLAP = 50      # overlap between consecutive chunks
    BATCH_SIZE = 100        # insert batch size for large documents

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
        """Chunk a biography text and index it for semantic search.

        Handles full books (500+ pages) with sentence-aware chunking.
        Returns the number of chunks indexed.
        """
        safe_name = persona_name.lower().replace(" ", "_")[:40]
        self._collection = self._create_collection(safe_name)
        embedder = self._get_embedder()

        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        total = len(chunks)
        indexed = 0

        # Insert in batches (efficient for large books)
        for batch_start in range(0, total, self.BATCH_SIZE):
            batch_chunks = chunks[batch_start:batch_start + self.BATCH_SIZE]
            docs = []
            for chunk in batch_chunks:
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
            indexed += len(docs)
            print(f"  📖 Indexed {indexed}/{total} passages...", end="\r")

        self._collection.flush()
        print(f"📚 Indexed {total} biography passages for {persona_name}  ")
        return total

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
    def _chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """Sentence-aware fixed-size chunking for full books.

        Strategy:
        1. Split text into sentences using regex.
        2. Group sentences into chunks of ~chunk_size characters.
        3. Overlap consecutive chunks by ~overlap characters to
           preserve context at boundaries.

        Handles PDFs that extract as continuous text (no paragraph
        breaks) as well as well-formatted text with paragraphs.
        """
        # Normalize whitespace (PDFs often have weird spacing)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        # Split into sentences — handles Mr./Mrs./Dr. abbreviations
        sentences = re.split(
            r"(?<=[.!?])\s+(?=[A-Z\"\'\u201c(])",
            text,
        )

        # Build chunks by grouping sentences
        chunks: List[str] = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence exceeds chunk_size, finalize chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
                chunks.append(current_chunk.strip())

                # Start next chunk with overlap from the end of this chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    # Take the last ~overlap chars, starting from a word boundary
                    tail = current_chunk[-overlap:]
                    word_start = tail.find(" ")
                    if word_start != -1:
                        current_chunk = tail[word_start + 1:] + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Filter out very short chunks (less than 30 chars)
        chunks = [c for c in chunks if len(c) >= 30]

        return chunks
