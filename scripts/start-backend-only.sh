#!/bin/bash

# Start only backend services, run frontend locally

set -e

echo "🧠 Starting Second Brain Backend Services..."

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env file"
fi

echo "🐳 Starting backend services..."

# Start only backend services
docker-compose -f docker-compose.dev.yml up --build -d

echo "⏳ Waiting for backend to be ready..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 2
done

echo "✅ Backend services are ready!"
echo ""
echo "🎉 Backend is running!"
echo ""
echo "🔧 API Docs:  http://localhost:8000/docs"
echo "📊 Database: localhost:5432 (user: user, password: password)"
echo ""
echo "📱 To start frontend locally:"
echo "   cd frontend"
echo "   npm install"
echo "   npm start"
echo ""
echo "📋 To view logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "🛑 To stop:     docker-compose -f docker-compose.dev.yml down"