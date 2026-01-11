#!/usr/bin/env python3
"""
Quick demo of the Second Brain AI Companion - No Docker needed!
This shows the core functionality without all the setup complexity.
"""

import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any

class QuickDemo:
    def __init__(self):
        self.documents = [
            {
                "id": "1",
                "title": "Machine Learning Fundamentals",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. Key concepts include supervised learning, unsupervised learning, and reinforcement learning.",
                "source_type": "pdf",
                "created_at": "2024-01-08T10:00:00Z"
            },
            {
                "id": "2", 
                "title": "Meeting Notes - Q4 Planning",
                "content": "Meeting Date: Last Tuesday. Key points: Q4 revenue targets up 15%, new product launch in November, marketing needs budget approval, engineering team requests 2 developers.",
                "source_type": "text",
                "created_at": "2024-01-05T14:30:00Z"
            },
            {
                "id": "3",
                "title": "Project Management Best Practices", 
                "content": "Effective project management requires: 1) Clear objectives 2) Detailed timelines 3) Risk management 4) Stakeholder communication 5) Progress monitoring. Agile methodologies like Scrum are popular.",
                "source_type": "pdf",
                "created_at": "2024-01-07T09:15:00Z"
            }
        ]
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword-based search simulation"""
        results = []
        query_words = query.lower().split()
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            
            # Calculate simple relevance score
            score = 0
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word) * 2
                if word in title_lower:
                    score += title_lower.count(word) * 3
            
            if score > 0:
                results.append({
                    **doc,
                    "relevance_score": min(score / 10, 1.0),
                    "excerpt": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:3]
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate AI-like response based on context"""
        
        if not context_docs:
            return "I don't have any relevant information in your knowledge base about this topic. Try uploading some documents first!"
        
        # Detect query type
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['last week', 'tuesday', 'meeting', 'discussed']):
            response = f"Based on your meeting notes, here's what was discussed:\n\n"
            for doc in context_docs:
                if 'meeting' in doc['title'].lower():
                    response += f"From '{doc['title']}':\n{doc['excerpt']}\n\n"
            response += "The key action items and decisions are outlined above."
            
        elif any(word in query_lower for word in ['machine learning', 'ml', 'algorithms']):
            response = f"Here's what I found about machine learning in your documents:\n\n"
            for doc in context_docs:
                if 'machine learning' in doc['content'].lower():
                    response += f"From '{doc['title']}':\n{doc['excerpt']}\n\n"
            response += "This covers the fundamental concepts and approaches in machine learning."
            
        elif any(word in query_lower for word in ['project management', 'project', 'management']):
            response = f"Based on your project management resources:\n\n"
            for doc in context_docs:
                if 'project' in doc['title'].lower():
                    response += f"From '{doc['title']}':\n{doc['excerpt']}\n\n"
            response += "These are proven methodologies for successful project execution."
            
        else:
            response = f"I found {len(context_docs)} relevant sources in your knowledge base:\n\n"
            for i, doc in enumerate(context_docs, 1):
                response += f"**{i}. {doc['title']}** ({doc['source_type'].upper()}) - {doc['relevance_score']:.0%} match\n"
                response += f"   {doc['excerpt']}\n\n"
            response += "💡 **Want to explore further?** Ask me more specific questions about these topics!"
        
        return response
    
    def stream_response(self, response: str):
        """Simulate streaming response like real AI"""
        words = response.split()
        for i, word in enumerate(words):
            print(word, end='', flush=True)
            if i < len(words) - 1:
                print(' ', end='', flush=True)
            
            # Vary typing speed for realism
            if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                time.sleep(0.1)  # Pause after sentences
            elif word.endswith(','):
                time.sleep(0.05)  # Brief pause after commas
            else:
                time.sleep(random.uniform(0.02, 0.08))  # Normal typing
        print('\n')

def main():
    print("🧠 Second Brain AI Companion - Quick Demo")
    print("=" * 50)
    print("This demo shows the core functionality without Docker setup!")
    print("Sample documents loaded: Machine Learning, Meeting Notes, Project Management")
    print("\nTry asking:")
    print("• 'What did we discuss in last Tuesday's meeting?'")
    print("• 'Tell me about machine learning'") 
    print("• 'What are project management best practices?'")
    print("• 'Summarize my documents'")
    print("\nType 'quit' to exit\n")
    
    demo = QuickDemo()
    
    while True:
        try:
            query = input("🤔 Ask me anything: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for trying the Second Brain demo!")
                break
            
            if not query:
                continue
            
            print("\n🔍 Searching your knowledge base...")
            time.sleep(0.5)  # Simulate search time
            
            # Search documents
            results = demo.search_documents(query)
            
            if results:
                print(f"✅ Found {len(results)} relevant sources")
                time.sleep(0.3)
                
                # Show sources
                print("\n📚 **Sources:**")
                for doc in results:
                    print(f"   • {doc['title']} ({doc['relevance_score']:.0%} match)")
                
                print("\n🤖 **AI Response:**")
                time.sleep(0.5)
                
                # Generate and stream response
                response = demo.generate_response(query, results)
                demo.stream_response(response)
            else:
                print("❌ No relevant documents found for your query.")
                print("💡 Try asking about: machine learning, meetings, or project management")
            
            print("\n" + "-" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for trying the Second Brain demo!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()