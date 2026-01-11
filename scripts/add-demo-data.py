#!/usr/bin/env python3
"""
Add demo data to the Second Brain system for testing
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
import uuid

# Add the backend src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from storage.database import AsyncSessionLocal
from storage.models import Document, Chunk
from ingestion.embedder import EmbeddingGenerator
from ingestion.chunker import IntelligentChunker

# Sample documents
DEMO_DOCUMENTS = [
    {
        "title": "Machine Learning Fundamentals",
        "content": """Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. 

Key concepts include:
- Supervised learning: Learning from labeled examples
- Unsupervised learning: Finding patterns in unlabeled data  
- Reinforcement learning: Learning through trial and error

Popular algorithms include linear regression, decision trees, neural networks, and support vector machines. The field has applications in computer vision, natural language processing, and predictive analytics.""",
        "source_type": "text",
        "author": "AI Research Team"
    },
    {
        "title": "Project Management Best Practices",
        "content": """Effective project management requires careful planning and execution. Here are key principles:

1. Define clear objectives and scope
2. Create detailed project timelines
3. Identify and manage risks early
4. Maintain regular communication with stakeholders
5. Monitor progress and adjust as needed

Agile methodologies like Scrum have become popular for software development projects. They emphasize iterative development, frequent feedback, and adaptability to change.""",
        "source_type": "pdf",
        "author": "Project Management Institute"
    },
    {
        "title": "Meeting Notes - Q4 Planning",
        "content": """Meeting Date: Last Tuesday
Attendees: Sarah, Mike, Jennifer, Alex

Key Discussion Points:
- Q4 revenue targets looking strong, up 15% from last quarter
- New product launch scheduled for November
- Marketing campaign needs additional budget approval
- Engineering team requests 2 additional developers
- Customer feedback has been overwhelmingly positive

Action Items:
- Sarah: Prepare budget proposal by Friday
- Mike: Interview candidates for engineering roles
- Jennifer: Finalize marketing materials
- Alex: Schedule customer success review

Next meeting: Next Tuesday at 2 PM""",
        "source_type": "text",
        "created_at": datetime.now() - timedelta(days=5)
    },
    {
        "title": "Quantum Computing Overview",
        "content": """Quantum computing represents a paradigm shift in computational power. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or qubits that can exist in superposition.

Key principles:
- Superposition: Qubits can be in multiple states simultaneously
- Entanglement: Qubits can be correlated in ways that classical physics cannot explain
- Quantum interference: Allows quantum algorithms to amplify correct answers

Applications include:
- Cryptography and security
- Drug discovery and molecular modeling
- Financial modeling and optimization
- Machine learning acceleration

Major players include IBM, Google, Microsoft, and various startups. The field is still in early stages but shows tremendous promise.""",
        "source_type": "pdf",
        "author": "Quantum Research Lab"
    },
    {
        "title": "Audio Transcript - Team Standup",
        "content": """Speaker 1: Good morning everyone, let's start with our daily standup. Sarah, what did you work on yesterday?

Speaker 2: I finished the user authentication module and started working on the dashboard components. Today I'll be focusing on the data visualization charts.

Speaker 1: Great progress. Mike, how about you?

Speaker 3: I completed the API integration for the payment system. Had some issues with the webhook configuration but got it sorted out. Today I'm tackling the notification service.

Speaker 1: Excellent. Any blockers or concerns?

Speaker 2: I might need some help with the chart library integration. The documentation is a bit unclear.

Speaker 3: I can help with that after lunch. I've used that library before.

Speaker 1: Perfect. Let's reconvene if any urgent issues come up. Have a productive day everyone!""",
        "source_type": "audio",
        "created_at": datetime.now() - timedelta(days=2)
    }
]

async def add_demo_data():
    """Add demo documents and chunks to the database"""
    
    print("🎭 Adding demo data to Second Brain...")
    
    # Initialize services
    embedder = EmbeddingGenerator()
    chunker = IntelligentChunker()
    
    async with AsyncSessionLocal() as db:
        for doc_data in DEMO_DOCUMENTS:
            print(f"   Adding: {doc_data['title']}")
            
            # Create document
            document = Document(
                source_path=f"demo/{doc_data['title'].lower().replace(' ', '_')}.txt",
                source_type=doc_data['source_type'],
                title=doc_data['title'],
                author=doc_data.get('author'),
                created_at=doc_data.get('created_at', datetime.now()),
                processing_status='completed',
                metadata={'demo': True, 'source': 'demo_script'}
            )
            
            db.add(document)
            await db.flush()  # Get the document ID
            
            # Chunk the content
            chunks_data = chunker.chunk_content(
                doc_data['content'],
                source_type=doc_data['source_type'],
                metadata={'title': doc_data['title']}
            )
            
            # Create chunks with embeddings
            for i, chunk_data in enumerate(chunks_data):
                embedding = embedder.generate_embedding(chunk_data['content'])
                
                chunk = Chunk(
                    document_id=document.id,
                    content=chunk_data['content'],
                    chunk_index=i,
                    token_count=chunk_data.get('token_count', len(chunk_data['content'].split())),
                    embedding=embedding,
                    metadata=chunk_data.get('metadata', {})
                )
                db.add(chunk)
            
        await db.commit()
    
    print("✅ Demo data added successfully!")
    print("🚀 You can now ask questions like:")
    print("   • 'What did we discuss in last Tuesday's meeting?'")
    print("   • 'Tell me about machine learning'")
    print("   • 'What are the key principles of quantum computing?'")
    print("   • 'Summarize our project management practices'")

if __name__ == "__main__":
    asyncio.run(add_demo_data())