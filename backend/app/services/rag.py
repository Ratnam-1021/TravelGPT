import os
import glob
from typing import List, Dict, Any
from app.config import settings

class RAGService:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self._initialize_vector_db()

    def _initialize_vector_db(self):
        """Initialize ChromaDB client and auto-ingest data guides & policies."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Persistent ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="travel_guides_and_policies"
            )
            
            # Auto ingest markdown files if collection is empty
            if self.collection.count() == 0:
                self.ingest_data_files()
        except Exception as e:
            print(f"[RAG] Warning: ChromaDB initialization error ({e}). Using in-memory store fallback.")
            self.collection = None

    def ingest_data_files(self):
        """Read all guides and policy markdown files and add to vector database."""
        docs = []
        metadatas = []
        ids = []

        data_dir = settings.DATA_DIR
        markdown_files = glob.glob(os.path.join(data_dir, "**/*.md"), recursive=True)

        for i, file_path in enumerate(markdown_files):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                rel_path = os.path.relpath(file_path, data_dir)
                # Split content into sections by headers (##)
                chunks = self._chunk_markdown(content, rel_path)
                
                for j, (chunk_text, chunk_meta) in enumerate(chunks):
                    doc_id = f"doc_{i}_{j}_{os.path.basename(file_path)}"
                    docs.append(chunk_text)
                    metadatas.append(chunk_meta)
                    ids.append(doc_id)
            except Exception as ex:
                print(f"[RAG] Error reading {file_path}: {ex}")

        if docs and self.collection is not None:
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[RAG] Successfully ingested {len(docs)} document chunks into ChromaDB.")

    def _chunk_markdown(self, text: str, source: str) -> List[tuple]:
        """Split markdown file by headers into coherent chunks."""
        sections = text.split("\n## ")
        chunks = []
        title = sections[0].replace("# ", "").strip() if sections else source

        for sec in sections:
            if not sec.strip():
                continue
            header = sec.split("\n")[0].strip()
            chunk_content = f"Source: {source} ({header})\n" + sec
            chunks.append((chunk_content, {"source": source, "title": header, "doc_title": title}))
        
        return chunks

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search vector store for relevant travel context."""
        results = []
        
        if self.collection is not None and self.collection.count() > 0:
            try:
                query_res = self.collection.query(
                    query_texts=[query],
                    n_results=min(top_k, self.collection.count())
                )
                
                documents = query_res.get("documents", [[]])[0]
                metadatas = query_res.get("metadatas", [[]])[0]
                distances = query_res.get("distances", [[]])[0] if "distances" in query_res else [0.5]*len(documents)
                
                for doc, meta, dist in zip(documents, metadatas, distances):
                    # Higher distance means lower similarity score in Chroma default L2/cosine
                    relevance = round(max(0.0, 1.0 - (dist if isinstance(dist, float) else 0.5)), 2)
                    results.append({
                        "source": meta.get("source", "Guide"),
                        "content": doc,
                        "relevance_score": relevance
                    })
                return results
            except Exception as e:
                print(f"[RAG] Vector search error: {e}")

        # Fallback text search if vector DB has an issue
        return self._keyword_search_fallback(query, top_k)

    def _keyword_search_fallback(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback search reading local markdown files."""
        results = []
        data_dir = settings.DATA_DIR
        markdown_files = glob.glob(os.path.join(data_dir, "**/*.md"), recursive=True)
        query_words = set(query.lower().split())

        for file_path in markdown_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                rel_path = os.path.relpath(file_path, data_dir)
                score = sum(1 for word in query_words if word in content.lower())
                if score > 0:
                    results.append({
                        "source": rel_path,
                        "content": content[:800] + "...",
                        "relevance_score": min(0.9, 0.3 + score * 0.1)
                    })
            except Exception:
                pass

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

rag_service = RAGService()
