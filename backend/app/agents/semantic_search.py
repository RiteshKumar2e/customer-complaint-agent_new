"""
Semantic Similarity using Sentence Transformers
Uses all-MiniLM-L6-v2: Fast, lightweight, unlimited usage
Perfect for finding similar complaints and pattern matching
"""
from sentence_transformers import SentenceTransformer, util
import logging
import numpy as np

class SemanticSimilarityEngine:
    def __init__(self):
        try:
            # all-MiniLM-L6-v2: 80MB model, 5x faster than BERT, 384-dim embeddings
            # Why? Optimized for semantic search with minimal resource usage
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logging.info("✅ Sentence Transformer Model Loaded")
            
            # Cache for historical complaint embeddings
            self.complaint_cache = []
            self.embedding_cache = []
        except Exception as e:
            logging.error(f"Failed to load sentence transformer: {e}")
            self.model = None

    def find_similar(self, query: str, candidates: list, top_k: int = 3) -> list:
        """
        Find most similar texts from candidates
        Returns: List of (text, similarity_score) tuples
        """
        if not self.model or not query or not candidates:
            return []
        
        try:
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            candidate_embeddings = self.model.encode(candidates, convert_to_tensor=True)
            
            # Compute cosine similarities
            similarities = util.cos_sim(query_embedding, candidate_embeddings)[0]
            
            # Get top-k results
            top_results = []
            for idx in similarities.argsort(descending=True)[:top_k]:
                if similarities[idx] > 0.3:  # Minimum similarity threshold
                    top_results.append({
                        "text": candidates[idx],
                        "similarity": float(similarities[idx])
                    })
            
            return top_results
        except Exception as e:
            logging.error(f"Similarity search error: {e}")
            return []

    def add_to_cache(self, complaint: str):
        """Add complaint to historical cache for future similarity searches"""
        if self.model and complaint:
            try:
                embedding = self.model.encode(complaint)
                self.complaint_cache.append(complaint)
                self.embedding_cache.append(embedding)
            except:
                pass

# Global instance
similarity_engine = SemanticSimilarityEngine()

def find_similar_complaints_local(query: str, candidates: list = None, top_k: int = 3):
    """Find similar complaints using local semantic search"""
    if candidates is None:
        candidates = similarity_engine.complaint_cache
    return similarity_engine.find_similar(query, candidates, top_k)

def cache_complaint(complaint: str):
    """Cache complaint for future similarity matching"""
    similarity_engine.add_to_cache(complaint)
