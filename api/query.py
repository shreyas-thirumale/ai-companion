from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Handle CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            query = data.get('query', '')
            
            # Mock response for now - you can integrate with your actual search logic
            response = {
                "query": query,
                "response": f"This is a demo response for your query: '{query}'. In a full implementation, this would search your knowledge base and provide relevant information.",
                "sources": [
                    {
                        "document_id": "demo-1",
                        "title": "Demo Document",
                        "content": "This is demo content that would be relevant to your query.",
                        "relevance_score": 0.85,
                        "source_type": "text"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "message": "Failed to process query"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()