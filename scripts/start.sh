#!/bin/bash

# Second Brain AI Companion - Startup Script

set -e

echo "🧠 Starting Second Brain AI Companion..."

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env file"
fi

# Check OpenAI API key status
if grep -q "OPENAI_API_KEY=sk-" backend/.env 2>/dev/null; then
    echo "🔑 OpenAI API key found - using real AI responses"
else
    echo "🎭 No OpenAI API key - using realistic demo mode"
    echo "   💡 This works perfectly for the assignment demo!"
    echo "   💡 All features work, just with simulated AI responses"
fi

echo "🐳 Starting Docker services..."

# Build and start services
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."

# Wait for backend to be ready
echo "   Waiting for backend..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 2
done

echo "✅ Services are ready!"
echo ""

# Ask about demo data
if ! grep -q "OPENAI_API_KEY=sk-" backend/.env 2>/dev/null; then
    echo "🎭 Demo Mode Detected!"
    echo ""
    read -p "Would you like to add sample documents for testing? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📚 Adding demo documents..."
        docker-compose exec backend python scripts/add-demo-data.py
        echo ""
    fi
fi

echo "🎉 Second Brain AI Companion is running!"
echo ""
echo "📱 Frontend:  http://localhost:3000"
echo "🔧 API Docs:  http://localhost:8000/docs"
echo "📊 Database: localhost:5432 (user: user, password: password)"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop:     docker-compose down"
echo ""
if grep -q "OPENAI_API_KEY=sk-" backend/.env 2>/dev/null; then
    echo "🚀 Ready with full AI capabilities!"
else
    echo "🎭 Ready in demo mode - perfect for showcasing the system!"
    echo "   Upload documents and ask questions to see realistic AI responses"
fi