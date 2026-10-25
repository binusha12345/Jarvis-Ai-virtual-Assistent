import os
import chromadb
from chromadb.utils import embedding_functions
from core.config import KNOWLEDGE_DIR, VECTOR_DIR, EMBEDDING_MODEL

_client = None
_collection = None

def _init_db():
    global _client, _collection
    if _collection: return _collection
    _client = chromadb.PersistentClient(path=VECTOR_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    _collection = _client.get_or_create_collection(name="jarvis_knowledge", embedding_function=ef)
    return _collection

def _extract_text(filepath):
    try:
        if filepath.endswith(".txt") or filepath.endswith(".md"):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif filepath.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join([p.extract_text() or "" for p in reader.pages])
        elif filepath.endswith(".docx"):
            from docx import Document
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""
    return ""

def _chunk(text, size=500):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

def ingest_knowledge():
    col = _init_db()
    existing = set(col.get()["ids"])
    added = 0
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for f in files:
            if f.lower().endswith((".txt", ".md", ".pdf", ".docx")):
                fp = os.path.join(root, f)
                text = _extract_text(fp)
                if not text: continue
                for i, chunk in enumerate(_chunk(text)):
                    doc_id = f"{f}_{i}"
                    if doc_id in existing: continue
                    col.add(documents=[chunk], ids=[doc_id], metadatas=[{"source": f}])
                    added += 1
    return added

def rag_query(question, top_k=3):
    try:
        col = _init_db()
        results = col.query(query_texts=[question], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        return "\n---\n".join(docs) if docs else "No relevant documents found."
    except Exception as e:
        return f"RAG error: {str(e)}"