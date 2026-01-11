from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Mock documents data
        documents = [
            {
                "id": "1",
                "title": "Machine Learning Fundamentals",
                "source_type": "pdf",
                "created_at": "2024-01-08T10:00:00Z",
                "file_size": 1024000,
                "processing_status": "completed"
            },
            {
                "id": "2", 
                "title": "Project Meeting Notes",
                "source_type": "text",
                "created_at": "2024-01-07T14:30:00Z",
                "file_size": 5120,
                "processing_status": "completed"
            }
        ]
        
        response = {
            "documents": documents,
            "total": len(documents)
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Handle file upload
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Mock upload response
        response = {
            "message": "File uploaded successfully",
            "document_id": "new-doc-123",
            "status": "processing"
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()