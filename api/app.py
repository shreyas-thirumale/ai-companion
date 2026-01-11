#!/usr/bin/env python3
"""
Vercel serverless function for Second Brain AI Companion
"""

import sys
import os
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Import the FastAPI app
try:
    # Import the app from simple-backend.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("simple_backend", root_dir / "simple-backend.py")
    simple_backend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(simple_backend)
    app = simple_backend.app
except Exception as e:
    print(f"Error importing simple-backend: {e}")
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"error": f"Failed to import backend: {str(e)}"}

# Export for Vercel
handler = app