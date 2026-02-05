"""
Documentary Production App - Local version with real GCP services
Uses the same Firestore, GCS, and Vertex AI as Cloud Run version
"""
import os
import re
import uuid
import hashlib
import threading
import base64
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from flask import Flask, render_template, request, jsonify, Response
from google.cloud import firestore, storage
from weasyprint import HTML
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding

app = Flask(__name__)

# Configuration - same as Cloud Run version
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "gbr-aim-aiengine-prod")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.0-flash-001")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", f"{PROJECT_ID}-doc-assets")
MAX_URLS_PER_QUERY = 10
DOWNLOAD_TIMEOUT = 30

# App version and environment
APP_VERSION = os.environ.get("APP_VERSION", "local-1.0.0")
APP_ENV = os.environ.get("APP_ENV", "local")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_NAME)

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID)

# Initialize Cloud Storage
storage_client = storage.Client(project=PROJECT_ID)

# Collection names - same as production
COLLECTIONS = {
    'projects': 'doc_projects',
    'episodes': 'doc_episodes',
    'series': 'doc_series',
    'research': 'doc_research',
    'interviews': 'doc_interviews',
    'shots': 'doc_shots',
    'assets': 'doc_assets',
    'scripts': 'doc_scripts',
    'feedback': 'doc_feedback'
}


# ============== Helper Functions ==============

def doc_to_dict(doc):
    """Convert Firestore document to dict with id."""
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None


def get_all_docs(collection_name, project_id=None):
    """Get all documents from a collection, optionally filtered by project."""
    collection = db.collection(COLLECTIONS[collection_name])
    if project_id:
        docs = collection.where('projectId', '==', project_id).stream()
    else:
        docs = collection.stream()
    return [doc_to_dict(doc) for doc in docs]


def get_doc(collection_name, doc_id):
    """Get a single document by ID."""
    doc = db.collection(COLLECTIONS[collection_name]).document(doc_id).get()
    return doc_to_dict(doc)


def create_doc(collection_name, data):
    """Create a new document."""
    data['createdAt'] = datetime.now(timezone.utc).isoformat()
    data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    doc_ref = db.collection(COLLECTIONS[collection_name]).document()
    doc_ref.set(data)
    data['id'] = doc_ref.id
    return data


def update_doc(collection_name, doc_id, data):
    """Update an existing document."""
    data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    db.collection(COLLECTIONS[collection_name]).document(doc_id).update(data)
    return get_doc(collection_name, doc_id)


def delete_doc(collection_name, doc_id):
    """Delete a document."""
    db.collection(COLLECTIONS[collection_name]).document(doc_id).delete()
    return True


# ============== AI Functions ==============

def generate_ai_response(prompt, system_prompt=""):
    """Generate AI response using Vertex AI."""
    try:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"AI error: {str(e)}"


# ============== Source Document Functions ==============

def extract_urls(text):
    """Extract URLs from text, limited to MAX_URLS_PER_QUERY."""
    url_pattern = r'https?://[^\s<>\[\]()"\']+'
    urls = re.findall(url_pattern, text)
    cleaned_urls = []
    for url in urls:
        url = url.rstrip('.,;:!?)')
        if url and len(url) > 10:
            cleaned_urls.append(url)
    unique_urls = list(dict.fromkeys(cleaned_urls))
    return unique_urls[:MAX_URLS_PER_QUERY]


def convert_to_pdf(html_content, url):
    """Convert HTML content to PDF."""
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if '<base' not in html_content.lower():
            html_content = html_content.replace(
                '<head>',
                f'<head><base href="{base_url}">',
                1
            )
        html = HTML(string=html_content, base_url=base_url)
        pdf_bytes = html.write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"PDF conversion error for {url}: {e}")
        return None


def download_and_store(url, bucket_name, project_id, research_id):
    """Download a URL, convert to PDF, and store in GCS bucket."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()

        html_content = response.text
        pdf_bytes = convert_to_pdf(html_content, url)

        if not pdf_bytes:
            return None

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        filename = f"{domain}_{url_hash}.pdf"
        blob_path = f"{project_id}/{research_id}/{filename}"

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(pdf_bytes, content_type='application/pdf')

        return {
            'url': url,
            'gcsPath': blob_path,
            'filename': filename,
            'size': len(pdf_bytes),
            'title': domain
        }
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


# ============== Routes ==============

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "mode": APP_ENV, "version": APP_VERSION})


# Project routes
@app.route("/api/projects", methods=["GET"])
def get_projects():
    return jsonify(get_all_docs('projects'))


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    return jsonify(create_doc('projects', data)), 201


@app.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    project = get_doc('projects', project_id)
    if project:
        return jsonify(project)
    return jsonify({"error": "Project not found"}), 404


@app.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json()
    return jsonify(update_doc('projects', project_id, data))


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    # Delete related data first
    for collection in ['episodes', 'series', 'research', 'interviews', 'shots', 'assets', 'scripts']:
        docs = db.collection(COLLECTIONS[collection]).where('projectId', '==', project_id).stream()
        for doc in docs:
            doc.reference.delete()
    delete_doc('projects', project_id)
    return jsonify({"success": True})


# Episodes
@app.route("/api/projects/<project_id>/episodes", methods=["GET"])
def get_episodes(project_id):
    return jsonify(get_all_docs('episodes', project_id))


@app.route("/api/episodes", methods=["POST"])
def create_episode():
    data = request.get_json()
    return jsonify(create_doc('episodes', data)), 201


@app.route("/api/episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    data = request.get_json()
    return jsonify(update_doc('episodes', episode_id, data))


@app.route("/api/episodes/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    delete_doc('episodes', episode_id)
    return jsonify({"success": True})


# Series
@app.route("/api/projects/<project_id>/series", methods=["GET"])
def get_series(project_id):
    return jsonify(get_all_docs('series', project_id))


@app.route("/api/series", methods=["POST"])
def create_series():
    data = request.get_json()
    return jsonify(create_doc('series', data)), 201


@app.route("/api/series/<series_id>", methods=["PUT"])
def update_series(series_id):
    data = request.get_json()
    return jsonify(update_doc('series', series_id, data))


@app.route("/api/series/<series_id>", methods=["DELETE"])
def delete_series(series_id):
    # Ungroup episodes first
    episodes = db.collection(COLLECTIONS['episodes']).where('seriesId', '==', series_id).stream()
    for ep in episodes:
        ep.reference.update({'seriesId': None})
    delete_doc('series', series_id)
    return jsonify({"success": True})


# Research
@app.route("/api/projects/<project_id>/research", methods=["GET"])
def get_research(project_id):
    return jsonify(get_all_docs('research', project_id))


@app.route("/api/research", methods=["POST"])
def create_research():
    data = request.get_json()
    return jsonify(create_doc('research', data)), 201


@app.route("/api/research/<research_id>", methods=["PUT"])
def update_research(research_id):
    data = request.get_json()
    return jsonify(update_doc('research', research_id, data))


@app.route("/api/research/<research_id>", methods=["DELETE"])
def delete_research(research_id):
    delete_doc('research', research_id)
    return jsonify({"success": True})


# Interviews
@app.route("/api/projects/<project_id>/interviews", methods=["GET"])
def get_interviews(project_id):
    return jsonify(get_all_docs('interviews', project_id))


@app.route("/api/interviews", methods=["POST"])
def create_interview():
    data = request.get_json()
    return jsonify(create_doc('interviews', data)), 201


@app.route("/api/interviews/<interview_id>", methods=["PUT"])
def update_interview(interview_id):
    data = request.get_json()
    return jsonify(update_doc('interviews', interview_id, data))


@app.route("/api/interviews/<interview_id>", methods=["DELETE"])
def delete_interview(interview_id):
    delete_doc('interviews', interview_id)
    return jsonify({"success": True})


# Shots
@app.route("/api/projects/<project_id>/shots", methods=["GET"])
def get_shots(project_id):
    return jsonify(get_all_docs('shots', project_id))


@app.route("/api/shots", methods=["POST"])
def create_shot():
    data = request.get_json()
    return jsonify(create_doc('shots', data)), 201


@app.route("/api/shots/<shot_id>", methods=["PUT"])
def update_shot(shot_id):
    data = request.get_json()
    return jsonify(update_doc('shots', shot_id, data))


@app.route("/api/shots/<shot_id>", methods=["DELETE"])
def delete_shot(shot_id):
    delete_doc('shots', shot_id)
    return jsonify({"success": True})


# Scripts
@app.route("/api/projects/<project_id>/scripts", methods=["GET"])
def get_scripts(project_id):
    return jsonify(get_all_docs('scripts', project_id))


@app.route("/api/scripts", methods=["POST"])
def create_script():
    data = request.get_json()
    return jsonify(create_doc('scripts', data)), 201


@app.route("/api/scripts/<script_id>", methods=["PUT"])
def update_script(script_id):
    data = request.get_json()
    return jsonify(update_doc('scripts', script_id, data))


@app.route("/api/scripts/<script_id>", methods=["DELETE"])
def delete_script(script_id):
    delete_doc('scripts', script_id)
    return jsonify({"success": True})


# Assets
@app.route("/api/projects/<project_id>/assets", methods=["GET"])
def get_assets(project_id):
    return jsonify(get_all_docs('assets', project_id))


@app.route("/api/assets", methods=["POST"])
def create_asset():
    data = request.get_json()
    return jsonify(create_doc('assets', data)), 201


@app.route("/api/assets/<asset_id>", methods=["PUT"])
def update_asset(asset_id):
    data = request.get_json()
    return jsonify(update_doc('assets', asset_id, data))


@app.route("/api/assets/<asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    # Delete file from GCS if it exists
    asset = get_doc('assets', asset_id)
    if asset and asset.get('gcsPath'):
        try:
            bucket = storage_client.bucket(STORAGE_BUCKET)
            blob = bucket.blob(asset['gcsPath'])
            blob.delete()
        except Exception as e:
            print(f"Error deleting blob: {e}")
    delete_doc('assets', asset_id)
    return jsonify({"success": True})


# ============== Asset Upload ==============

@app.route("/api/assets/upload", methods=["POST"])
def upload_asset():
    """Handle asset file upload with research document support."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Get form data
    project_id = request.form.get('projectId')
    episode_id = request.form.get('episodeId')
    series_id = request.form.get('seriesId')
    is_research_document = request.form.get('isResearchDocument', 'false').lower() == 'true'
    title = request.form.get('title', file.filename)
    asset_type = request.form.get('type', 'Document')
    status = request.form.get('status', 'Acquired')
    notes = request.form.get('notes', '')

    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    # Read file content
    file_content = file.read()
    file_size = len(file_content)
    content_type = file.content_type or 'application/octet-stream'
    original_filename = file.filename

    # Upload to GCS
    file_hash = hashlib.md5(file_content).hexdigest()[:8]
    blob_path = f"assets/{project_id}/{file_hash}_{original_filename}"

    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(file_content, content_type=content_type)
    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

    # Create asset document
    asset_data = {
        "projectId": project_id,
        "title": title,
        "type": asset_type,
        "status": status,
        "notes": notes,
        "gcsPath": blob_path,
        "filename": original_filename,
        "mimeType": content_type,
        "sizeBytes": file_size,
        "hasFile": True,
        "isResearchDocument": is_research_document,
    }

    # Add optional entity associations
    if episode_id:
        asset_data["episodeId"] = episode_id
    if series_id:
        asset_data["seriesId"] = series_id

    asset = create_doc('assets', asset_data)

    return jsonify({
        "success": True,
        "asset": asset,
        "gcsPath": blob_path,
        "filename": original_filename,
        "size": file_size
    }), 201


@app.route("/api/assets/<asset_id>/file", methods=["GET"])
def get_asset_file(asset_id):
    """Download an asset's file."""
    asset = get_doc('assets', asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    gcs_path = asset.get('gcsPath')
    if not gcs_path:
        return jsonify({"error": "File not found"}), 404

    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(gcs_path)
        content = blob.download_as_bytes()
        content_type = asset.get('mimeType', 'application/octet-stream')
        filename = asset.get('filename', 'download')

        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500


# ============== Research Documents Query Endpoints ==============

@app.route("/api/episodes/<episode_id>/research-documents", methods=["GET"])
def get_episode_research_documents(episode_id):
    """Get research documents for an episode."""
    docs = db.collection(COLLECTIONS['assets']).where('episodeId', '==', episode_id).where('isResearchDocument', '==', True).stream()
    return jsonify([doc_to_dict(doc) for doc in docs])


@app.route("/api/series/<series_id>/research-documents", methods=["GET"])
def get_series_research_documents(series_id):
    """Get research documents for a series."""
    docs = db.collection(COLLECTIONS['assets']).where('seriesId', '==', series_id).where('isResearchDocument', '==', True).stream()
    return jsonify([doc_to_dict(doc) for doc in docs])


@app.route("/api/projects/<project_id>/research-documents", methods=["GET"])
def get_project_research_documents(project_id):
    """Get project-level research documents (not associated with episode/series)."""
    # Get all research docs for project, then filter in Python
    docs = db.collection(COLLECTIONS['assets']).where('projectId', '==', project_id).where('isResearchDocument', '==', True).stream()
    result = []
    for doc in docs:
        data = doc_to_dict(doc)
        if not data.get('episodeId') and not data.get('seriesId'):
            result.append(data)
    return jsonify(result)


@app.route("/api/projects/<project_id>/all-research-documents", methods=["GET"])
def get_all_research_documents(project_id):
    """Get all research documents for a project."""
    docs = db.collection(COLLECTIONS['assets']).where('projectId', '==', project_id).where('isResearchDocument', '==', True).stream()
    return jsonify([doc_to_dict(doc) for doc in docs])


# ============== Source Documents ==============

@app.route("/api/projects/<project_id>/source-documents", methods=["GET"])
def get_source_documents(project_id):
    """Get source documents for a project."""
    docs = db.collection(COLLECTIONS['assets']).where('projectId', '==', project_id).where('isSourceDocument', '==', True).stream()
    return jsonify([doc_to_dict(doc) for doc in docs])


@app.route("/api/document/<path:blob_path>")
def get_document(blob_path):
    """Serve a document (inline)."""
    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(blob_path)
        content = blob.download_as_bytes()
        content_type = blob.content_type or 'application/pdf'
        filename = blob_path.split("/")[-1]

        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'inline; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": f"Document not found: {str(e)}"}), 404


@app.route("/api/download/<path:blob_path>")
def download_document(blob_path):
    """Download a document (attachment)."""
    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(blob_path)
        content = blob.download_as_bytes()
        content_type = blob.content_type or 'application/pdf'
        filename = blob_path.split("/")[-1]

        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": f"Document not found: {str(e)}"}), 404


# ============== AI Endpoints ==============

@app.route("/api/ai/generate-topics", methods=["POST"])
def ai_generate_topics():
    """Generate episode topics from project title and description."""
    data = request.get_json()
    title = data.get('title', 'Documentary')
    description = data.get('description', '')
    num_topics = data.get('numTopics', 5)

    prompt = f"""Generate {num_topics} episode ideas for a documentary titled "{title}".

Description: {description}

For each episode, provide:
1. A compelling title
2. A brief description (2-3 sentences)

Format your response as a JSON array with objects containing "title", "description", and "order" fields.
Only output the JSON array, no other text."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Try to parse JSON from response
        import json
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text.rsplit('\n', 1)[0]

        topics = json.loads(response_text)
        return jsonify({"topics": topics[:num_topics]})
    except Exception as e:
        # Fallback to generic topics
        topics = [
            {"title": f"Episode {i+1}: {title} - Part {i+1}", "description": f"Exploring aspect {i+1} of {title}.", "order": i+1}
            for i in range(num_topics)
        ]
        return jsonify({"topics": topics})


@app.route("/api/ai/research", methods=["POST"])
def ai_research():
    """AI-powered research with source downloading."""
    data = request.get_json()
    query = data.get('query', '')
    project_id = data.get('projectId', '')
    download_sources = data.get('downloadSources', True)

    system_prompt = """You are a research assistant for documentary filmmakers.
    Provide well-sourced, factual information with clear citations.
    Include URLs to primary sources when possible.
    Format your response with clear sections and bullet points."""

    result = generate_ai_response(query, system_prompt)
    response_data = {"result": result, "sources": []}

    if download_sources and project_id:
        urls = extract_urls(result)
        if urls:
            research_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + hashlib.md5(query.encode()).hexdigest()[:8]
            response_data["researchId"] = research_id

            for url in urls[:3]:  # Limit to 3 sources
                source_data = download_and_store(url, STORAGE_BUCKET, project_id, research_id)
                if source_data:
                    # Create asset for source document
                    asset_data = {
                        "projectId": project_id,
                        "researchId": research_id,
                        "title": source_data['title'],
                        "type": "Document",
                        "source": url,
                        "gcsPath": source_data['gcsPath'],
                        "status": "Acquired",
                        "isSourceDocument": True,
                        "sizeBytes": source_data['size'],
                        "filename": source_data['filename']
                    }
                    create_doc('assets', asset_data)
                    response_data["sources"].append({
                        "url": url,
                        "status": "success",
                        "title": source_data['title'],
                        "gcsPath": source_data['gcsPath']
                    })

    return jsonify(response_data)


@app.route("/api/ai/interview-questions", methods=["POST"])
def ai_interview():
    """Generate interview questions."""
    data = request.get_json()
    subject = data.get('subject', 'Subject')
    role = data.get('role', '')
    context = data.get('context', '')

    prompt = f"""Generate thoughtful interview questions for {subject}, who is a {role}.

Context: {context}

Provide 8-10 open-ended questions that will elicit compelling storytelling responses.
Include follow-up prompts where appropriate."""

    result = generate_ai_response(prompt)
    return jsonify({"result": result})


@app.route("/api/ai/script-outline", methods=["POST"])
def ai_script():
    """Generate script outline."""
    data = request.get_json()
    title = data.get('title', 'Episode')
    duration = data.get('duration', '45 minutes')
    content = data.get('content', '')

    prompt = f"""Create a detailed script outline for a documentary episode titled "{title}".

Target duration: {duration}
Content/Notes: {content}

Include:
- Three-act structure with timestamps
- Key narrative beats
- Suggested interview segments
- B-roll and visual suggestions"""

    result = generate_ai_response(prompt)
    return jsonify({"result": result})


@app.route("/api/ai/shot-ideas", methods=["POST"])
def ai_shots():
    """Generate shot ideas."""
    data = request.get_json()
    scene = data.get('scene', '')
    location = data.get('location', '')

    prompt = f"""Suggest cinematic shot ideas for a documentary scene.

Scene: {scene}
Location: {location}

Include:
- Shot type (wide, close-up, etc.)
- Camera movement suggestions
- Equipment recommendations
- Lighting considerations"""

    result = generate_ai_response(prompt)
    return jsonify({"result": result})


@app.route("/api/ai/expand-topic", methods=["POST"])
def ai_expand():
    """Expand on a topic."""
    data = request.get_json()
    topic = data.get('topic', '')

    prompt = f"""Provide a comprehensive exploration of this documentary topic: {topic}

Include:
- Multiple angles and perspectives
- Key themes to explore
- Potential story threads
- Related subtopics"""

    result = generate_ai_response(prompt)
    return jsonify({"result": result})


def get_research_document_contents(episode_id=None, series_id=None, project_id=None):
    """Fetch and read contents of research documents for context."""
    documents_context = []

    try:
        # Get episode research documents
        if episode_id:
            docs = db.collection(COLLECTIONS['assets']).where('episodeId', '==', episode_id).where('isResearchDocument', '==', True).stream()
            for doc in docs:
                data = doc.to_dict()
                content = read_document_content(data.get('gcsPath'), data.get('mimeType', ''))
                if content:
                    documents_context.append({
                        'source': f"Episode Document: {data.get('title', data.get('filename', 'Unknown'))}",
                        'content': content
                    })

        # Get series research documents
        if series_id:
            docs = db.collection(COLLECTIONS['assets']).where('seriesId', '==', series_id).where('isResearchDocument', '==', True).stream()
            for doc in docs:
                data = doc.to_dict()
                content = read_document_content(data.get('gcsPath'), data.get('mimeType', ''))
                if content:
                    documents_context.append({
                        'source': f"Series Document: {data.get('title', data.get('filename', 'Unknown'))}",
                        'content': content
                    })

        # Get project-level research documents
        if project_id:
            docs = db.collection(COLLECTIONS['assets']).where('projectId', '==', project_id).where('isResearchDocument', '==', True).stream()
            for doc in docs:
                data = doc.to_dict()
                # Only include project-level docs (not linked to episode/series)
                if not data.get('episodeId') and not data.get('seriesId'):
                    content = read_document_content(data.get('gcsPath'), data.get('mimeType', ''))
                    if content:
                        documents_context.append({
                            'source': f"Project Document: {data.get('title', data.get('filename', 'Unknown'))}",
                            'content': content
                        })
    except Exception as e:
        print(f"Error fetching research documents: {e}")

    return documents_context


def read_document_content(gcs_path, mime_type=''):
    """Read content from a document in GCS."""
    if not gcs_path:
        return None

    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(gcs_path)
        content = blob.download_as_bytes()

        # For text-based files, decode to string
        if mime_type.startswith('text/') or gcs_path.endswith(('.txt', '.md', '.csv')):
            return content.decode('utf-8', errors='ignore')[:10000]  # Limit to 10k chars

        # For PDFs and other binary formats, we'd need extraction
        # For now, skip binary files
        if gcs_path.endswith('.pdf'):
            return f"[PDF Document - content extraction not implemented]"

        return None
    except Exception as e:
        print(f"Error reading document {gcs_path}: {e}")
        return None


@app.route("/api/ai/simple-research", methods=["POST"])
def ai_simple_research():
    """AI research query augmented with uploaded research documents from episode and series."""
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    user_query = data.get('query', '')  # User's custom research prompt
    episode_id = data.get('episodeId', '')
    series_id = data.get('seriesId', '')
    project_id = data.get('projectId', '')
    save_research = data.get('save', True)

    # Fetch research documents for context
    research_docs = get_research_document_contents(
        episode_id=episode_id,
        series_id=series_id,
        project_id=project_id
    )

    # Build context from research documents
    context_section = ""
    if research_docs:
        context_section = "\n\n## Reference Documents\n\nThe following research documents have been uploaded and should be used as context:\n\n"
        for doc in research_docs:
            context_section += f"### {doc['source']}\n{doc['content']}\n\n"

    # Use user's query if provided, otherwise fall back to title/description
    research_query = user_query if user_query else f"Research background information for the documentary episode titled '{title}': {description}"

    prompt = f"""You are researching for a documentary episode.

Episode: {title}
{f'Description: {description}' if description else ''}
{context_section}

## Research Request

{research_query}

## Instructions

Based on {'the reference documents above and ' if research_docs else ''}the research request, provide:
- Key facts and background information
- Relevant sources and references (with URLs where possible)
- Interview suggestions (people to talk to)
- Visual/archive material recommendations

{f'IMPORTANT: Incorporate and build upon the information from the {len(research_docs)} provided reference document(s). Reference specific details from them where relevant.' if research_docs else ''}

Format your response with clear sections and bullet points."""

    result = generate_ai_response(prompt)
    response_data = {
        "result": result,
        "title": title,
        "query": research_query,
        "saved": False,
        "documentsUsed": len(research_docs)
    }

    if save_research and episode_id:
        update_doc('episodes', episode_id, {
            'research': result,
            'researchGeneratedAt': datetime.now(timezone.utc).isoformat()
        })
        response_data['saved'] = True
        response_data['episodeId'] = episode_id

    return jsonify(response_data)


@app.route("/api/episodes/<episode_id>/research", methods=["GET"])
def get_episode_research(episode_id):
    """Get saved research for an episode."""
    episode = get_doc('episodes', episode_id)
    if not episode:
        return jsonify({"error": "Episode not found"}), 404

    return jsonify({
        "research": episode.get('research', ''),
        "generatedAt": episode.get('researchGeneratedAt', ''),
        "episodeId": episode_id,
        "episodeTitle": episode.get('title', '')
    })


@app.route("/api/episodes/<episode_id>/research", methods=["PUT"])
def save_episode_research(episode_id):
    """Save research to an episode."""
    data = request.get_json()
    research = data.get('research', '')

    update_doc('episodes', episode_id, {
        'research': research,
        'researchGeneratedAt': datetime.now(timezone.utc).isoformat()
    })

    return jsonify({
        "success": True,
        "episodeId": episode_id,
        "linksExtracted": 0,
        "assetsCreated": 0
    })


@app.route("/api/episodes/<episode_id>/research", methods=["DELETE"])
def delete_episode_research(episode_id):
    """Delete saved research for an episode."""
    update_doc('episodes', episode_id, {
        'research': '',
        'researchGeneratedAt': ''
    })
    return jsonify({"success": True})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Documentary Production App - LOCAL MODE")
    print("  Using REAL GCP services (Firestore, GCS, Vertex AI)")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Bucket: {STORAGE_BUCKET}")
    print("=" * 50)
    print("\n  Open: http://localhost:5000\n")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
