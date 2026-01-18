from app.services.rag_engine import rag_engine

class KnowledgeRetrievalAgent:
    """
    Advanced RAG (Retrieval Augmented Generation) Agent.
    Now uses a real document retrieval system with vector similarity.
    """
    async def retrieve_context(self, category: str, query: str) -> str:
        # We search with combined category and query for better precision
        search_query = f"{category} {query}"
        try:
            # The rag_engine is synchronous but we keep the method async for pipeline compatibility
            context = rag_engine.retrieve(search_query)
            return context
        except Exception as e:
            print(f"RAG Error: {e}")
            return "General company support guidelines apply."

kb_agent = KnowledgeRetrievalAgent()

async def get_kb_context(category: str, query: str):
    return await kb_agent.retrieve_context(category, query)
