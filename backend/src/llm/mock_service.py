"""
Enhanced Mock LLM service for demo purposes - provides realistic AI responses
"""
import asyncio
from typing import List, Dict, Any, AsyncGenerator
import random
import re
from datetime import datetime, timedelta

class MockLLMService:
    """Mock LLM service that simulates realistic OpenAI responses"""
    
    def __init__(self):
        self.response_templates = {
            'general': [
                "Based on your uploaded documents, I found several relevant pieces of information about {topic}.",
                "From analyzing your knowledge base, here's what I discovered regarding {topic}:",
                "I've searched through your documents and found some interesting insights about {topic}:",
                "Looking at the content you've uploaded, I can provide the following information about {topic}:",
            ],
            'temporal': [
                "Based on the timestamps in your documents, here's what happened {timeframe}:",
                "Looking at your recent uploads from {timeframe}, I found:",
                "From your documents dated {timeframe}, here are the key points:",
            ],
            'how_to': [
                "Based on your documents, here's a step-by-step approach:",
                "From the information in your knowledge base, here's how to proceed:",
                "Your uploaded content suggests the following methodology:",
            ],
            'summary': [
                "Here's a summary of the key points from your documents:",
                "The main themes I found across your uploaded content are:",
                "Synthesizing information from multiple sources, here are the highlights:",
            ]
        }
        
        self.context_responses = {
            'pdf': "From your PDF documents, I extracted the following information:",
            'audio': "Based on the audio transcripts in your knowledge base:",
            'text': "From your text files and notes:",
            'image': "Based on the text extracted from your images:",
            'web': "From the web content you've saved:"
        }
    
    def _extract_topic(self, query: str) -> str:
        """Extract the main topic from the query"""
        # Remove common question words
        topic = re.sub(r'\b(what|how|when|where|why|who|tell me about|explain|describe)\b', '', query.lower())
        topic = re.sub(r'\b(is|are|was|were|the|a|an)\b', '', topic)
        topic = topic.strip()
        return topic if topic else "this topic"
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query to provide appropriate response"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['last week', 'yesterday', 'last month', 'recently', 'when']):
            return 'temporal'
        elif any(word in query_lower for word in ['how to', 'how do', 'steps', 'process', 'method']):
            return 'how_to'
        elif any(word in query_lower for word in ['summarize', 'summary', 'overview', 'main points']):
            return 'summary'
        else:
            return 'general'
    
    async def generate_response(self,
                              query: str,
                              context_chunks: List[Dict[str, Any]],
                              conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate a realistic mock response"""
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        if not context_chunks:
            return """I don't have any relevant information in your knowledge base about this topic yet. 

To get started:
1. Upload some documents using the upload button
2. Wait for them to be processed 
3. Ask me questions about the content

I can help you find information from PDFs, Word docs, text files, audio recordings, and images once you upload them!"""
        
        # Build contextual response
        response_parts = []
        
        # Get query type and topic
        query_type = self._detect_query_type(query)
        topic = self._extract_topic(query)
        
        # Add opening based on query type
        if query_type == 'temporal':
            timeframe = "in your recent documents"
            if "last week" in query.lower():
                timeframe = "last week"
            elif "yesterday" in query.lower():
                timeframe = "yesterday"
            elif "last month" in query.lower():
                timeframe = "last month"
            
            opening = random.choice(self.response_templates['temporal']).format(timeframe=timeframe)
        else:
            opening = random.choice(self.response_templates[query_type]).format(topic=topic)
        
        response_parts.append(opening)
        
        # Add context from chunks
        if context_chunks:
            response_parts.append(f"\n\nI found {len(context_chunks)} relevant sources in your knowledge base:")
            
            for i, chunk in enumerate(context_chunks[:3]):
                title = chunk.get('title', f'Document {i+1}')
                source_type = chunk.get('source_type', 'document')
                content = chunk.get('content', '')
                
                # Create realistic content summary
                content_preview = content[:150] + "..." if len(content) > 150 else content
                relevance = chunk.get('relevance_score', random.uniform(0.7, 0.95))
                
                response_parts.append(f"\n**{i+1}. {title}** ({source_type.upper()}) - {relevance:.0%} match")
                response_parts.append(f"   {content_preview}")
        
        # Add query-specific insights
        if query_type == 'how_to':
            response_parts.append(f"\n\n**Step-by-step approach based on your documents:**")
            response_parts.append("1. Review the foundational concepts mentioned in your sources")
            response_parts.append("2. Follow the methodology outlined in your uploaded materials")
            response_parts.append("3. Apply the best practices identified across multiple documents")
        
        elif query_type == 'temporal':
            response_parts.append(f"\n\n**Timeline insights:**")
            response_parts.append("• Most relevant information appears in your recently uploaded documents")
            response_parts.append("• Key developments are documented across multiple sources")
            response_parts.append("• Consider reviewing related materials from the same time period")
        
        elif query_type == 'summary':
            response_parts.append(f"\n\n**Key themes identified:**")
            response_parts.append("• Consistent patterns across multiple document sources")
            response_parts.append("• Important connections between different pieces of content")
            response_parts.append("• Actionable insights derived from your knowledge base")
        
        # Add helpful closing
        response_parts.append(f"\n\n💡 **Want to explore further?** Try asking about specific aspects of {topic} or upload more related documents to expand your knowledge base!")
        
        return "".join(response_parts)
    
    async def generate_response_stream(self,
                                     query: str,
                                     context_chunks: List[Dict[str, Any]],
                                     conversation_history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
        """Generate streaming mock response with realistic typing speed"""
        
        response = await self.generate_response(query, context_chunks, conversation_history)
        
        # Stream the response with realistic typing patterns
        words = response.split()
        for i, word in enumerate(words):
            # Vary typing speed for realism
            if word.startswith('**') or word.startswith('#'):
                await asyncio.sleep(0.1)  # Pause before headers
            elif word.endswith('.') or word.endswith('!') or word.endswith('?'):
                await asyncio.sleep(0.08)  # Pause after sentences
            elif word.endswith(','):
                await asyncio.sleep(0.04)  # Brief pause after commas
            else:
                await asyncio.sleep(random.uniform(0.02, 0.06))  # Normal typing
            
            if i == 0:
                yield word
            else:
                yield " " + word
    
    async def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a realistic summary"""
        await asyncio.sleep(0.5)
        
        if len(content) <= max_length:
            return content
        
        # Create a more intelligent summary
        sentences = content.split('. ')
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) < max_length - 20:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        summary = '. '.join(summary_sentences)
        if not summary.endswith('.'):
            summary += '.'
        
        return summary + " [AI-generated summary]"
    
    async def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract realistic keywords"""
        await asyncio.sleep(0.3)
        
        # More sophisticated keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Common words to exclude
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know', 
            'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 
            'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 
            'such', 'take', 'than', 'them', 'well', 'were', 'what', 'your',
            'about', 'after', 'again', 'before', 'being', 'between', 'both',
            'during', 'each', 'few', 'more', 'most', 'other', 'same', 'should',
            'through', 'under', 'until', 'while', 'would', 'could', 'might'
        }
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most frequent words
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]