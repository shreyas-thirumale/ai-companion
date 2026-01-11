import openai
from typing import List, Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from src.config import settings

logger = logging.getLogger(__name__)

# Check if we should use mock service
USE_MOCK = not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here"

if USE_MOCK:
    logger.warning("Using mock LLM service - set OPENAI_API_KEY for full functionality")
    from .mock_service import MockLLMService
    LLMService = MockLLMService
else:
    # Configure OpenAI
    import openai
    openai.api_key = settings.openai_api_key
    logger.info("Using real OpenAI LLM service")

    class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_response(self,
                              query: str,
                              context_chunks: List[Dict[str, Any]],
                              conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate response using LLM"""
        
        # Build context from chunks
        context = self._build_context(context_chunks)
        
        # Build conversation history
        messages = self._build_messages(query, context, conversation_history)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheaper alternative for development
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    async def generate_response_stream(self,
                                     query: str,
                                     context_chunks: List[Dict[str, Any]],
                                     conversation_history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response using LLM"""
        
        # Build context from chunks
        context = self._build_context(context_chunks)
        
        # Build conversation history
        messages = self._build_messages(query, context, conversation_history)
        
        try:
            stream = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheaper alternative for development
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _build_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks"""
        
        if not context_chunks:
            return "No relevant information found in your knowledge base."
        
        context_parts = []
        
        for i, chunk in enumerate(context_chunks[:5]):  # Limit to top 5 chunks
            source_info = f"Source: {chunk.get('title', 'Unknown')} ({chunk.get('source_type', 'unknown')})"
            if chunk.get('created_at'):
                created_date = chunk['created_at']
                if isinstance(created_date, str):
                    created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                source_info += f" - {created_date.strftime('%Y-%m-%d')}"
            
            content = chunk.get('content', '').strip()
            if len(content) > 500:
                content = content[:500] + "..."
            
            context_parts.append(f"[{i+1}] {source_info}\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _build_messages(self,
                       query: str,
                       context: str,
                       conversation_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        
        system_prompt = """You are a helpful AI assistant that acts as a "second brain" for the user. You have access to the user's personal knowledge base containing documents, notes, audio transcripts, web content, and images they've saved.

Your role is to:
1. Answer questions based on the provided context from their knowledge base
2. Synthesize information from multiple sources when relevant
3. Be conversational and helpful, like talking to a knowledgeable friend
4. Acknowledge when information isn't available in their knowledge base
5. Reference specific sources when providing information
6. Maintain context from previous conversations when relevant

Guidelines:
- Always base your answers on the provided context
- If the context doesn't contain relevant information, say so clearly
- When referencing information, mention the source (document title, date, etc.)
- Be concise but comprehensive
- Use a friendly, conversational tone
- If asked about temporal information (like "last week"), pay attention to dates in the context"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append(msg)
        
        # Add current query with context
        user_message = f"""Context from my knowledge base:
{context}

Question: {query}"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a summary of content"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Summarize the following content in {max_length} characters or less. Be concise but capture the key points."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content
    
    async def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Extract up to {max_keywords} important keywords or phrases from the following content. Return them as a comma-separated list."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            keywords_text = response.choices[0].message.content
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []