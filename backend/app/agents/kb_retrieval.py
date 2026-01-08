from app.agents.gemini_client import async_ask_gemini

class KnowledgeRetrievalAgent:
    """
    Advanced Simulated RAG (Retrieval Augmented Generation) Agent.
    In a production system, this would query a Vector DB (Pinecone/Milvus).
    Here, it uses specialized LLM context to 'retrieve' internal policy wisdom.
    """
    async def retrieve_context(self, category: str, query: str) -> str:
        prompt = f"""
        Act as a Knowledge Base Retrieval system. 
        Search internal company docs for: '{query}' in the {category} department.
        
        Provide 2-3 specific policy snippets or technical guidelines that are RELEVANT.
        Keep it brief and factual.
        """
        try:
            context = await async_ask_gemini(prompt)
            return context
        except:
            return "General company support guidelines apply."

kb_agent = KnowledgeRetrievalAgent()

async def get_kb_context(category: str, query: str):
    return await kb_agent.retrieve_context(category, query)
