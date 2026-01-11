# Vercel Deployment Guide

This project is configured for deployment on Vercel with both frontend (React) and backend (Python serverless functions).

## Project Structure

```
/
├── api/                 # Python serverless functions
│   ├── health.py       # Health check endpoint
│   ├── query.py        # Query processing endpoint
│   └── documents.py    # Document management endpoint
├── src/                # React frontend source
├── public/             # Static assets
├── package.json        # Frontend dependencies
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
└── README.md
```

## Deployment Steps

### 1. Connect to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Sign up/login with your GitHub account
3. Click "New Project"
4. Import your GitHub repository

### 2. Configure Environment Variables

In your Vercel dashboard, add these environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here (optional)
```

### 3. Deploy

Vercel will automatically:
- Build the React frontend
- Deploy Python serverless functions
- Set up routing between frontend and API

### 4. Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain

## API Endpoints

Once deployed, your API will be available at:

- `GET /api/health` - Health check
- `POST /api/query` - Submit queries
- `GET /api/documents` - List documents
- `POST /api/documents` - Upload documents

## Local Development

```bash
# Install frontend dependencies
npm install

# Start development server
npm start

# The frontend will run on http://localhost:3000
# API functions can be tested using Vercel CLI:
vercel dev
```

## Environment Variables

Create a `.env.local` file for local development:

```
REACT_APP_API_URL=/api
OPENAI_API_KEY=your_key_here
```

## Notes

- The serverless functions are currently mock implementations
- For production, you'll need to integrate with a real database
- File uploads will need additional configuration for larger files
- Consider adding authentication for production use