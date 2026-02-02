# Documentary Production App

A mobile-first web application for managing documentary productions with AI-powered assistance. Built with Flask, Google Cloud Firestore, and Vertex AI (Gemini).

## Features

### Project Management
- **Dashboard** - Overview of project statistics and episode progress
- **Episodes** - Plan and track documentary episodes with status workflow
- **Research** - Store research notes, sources, and contacts
- **Interviews** - Manage interview subjects, questions, and scheduling
- **Production** - Shot lists with locations, equipment, and dates
- **Assets** - Track media assets (video, audio, images, documents)
- **Scripts** - Write and organize episode scripts and outlines

### AI Assistant (Powered by Gemini)
- **Research Help** - Find sources, archives, and background information
- **Interview Questions** - Generate thoughtful questions for subjects
- **Script Outlines** - Create structured episode outlines
- **Shot Ideas** - Get creative cinematography suggestions
- **Topic Exploration** - Explore angles, themes, and storylines

## Running Locally

### Prerequisites
- Python 3.9+
- pip

### Quick Start (Test Mode)

Test mode uses in-memory storage and mocked AI responses - no GCP account required.

```bash
# Clone the repository
git clone https://github.com/grahamatarrowmedia/ai-doc-phone--app.git
cd ai-doc-phone--app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask

# Run test app
python test_app.py
```

Open http://localhost:5000 in your browser (or phone).

### Full Mode (with GCP)

Requires a Google Cloud project with Firestore and Vertex AI enabled.

```bash
# Install all dependencies
pip install -r requirements.txt

# Set up GCP authentication
gcloud auth application-default login

# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GCP_LOCATION=us-central1

# Run the app
python app.py
```

## Deployment

### Deploy to Cloud Run

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Manual Deployment

```bash
# Build container
docker build -t gcr.io/PROJECT_ID/doc-production-app .

# Push to registry
docker push gcr.io/PROJECT_ID/doc-production-app

# Deploy to Cloud Run
gcloud run deploy doc-production-app \
  --image gcr.io/PROJECT_ID/doc-production-app \
  --region us-central1 \
  --platform managed \
  --set-env-vars "GCP_PROJECT_ID=PROJECT_ID"
```

## Project Structure

```
ai-doc-phone--app/
├── app.py              # Flask backend with Firestore + Vertex AI
├── test_app.py         # Local test version (no GCP required)
├── templates/
│   └── index.html      # Mobile-first SPA interface
├── static/
│   ├── css/style.css   # Responsive styling
│   └── manifest.json   # PWA manifest
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── cloudbuild.yaml     # Cloud Build deployment
└── README.md           # This file
```

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Collections (episodes, research, interviews, shots, assets, scripts)
- `GET /api/projects/<project_id>/<collection>` - List items
- `POST /api/<collection>` - Create item
- `PUT /api/<collection>/<id>` - Update item
- `DELETE /api/<collection>/<id>` - Delete item

### AI Endpoints
- `POST /api/ai/research` - Research assistance
- `POST /api/ai/interview-questions` - Generate interview questions
- `POST /api/ai/script-outline` - Generate script outline
- `POST /api/ai/shot-ideas` - Get shot ideas
- `POST /api/ai/expand-topic` - Explore topic angles

## Mobile Usage

The app is designed as a Progressive Web App (PWA) for mobile use:

1. Open the app URL in your mobile browser
2. Tap "Add to Home Screen" (iOS Safari) or install prompt (Android Chrome)
3. The app will run in standalone mode like a native app

## License

MIT
