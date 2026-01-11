#!/usr/bin/env python3
"""
Test script to verify the improved search relevance scoring
"""

import asyncio
import requests
import json

# Test queries that should NOT match the Machine Learning document
test_queries = [
    "weather forecast",
    "cooking recipes", 
    "travel plans",
    "shopping list",
    "birthday party",
    "car maintenance",
    "gardening tips",
    "movie recommendations",
    "music playlist",
    "exercise routine"
]

# Test queries that SHOULD match the Machine Learning document
relevant_queries = [
    "machine learning",
    "artificial intelligence", 
    "neural networks",
    "supervised learning",
    "algorithms",
    "data science",
    "AI fundamentals"
]

async def test_search_query(query):
    """Test a single search query"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/query",
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get("sources", [])
            
            print(f"\n🔍 Query: '{query}'")
            print(f"📊 Found {len(sources)} results")
            
            for i, source in enumerate(sources, 1):
                title = source.get("title", "Unknown")
                relevance = source.get("relevance_score", 0)
                print(f"  {i}. {title} - {relevance:.1%} relevance")
            
            # Check if Machine Learning document appears
            ml_doc_found = any("Machine Learning" in source.get("title", "") for source in sources)
            return ml_doc_found, len(sources), sources
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False, 0, []
            
    except Exception as e:
        print(f"❌ Error testing query '{query}': {e}")
        return False, 0, []

async def main():
    print("🧪 Testing Search Relevance Improvements")
    print("=" * 50)
    
    # Test irrelevant queries
    print("\n🚫 Testing IRRELEVANT queries (should NOT return ML document):")
    irrelevant_matches = 0
    
    for query in test_queries:
        ml_found, result_count, sources = await test_search_query(query)
        if ml_found:
            irrelevant_matches += 1
            print(f"  ⚠️ PROBLEM: ML document appeared for irrelevant query!")
    
    print(f"\n📈 Irrelevant query results:")
    print(f"  - ML document appeared in {irrelevant_matches}/{len(test_queries)} irrelevant queries")
    print(f"  - Success rate: {((len(test_queries) - irrelevant_matches) / len(test_queries)) * 100:.1f}%")
    
    # Test relevant queries
    print("\n✅ Testing RELEVANT queries (should return ML document):")
    relevant_matches = 0
    
    for query in relevant_queries:
        ml_found, result_count, sources = await test_search_query(query)
        if ml_found:
            relevant_matches += 1
        else:
            print(f"  ⚠️ PROBLEM: ML document missing for relevant query!")
    
    print(f"\n📈 Relevant query results:")
    print(f"  - ML document appeared in {relevant_matches}/{len(relevant_queries)} relevant queries")
    print(f"  - Success rate: {(relevant_matches / len(relevant_queries)) * 100:.1f}%")
    
    # Overall assessment
    print(f"\n🎯 Overall Assessment:")
    total_correct = (len(test_queries) - irrelevant_matches) + relevant_matches
    total_queries = len(test_queries) + len(relevant_queries)
    overall_accuracy = (total_correct / total_queries) * 100
    
    print(f"  - Overall accuracy: {overall_accuracy:.1f}%")
    
    if overall_accuracy >= 90:
        print("  ✅ EXCELLENT: Search relevance is working very well!")
    elif overall_accuracy >= 80:
        print("  ✅ GOOD: Search relevance is working well")
    elif overall_accuracy >= 70:
        print("  ⚠️ FAIR: Search relevance needs some improvement")
    else:
        print("  ❌ POOR: Search relevance needs significant improvement")

if __name__ == "__main__":
    asyncio.run(main())