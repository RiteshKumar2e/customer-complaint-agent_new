import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

class RAGEngine:
    """
    Real RAG (Retrieval Augmented Generation) Engine.
    Uses TF-IDF Vectorization and Cosine Similarity to find relevant company policies.
    """
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.kb_data = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.load_kb()

    def load_kb(self):
        """Load and index the knowledge base"""
        if not os.path.exists(self.kb_path):
            print(f"⚠️ KB path {self.kb_path} not found.")
            return

        try:
            with open(self.kb_path, 'r') as f:
                self.kb_data = json.load(f)
            
            # Combine category, topic and content for indexing
            documents = [
                f"{doc['category']} {doc['topic']} {doc['content']}" 
                for doc in self.kb_data
            ]
            
            if documents:
                self.tfidf_matrix = self.vectorizer.fit_transform(documents)
                print(f"✅ RAG Engine: Indexed {len(documents)} documents.")
        except Exception as e:
            print(f"❌ RAG Initialization Error: {e}")

    def retrieve(self, query: str, top_k: int = 2) -> str:
        """Retrieve most relevant policy snippets"""
        if self.tfidf_matrix is None or not self.kb_data:
            return "General company support guidelines apply."

        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1: # Threshold for relevance
                    doc = self.kb_data[idx]
                    results.append(f"[{doc['topic']}]: {doc['content']}")
            
            if not results:
                return "No specific internal policy matched. Use general professional judgment."
                
            return "\n\n".join(results)
        except Exception as e:
            print(f"❌ RAG Retrieval Error: {e}")
            return "General company support guidelines apply."

# Initialize the global RAG instance
kb_file = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "policies.json")
rag_engine = RAGEngine(kb_file)
