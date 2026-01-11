# Deployment Guide

## Vercel Deployment

This application is configured for deployment on Vercel with the following setup:

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **MongoDB Atlas**: Set up a MongoDB Atlas cluster
3. **OpenRouter API Key**: Get an API key from [openrouter.ai](https://openrouter.ai)

### Environment Variables

Set these environment variables in your Vercel project settings:

```bash
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MONGODB_URL=your_mongodb_atlas_connection_string_here
DATABASE_NAME=second_brain_ai
DEBUG=false
CORS_ORIGINS=*
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Deployment Steps

1. **Connect Repository**:
   ```bash
   # Push your code to GitHub
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Deploy to Vercel**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will automatically detect the configuration from `vercel.json`

3. **Set Environment Variables**:
   - In your Vercel project dashboard, go to Settings → Environment Variables
   - Add all the required environment variables listed above

4. **Deploy**:
   - Vercel will automatically deploy your application
   - The frontend will be served from `index.html`
   - The backend API will be available at `/api/*` routes

### Architecture

- **Frontend**: Static HTML served by Vercel
- **Backend**: Python FastAPI serverless functions
- **Database**: MongoDB Atlas (cloud)
- **AI**: OpenRouter API for LLM responses

### Features Available in Deployment

✅ **Document Upload & Storage** - Upload PDFs, text files, and more
✅ **AI Chat Interface** - Ask questions about your documents  
✅ **Document Search** - Find relevant documents with AI-powered search
✅ **Download Documents** - Download processed content
✅ **Chat History** - Persistent chat history in browser
✅ **Clear Chat Command** - Type `/clear` to clear chat history

⚠️ **Audio Transcription** - Disabled in Vercel deployment (requires local Whisper)

### Local Development

To run locally:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Run the backend
python simple-backend.py

# Open index.html in your browser
```

### Troubleshooting

1. **API Errors**: Check environment variables are set correctly
2. **Database Connection**: Ensure MongoDB Atlas IP whitelist includes 0.0.0.0/0
3. **CORS Issues**: Make sure CORS_ORIGINS includes your domain
4. **Function Timeout**: Vercel functions have a 10-second timeout limit

### Monitoring

- Check Vercel function logs in the dashboard
- Monitor MongoDB Atlas metrics
- Use browser developer tools for frontend debugging