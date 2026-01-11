# Second Brain AI Companion

A personal AI companion that ingests, understands, and reasons about your information. Upload documents, audio, images, and web content, then have natural language conversations to retrieve and synthesize information from your knowledge base.

## 🚀 Vercel Deployment Ready

This project is configured for seamless deployment on Vercel with:
- **Frontend**: React app with Tailwind CSS
- **Backend**: Python serverless functions
- **API**: RESTful endpoints for document management and queries

## 🎯 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ai-companion)

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python serverless functions on Vercel
- **API**: RESTful endpoints with CORS support
- **Deployment**: Vercel with automatic builds and deployments

## 📁 Project Structure

```
/
├── api/                 # Python serverless functions
│   ├── health.py       # Health check endpoint
│   ├── query.py        # Query processing endpoint
│   └── documents.py    # Document management endpoint
├── src/                # React frontend source
│   ├── components/     # Reusable UI components
│   ├── pages/          # Main application pages
│   ├── services/       # API client
│   └── hooks/          # Custom React hooks
├── public/             # Static assets
├── package.json        # Frontend dependencies
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
└── DEPLOYMENT.md       # Deployment guide
```

## 🚀 Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# For API testing with Vercel CLI
npx vercel dev
```

## 🔧 Environment Variables

Create a `.env.local` file:

```
REACT_APP_API_URL=/api
OPENAI_API_KEY=your_openai_api_key_here
```

## 📊 Features

### ✅ Frontend
- [x] Clean, responsive chat interface
- [x] Real-time streaming responses
- [x] File upload with drag-and-drop
- [x] Document management interface
- [x] Analytics dashboard
- [x] Search and filtering capabilities

### ✅ Backend API
- [x] Health check endpoint
- [x] Document upload and management
- [x] Query processing with mock responses
- [x] CORS support for cross-origin requests
- [x] Serverless architecture

## 🔒 Production Considerations

For production deployment, consider:
- Adding authentication and authorization
- Integrating with a real database (PostgreSQL, MongoDB)
- Implementing file storage (AWS S3, Vercel Blob)
- Adding rate limiting and security headers
- Setting up monitoring and logging

## 📞 Support

For deployment questions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Ready for Vercel deployment! 🚀**