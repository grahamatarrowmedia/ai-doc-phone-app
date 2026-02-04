"""
Documentary Production App - Flask backend with Firestore and Vertex AI
"""
import os
import re
import hashlib
import threading
import base64
import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import Flask, render_template, request, jsonify, Response
from google.cloud import firestore, storage
from weasyprint import HTML
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding

app = Flask(__name__)

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.0-flash-001")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", f"{PROJECT_ID}-doc-assets")
MAX_URLS_PER_QUERY = 10
DOWNLOAD_TIMEOUT = 30

# App version and environment
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
APP_ENV = os.environ.get("APP_ENV", "production")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_NAME)

# Initialize Firestore
db = firestore.Client()

# Initialize Cloud Storage
storage_client = storage.Client()

# Collection names
COLLECTIONS = {
    'projects': 'doc_projects',
    'episodes': 'doc_episodes',
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
    data['createdAt'] = datetime.utcnow().isoformat()
    data['updatedAt'] = datetime.utcnow().isoformat()
    doc_ref = db.collection(COLLECTIONS[collection_name]).document()
    doc_ref.set(data)
    data['id'] = doc_ref.id
    return data


def update_doc(collection_name, doc_id, data):
    """Update an existing document."""
    data['updatedAt'] = datetime.utcnow().isoformat()
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


def generate_grounded_research(prompt, system_prompt=""):
    """Placeholder - AI research functionality disabled in this build."""
    return {
        'text': 'AI Research functionality is not available in this build.',
        'sources': []
    }


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


def validate_url(url, timeout=3):
    """Check if a URL is accessible (returns True if reachable)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        # Try GET if HEAD fails (some servers don't support HEAD)
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.close()
            return response.status_code < 400
        except:
            return False


def filter_valid_urls(urls, max_to_check=5):
    """Filter URLs to only include valid, accessible ones (limited to prevent timeout)."""
    valid_urls = []
    checked = 0
    for url in urls:
        if checked >= max_to_check:
            break
        if len(valid_urls) >= 3:  # Stop once we have enough valid URLs
            break
        if validate_url(url):
            valid_urls.append(url)
            print(f"✓ Valid URL: {url[:60]}...")
        else:
            print(f"✗ Invalid URL: {url[:60]}...")
        checked += 1
    return valid_urls


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
        response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()

        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        if path:
            base_filename = path.split('/')[-1]
            base_filename = re.sub(r'[^\w\-.]', '_', base_filename)
        else:
            base_filename = parsed_url.netloc.replace('.', '_')

        if '.' in base_filename:
            base_filename = base_filename.rsplit('.', 1)[0]

        title = base_filename.replace('_', ' ').title()
        if 'html' in content_type:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        bucket = storage_client.bucket(bucket_name)

        result = {"url": url, "title": title, "status": "success"}

        if content_type == 'application/pdf':
            blob_path = f"{project_id}/{url_hash}_{base_filename}.pdf"
            blob = bucket.blob(blob_path)
            blob.upload_from_string(response.content, content_type='application/pdf')
            result["gcsPath"] = blob_path
            result["size_bytes"] = len(response.content)
            result["filename"] = f"{base_filename}.pdf"

        elif 'html' in content_type or 'text' in content_type:
            pdf_bytes = convert_to_pdf(response.text, url)
            if pdf_bytes:
                blob_path = f"{project_id}/{url_hash}_{base_filename}.pdf"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(pdf_bytes, content_type='application/pdf')
                result["gcsPath"] = blob_path
                result["size_bytes"] = len(pdf_bytes)
                result["filename"] = f"{base_filename}.pdf"
            else:
                blob_path = f"{project_id}/{url_hash}_{base_filename}.html"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(response.content, content_type='text/html')
                result["gcsPath"] = blob_path
                result["size_bytes"] = len(response.content)
                result["filename"] = f"{base_filename}.html"
        else:
            ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
            blob_path = f"{project_id}/{url_hash}_{base_filename}.{ext}"
            blob = bucket.blob(blob_path)
            blob.upload_from_string(response.content, content_type=content_type)
            result["gcsPath"] = blob_path
            result["size_bytes"] = len(response.content)
            result["filename"] = f"{base_filename}.{ext}"

        if result.get("gcsPath"):
            create_source_document_asset(project_id, research_id, result)

        return result

    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


def create_source_document_asset(project_id, research_id, doc_result):
    """Create a Firestore asset entry for a downloaded source document."""
    try:
        asset_data = {
            "projectId": project_id,
            "researchId": research_id,
            "title": doc_result.get("title", "Untitled Document"),
            "type": "Document",
            "source": doc_result.get("url", ""),
            "gcsPath": doc_result.get("gcsPath", ""),
            "status": "Acquired",
            "isSourceDocument": True,
            "sizeBytes": doc_result.get("size_bytes", 0),
            "filename": doc_result.get("filename", ""),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        doc_ref = db.collection(COLLECTIONS['assets']).document()
        doc_ref.set(asset_data)
        print(f"Created source document asset: {doc_result.get('title')}")
    except Exception as e:
        print(f"Error creating asset: {e}")


def process_source_documents_async(urls, bucket_name, project_id, research_id):
    """Background thread to download and process source documents."""
    print(f"Starting download of {len(urls)} sources for research {research_id}")
    success_count = 0
    error_count = 0
    for url in urls:
        try:
            print(f"Downloading: {url[:80]}...")
            result = download_and_store(url, bucket_name, project_id, research_id)
            if result.get("status") == "error":
                print(f"Failed to download {url}: {result.get('error')}")
                error_count += 1
            else:
                print(f"Successfully downloaded: {result.get('title', url)}")
                success_count += 1
        except Exception as e:
            print(f"Error processing {url}: {e}")
            error_count += 1
    print(f"Download complete: {success_count} success, {error_count} errors")


def ensure_bucket_exists(bucket_name):
    """Create bucket if it doesn't exist."""
    try:
        bucket = storage_client.bucket(bucket_name)
        if not bucket.exists():
            bucket = storage_client.create_bucket(bucket_name, location=LOCATION)
        return True
    except Exception as e:
        print(f"Bucket error: {e}")
        return False


# ============== Routes ==============

@app.route("/")
def index():
    """Render the main app interface."""
    return render_template("index.html", app_version=APP_VERSION, app_env=APP_ENV)


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


# ============== Project Routes ==============

@app.route("/api/projects", methods=["GET"])
def get_projects():
    """Get all projects."""
    projects = get_all_docs('projects')
    return jsonify(projects)


@app.route("/api/projects", methods=["POST"])
def create_project():
    """Create a new project."""
    data = request.get_json()
    project = create_doc('projects', data)
    return jsonify(project), 201


@app.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """Get a single project."""
    project = get_doc('projects', project_id)
    if project:
        return jsonify(project)
    return jsonify({"error": "Project not found"}), 404


@app.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    """Update a project."""
    data = request.get_json()
    project = update_doc('projects', project_id, data)
    return jsonify(project)


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project and all related data."""
    # Delete all related data first
    for collection in ['episodes', 'research', 'interviews', 'shots', 'assets', 'scripts']:
        docs = db.collection(COLLECTIONS[collection]).where('projectId', '==', project_id).stream()
        for doc in docs:
            doc.reference.delete()

    # Delete the project itself
    delete_doc('projects', project_id)
    return jsonify({"success": True})


# ============== Episode Routes ==============

@app.route("/api/projects/<project_id>/episodes", methods=["GET"])
def get_episodes(project_id):
    """Get all episodes for a project."""
    episodes = get_all_docs('episodes', project_id)
    return jsonify(episodes)


@app.route("/api/episodes", methods=["POST"])
def create_episode():
    """Create a new episode."""
    data = request.get_json()
    episode = create_doc('episodes', data)
    return jsonify(episode), 201


@app.route("/api/episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    """Update an episode."""
    data = request.get_json()
    episode = update_doc('episodes', episode_id, data)
    return jsonify(episode)


@app.route("/api/episodes/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    """Delete an episode."""
    delete_doc('episodes', episode_id)
    return jsonify({"success": True})


# ============== Research Routes ==============

@app.route("/api/projects/<project_id>/research", methods=["GET"])
def get_research(project_id):
    """Get all research for a project."""
    research = get_all_docs('research', project_id)
    return jsonify(research)


@app.route("/api/research", methods=["POST"])
def create_research():
    """Create a new research item."""
    data = request.get_json()
    research = create_doc('research', data)
    return jsonify(research), 201


@app.route("/api/research/<research_id>", methods=["PUT"])
def update_research(research_id):
    """Update a research item."""
    data = request.get_json()
    research = update_doc('research', research_id, data)
    return jsonify(research)


@app.route("/api/research/<research_id>", methods=["DELETE"])
def delete_research(research_id):
    """Delete a research item."""
    delete_doc('research', research_id)
    return jsonify({"success": True})


# ============== Interview Routes ==============

@app.route("/api/projects/<project_id>/interviews", methods=["GET"])
def get_interviews(project_id):
    """Get all interviews for a project."""
    interviews = get_all_docs('interviews', project_id)
    return jsonify(interviews)


@app.route("/api/interviews", methods=["POST"])
def create_interview():
    """Create a new interview."""
    data = request.get_json()
    interview = create_doc('interviews', data)
    return jsonify(interview), 201


@app.route("/api/interviews/<interview_id>", methods=["PUT"])
def update_interview(interview_id):
    """Update an interview."""
    data = request.get_json()
    interview = update_doc('interviews', interview_id, data)
    return jsonify(interview)


@app.route("/api/interviews/<interview_id>", methods=["DELETE"])
def delete_interview(interview_id):
    """Delete an interview."""
    delete_doc('interviews', interview_id)
    return jsonify({"success": True})


# ============== Shot Routes ==============

@app.route("/api/projects/<project_id>/shots", methods=["GET"])
def get_shots(project_id):
    """Get all shots for a project."""
    shots = get_all_docs('shots', project_id)
    return jsonify(shots)


@app.route("/api/shots", methods=["POST"])
def create_shot():
    """Create a new shot."""
    data = request.get_json()
    shot = create_doc('shots', data)
    return jsonify(shot), 201


@app.route("/api/shots/<shot_id>", methods=["PUT"])
def update_shot(shot_id):
    """Update a shot."""
    data = request.get_json()
    shot = update_doc('shots', shot_id, data)
    return jsonify(shot)


@app.route("/api/shots/<shot_id>", methods=["DELETE"])
def delete_shot(shot_id):
    """Delete a shot."""
    delete_doc('shots', shot_id)
    return jsonify({"success": True})


# ============== Asset Routes ==============

@app.route("/api/projects/<project_id>/assets", methods=["GET"])
def get_assets(project_id):
    """Get all assets for a project."""
    assets = get_all_docs('assets', project_id)
    return jsonify(assets)


@app.route("/api/assets", methods=["POST"])
def create_asset():
    """Create a new asset."""
    data = request.get_json()
    asset = create_doc('assets', data)
    return jsonify(asset), 201


@app.route("/api/assets/<asset_id>", methods=["PUT"])
def update_asset(asset_id):
    """Update an asset."""
    data = request.get_json()
    asset = update_doc('assets', asset_id, data)
    return jsonify(asset)


@app.route("/api/assets/<asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    """Delete an asset and its GCS file if it exists."""
    # Get asset first to check for GCS file
    asset = get_doc('assets', asset_id)
    if asset and asset.get('gcsPath'):
        try:
            bucket = storage_client.bucket(STORAGE_BUCKET)
            blob = bucket.blob(asset['gcsPath'])
            if blob.exists():
                blob.delete()
        except Exception as e:
            print(f"Error deleting GCS file: {e}")

    delete_doc('assets', asset_id)
    return jsonify({"success": True})


@app.route("/api/projects/<project_id>/assets/clear-sources", methods=["DELETE"])
def clear_source_documents(project_id):
    """Delete all source documents for a project."""
    try:
        # Get all source documents
        docs_ref = db.collection(COLLECTIONS['assets']).where(
            'projectId', '==', project_id
        ).where(
            'isSourceDocument', '==', True
        )

        deleted_count = 0
        bucket = storage_client.bucket(STORAGE_BUCKET)

        for doc in docs_ref.stream():
            doc_data = doc.to_dict()
            # Delete GCS file if exists
            if doc_data.get('gcsPath'):
                try:
                    blob = bucket.blob(doc_data['gcsPath'])
                    if blob.exists():
                        blob.delete()
                except Exception as e:
                    print(f"Error deleting GCS file {doc_data['gcsPath']}: {e}")

            # Delete Firestore document
            doc.reference.delete()
            deleted_count += 1

        return jsonify({"success": True, "deleted": deleted_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/assets/download-sources", methods=["POST"])
def download_additional_sources(project_id):
    """Download source documents from a list of URLs."""
    data = request.get_json()
    urls = data.get('urls', [])
    research_id = data.get('researchId', datetime.utcnow().strftime("%Y%m%d_%H%M%S"))

    if not urls:
        return jsonify({"error": "No URLs provided"}), 400

    ensure_bucket_exists(STORAGE_BUCKET)
    results = []
    for url in urls[:5]:  # Max 5 per request
        try:
            result = download_and_store(url, STORAGE_BUCKET, project_id, research_id)
            results.append({
                "url": url,
                "status": "completed" if result.get("status") == "success" else "error",
                "title": result.get("title", ""),
                "filename": result.get("filename", ""),
                "error": result.get("error")
            })
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})

    return jsonify({"results": results})


@app.route("/api/projects/<project_id>/assets/download-all", methods=["GET"])
def download_all_source_documents(project_id):
    """Download all source documents as a ZIP file."""
    import zipfile
    import io

    try:
        # Get all source documents
        docs_ref = db.collection(COLLECTIONS['assets']).where(
            'projectId', '==', project_id
        ).where(
            'isSourceDocument', '==', True
        )

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        bucket = storage_client.bucket(STORAGE_BUCKET)

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs_ref.stream():
                doc_data = doc.to_dict()
                if doc_data.get('gcsPath'):
                    try:
                        blob = bucket.blob(doc_data['gcsPath'])
                        if blob.exists():
                            content = blob.download_as_bytes()
                            filename = doc_data.get('filename') or doc_data['gcsPath'].split('/')[-1]
                            zip_file.writestr(filename, content)
                    except Exception as e:
                        print(f"Error adding {doc_data['gcsPath']} to ZIP: {e}")

        zip_buffer.seek(0)

        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment; filename="source-documents-{project_id[:8]}.zip"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Script Routes ==============

@app.route("/api/projects/<project_id>/scripts", methods=["GET"])
def get_scripts(project_id):
    """Get all scripts for a project."""
    scripts = get_all_docs('scripts', project_id)
    return jsonify(scripts)


@app.route("/api/scripts", methods=["POST"])
def create_script():
    """Create a new script."""
    data = request.get_json()
    script = create_doc('scripts', data)
    return jsonify(script), 201


@app.route("/api/scripts/<script_id>", methods=["PUT"])
def update_script(script_id):
    """Update a script."""
    data = request.get_json()
    script = update_doc('scripts', script_id, data)
    return jsonify(script)


@app.route("/api/scripts/<script_id>", methods=["DELETE"])
def delete_script(script_id):
    """Delete a script."""
    delete_doc('scripts', script_id)
    return jsonify({"success": True})


# ============== Feedback Routes ==============

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Submit user feedback with optional screenshot."""
    data = request.get_json()

    feedback_text = data.get('text', '')
    feedback_type = data.get('type', 'general')
    screenshot_data = data.get('screenshot')
    project_id = data.get('projectId')
    project_title = data.get('projectTitle')
    current_tab = data.get('currentTab')
    user_agent = data.get('userAgent', '')
    screen_size = data.get('screenSize', '')
    timestamp = data.get('timestamp', datetime.utcnow().isoformat())

    if not feedback_text:
        return jsonify({"error": "Feedback text is required"}), 400

    # Save screenshot to GCS if provided
    screenshot_path = None
    if screenshot_data and screenshot_data.startswith('data:image'):
        try:
            # Extract base64 data
            header, base64_data = screenshot_data.split(',', 1)
            image_data = base64.b64decode(base64_data)

            # Generate unique filename
            feedback_id = str(uuid.uuid4())[:8]
            screenshot_filename = f"feedback/{feedback_id}_screenshot.jpg"

            # Upload to GCS
            ensure_bucket_exists(STORAGE_BUCKET)
            bucket = storage_client.bucket(STORAGE_BUCKET)
            blob = bucket.blob(screenshot_filename)
            blob.upload_from_string(image_data, content_type='image/jpeg')

            screenshot_path = screenshot_filename
            print(f"Feedback screenshot saved: {screenshot_filename}")

        except Exception as e:
            print(f"Error saving feedback screenshot: {e}")
            # Continue without screenshot

    # Create feedback document
    feedback_doc = {
        'text': feedback_text,
        'type': feedback_type,
        'name': data.get('name', 'Anonymous'),
        'version': data.get('version', ''),
        'url': data.get('url', ''),
        'screenshotPath': screenshot_path,
        'projectId': project_id,
        'projectTitle': project_title,
        'currentTab': current_tab,
        'userAgent': user_agent,
        'screenSize': screen_size,
        'status': 'new',
        'response': '',
        'createdAt': timestamp,
        'updatedAt': timestamp
    }

    # Save to Firestore
    doc_ref = db.collection(COLLECTIONS['feedback']).document()
    doc_ref.set(feedback_doc)
    feedback_doc['id'] = doc_ref.id

    print(f"Feedback submitted: [{feedback_type}] {feedback_text[:50]}...")

    return jsonify({
        "success": True,
        "id": doc_ref.id,
        "feedbackId": doc_ref.id,
        "message": "Feedback received"
    }), 201


@app.route("/api/feedback", methods=["GET"])
def get_all_feedback():
    """Get all feedback (admin view)."""
    docs = db.collection(COLLECTIONS['feedback']).order_by(
        'createdAt', direction=firestore.Query.DESCENDING
    ).limit(100).stream()

    feedback_list = []
    for doc in docs:
        fb = doc.to_dict()
        fb['id'] = doc.id
        feedback_list.append(fb)

    return jsonify(feedback_list)


@app.route("/api/feedback/<feedback_id>", methods=["PUT"])
def update_feedback_status(feedback_id):
    """Update a feedback entry (status and admin response)."""
    try:
        data = request.get_json()
        update_data = {
            "updatedAt": datetime.utcnow().isoformat()
        }
        if 'status' in data:
            update_data['status'] = data['status']
        if 'response' in data:
            update_data['response'] = data['response']

        doc_ref = db.collection(COLLECTIONS['feedback']).document(feedback_id)
        doc_ref.update(update_data)
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Failed to update feedback: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/blueprint-content", methods=["GET"])
def get_blueprint_content(project_id):
    """Get the blueprint markdown content for a project."""
    project = get_doc('projects', project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Check if project has blueprint content stored
    blueprint_content = project.get('blueprintContent', '')

    if not blueprint_content and project.get('blueprintFile'):
        # Try to extract content from stored document
        try:
            file_path = project['blueprintFile'].get('path', '')
            if file_path:
                bucket = storage_client.bucket(STORAGE_BUCKET)
                blob = bucket.blob(file_path)
                if blob.exists():
                    content = blob.download_as_text()
                    # If it's HTML (from PDF), try to extract text
                    if content.startswith('<!DOCTYPE') or content.startswith('<html'):
                        blueprint_content = "Blueprint document available for download"
                    else:
                        blueprint_content = content
        except Exception as e:
            print(f"Error loading blueprint content: {e}")

    return jsonify({"content": blueprint_content})


@app.route("/api/ai/generate-script", methods=["POST"])
def ai_generate_script():
    """Generate a Quickture-compatible documentary script for an episode."""
    data = request.get_json()
    episode_id = data.get('episodeId', '')
    episode_title = data.get('episodeTitle', '')
    episode_description = data.get('episodeDescription', '')
    project_title = data.get('projectTitle', '')
    project_description = data.get('projectDescription', '')
    project_style = data.get('projectStyle', '')
    project_id = data.get('projectId', '')
    duration = data.get('duration', '45 minutes')

    # Get research for this episode if available
    research_content = ""
    if episode_id:
        research_docs = db.collection(COLLECTIONS['research']).where(
            'episodeId', '==', episode_id
        ).limit(1).stream()
        for doc in research_docs:
            research_content = doc.to_dict().get('content', '')[:5000]
            break

    system_prompt = f"""You are a professional documentary script writer creating scripts optimized for AI-assisted editing tools like Quickture.

## PROJECT CONTEXT
- Project: {project_title}
- Style: {project_style or 'Documentary'}
- Description: {project_description}

## QUICKTURE-COMPATIBLE SCRIPT FORMAT

Create a detailed documentary script that includes:

1. **HEADER SECTION**
   - Episode title and number
   - Target duration
   - Style/tone notes for editors

2. **SCENE BREAKDOWN** (use this format for each scene):
   ```
   SCENE [NUMBER]: [SCENE TITLE]
   Duration: [estimated time]
   Location: [setting]
   Mood: [emotional tone]

   VISUAL:
   [Description of what we see - B-roll, interviews, graphics]

   AUDIO:
   [Narration, interview soundbites, ambient sound, music cues]

   NARRATION:
   "[Exact narration text if any]"

   INTERVIEW BITES:
   - [Subject name]: "[Key quote or topic to cover]"

   B-ROLL NEEDED:
   - [List of specific shots needed]

   GRAPHICS/TEXT:
   - [Any lower thirds, titles, or info graphics]

   TRANSITION:
   [How this scene connects to the next]
   ```

3. **SHOT LIST SUMMARY**
   - Numbered list of all shots with descriptions
   - Technical notes (wide/close, handheld/tripod, etc.)

4. **INTERVIEW GUIDE**
   - Questions for each subject
   - Key points to cover

5. **MUSIC/SOUND DESIGN NOTES**
   - Mood suggestions per scene
   - Transition audio cues

## REQUIREMENTS
- Be specific and actionable for editors
- Include timing estimates for pacing
- Mark emotional beats and story arc moments
- Note any archival footage or graphics needed
- Keep narration concise and documentary-style
"""

    research_section = f"\n\nRESEARCH AVAILABLE:\n{research_content}" if research_content else ""

    prompt = f"""Create a detailed, Quickture-compatible documentary script for:

Episode: {episode_title}
Description: {episode_description}
Target Duration: {duration}
{research_section}

Generate a comprehensive production script with scene breakdowns, shot lists, narration, and interview guides."""

    result = generate_ai_response(prompt, system_prompt)

    # Save the script
    script_data = {
        'projectId': project_id,
        'episodeId': episode_id,
        'title': f"Script: {episode_title}",
        'content': result,
        'format': 'quickture',
        'duration': duration,
        'status': 'Draft'
    }

    if project_id:
        saved_script = create_doc('scripts', script_data)
        return jsonify({
            "script": result,
            "saved": True,
            "scriptId": saved_script['id']
        })

    return jsonify({"script": result, "saved": False})


# ============== AI Routes ==============

@app.route("/api/ai/research", methods=["POST"])
def ai_research():
    """AI research - disabled in this build."""
    return jsonify({
        "result": "AI Research functionality is not available in this build.",
        "sources": [],
        "disabled": True
    })


@app.route("/api/ai/simple-research", methods=["POST"])
def ai_simple_research():
    """Simple AI research query for episode background research."""
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    episode_id = data.get('episodeId', '')
    project_id = data.get('projectId', '')
    save_research = data.get('save', True)

    print(f"[DEBUG] simple-research called: title={title}, episodeId={episode_id}, projectId={project_id}, save={save_research}")

    prompt = f"""I have a documentary episode which is called "{title}": {description}

This requires some research so please do the background research for this.
Please include the source links for all the research.

Format your response with:
- Clear sections with headers
- Bullet points for key facts
- Include real, clickable URLs to credible sources (news sites, Wikipedia, .gov, .edu, .org sites)
- Mark each source with its URL in markdown link format: [Source Name](URL)"""

    system_prompt = """You are a documentary research assistant. Provide comprehensive background research with real source links. Always format URLs as markdown links that can be clicked. Focus on factual, verifiable information from credible sources."""

    result = generate_ai_response(prompt, system_prompt)

    print(f"[DEBUG] AI response length: {len(result)} chars")

    response_data = {
        "result": result,
        "title": title,
        "saved": False
    }

    # Save research to episode if episodeId provided
    if save_research and episode_id and project_id:
        try:
            print(f"[DEBUG] Saving research to episode {episode_id}")
            # Update the episode with the research content
            episode_ref = db.collection(COLLECTIONS['episodes']).document(episode_id)
            episode_ref.update({
                'research': result,
                'researchGeneratedAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            })
            response_data['saved'] = True
            response_data['episodeId'] = episode_id
            print(f"[DEBUG] Research saved successfully to episode {episode_id}")
        except Exception as e:
            print(f"[ERROR] Failed to save research: {e}")
            response_data['saveError'] = str(e)

    return jsonify(response_data)


@app.route("/api/episodes/<episode_id>/research", methods=["GET"])
def get_episode_research(episode_id):
    """Get saved research for an episode."""
    print(f"[DEBUG] Getting research for episode {episode_id}")
    try:
        episode = get_doc('episodes', episode_id)
        if not episode:
            print(f"[DEBUG] Episode {episode_id} not found")
            return jsonify({"error": "Episode not found"}), 404

        research = episode.get('research', '')
        generated_at = episode.get('researchGeneratedAt', '')

        print(f"[DEBUG] Found research: {len(research)} chars, generated at: {generated_at}")

        return jsonify({
            "research": research,
            "generatedAt": generated_at,
            "episodeId": episode_id,
            "episodeTitle": episode.get('title', '')
        })
    except Exception as e:
        print(f"[ERROR] Failed to get research: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/episodes/<episode_id>/research", methods=["DELETE"])
def delete_episode_research(episode_id):
    """Delete saved research for an episode."""
    print(f"[DEBUG] Deleting research for episode {episode_id}")
    try:
        episode_ref = db.collection(COLLECTIONS['episodes']).document(episode_id)
        episode_ref.update({
            'research': '',
            'researchGeneratedAt': '',
            'updatedAt': datetime.utcnow().isoformat()
        })
        print(f"[DEBUG] Research deleted for episode {episode_id}")
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Failed to delete research: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/episodes/<episode_id>/research", methods=["PUT"])
def save_episode_research(episode_id):
    """Save research to an episode and extract links as reference assets."""
    print(f"[DEBUG] Saving research for episode {episode_id}")
    try:
        data = request.get_json()
        research = data.get('research', '')

        if not research:
            return jsonify({"error": "No research content provided"}), 400

        # Get episode to find projectId
        episode_ref = db.collection(COLLECTIONS['episodes']).document(episode_id)
        episode_doc = episode_ref.get()
        if not episode_doc.exists:
            return jsonify({"error": "Episode not found"}), 404

        episode_data = episode_doc.to_dict()
        project_id = episode_data.get('projectId')
        episode_title = episode_data.get('title', 'Unknown Episode')

        # Save research to episode
        episode_ref.update({
            'research': research,
            'researchGeneratedAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        })
        print(f"[DEBUG] Research saved for episode {episode_id}, length: {len(research)}")

        # Extract markdown links and create assets as reference links
        links_created = 0
        markdown_links = []

        if project_id:
            # Find all markdown links: [text](url)
            markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', research)
            print(f"[DEBUG] Found {len(markdown_links)} links in research")

            for link_text, link_url in markdown_links:
                try:
                    # Check if asset with this URL already exists for this project
                    existing = db.collection(COLLECTIONS['assets']).where(
                        'projectId', '==', project_id
                    ).where(
                        'source', '==', link_url
                    ).limit(1).get()

                    if len(list(existing)) > 0:
                        print(f"[DEBUG] Asset already exists for URL: {link_url[:50]}...")
                        continue

                    # Create asset for this link as a reference (link only, no download)
                    asset_data = {
                        "projectId": project_id,
                        "episodeId": episode_id,
                        "title": link_text[:100],
                        "type": "Reference",
                        "source": link_url,
                        "status": "Identified",
                        "isSourceDocument": False,
                        "isResearchLink": True,
                        "sourceEpisode": episode_title,
                        "notes": f"Extracted from research for: {episode_title}",
                        "createdAt": datetime.utcnow().isoformat(),
                        "updatedAt": datetime.utcnow().isoformat()
                    }
                    doc_ref = db.collection(COLLECTIONS['assets']).document()
                    doc_ref.set(asset_data)
                    links_created += 1
                    print(f"[DEBUG] Created asset: {link_text[:50]}...")
                except Exception as link_error:
                    print(f"[ERROR] Failed to create asset for {link_url}: {link_error}")

        print(f"[DEBUG] Created {links_created} new reference assets")
        return jsonify({
            "success": True,
            "episodeId": episode_id,
            "linksExtracted": len(markdown_links),
            "assetsCreated": links_created
        })
    except Exception as e:
        print(f"[ERROR] Failed to save research: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/interview-questions", methods=["POST"])
def ai_interview_questions():
    """Generate interview questions."""
    data = request.get_json()
    subject = data.get('subject', '')
    role = data.get('role', '')
    context = data.get('context', '')
    project_title = data.get('projectTitle', '')

    system_prompt = """You are a documentary interview specialist. Generate thoughtful, open-ended questions that elicit detailed stories and insights. Focus on emotional moments, specific details, and unique perspectives."""

    prompt = f"""Generate 8-10 interview questions for {subject}, who is/was a {role}, for a documentary about "{project_title}".
Focus on: {context}.
Make questions specific, open-ended, and designed to get compelling stories."""

    result = generate_ai_response(prompt, system_prompt)
    return jsonify({"result": result})


@app.route("/api/ai/script-outline", methods=["POST"])
def ai_script_outline():
    """Generate script outline."""
    data = request.get_json()
    title = data.get('title', '')
    topic = data.get('topic', '')
    duration = data.get('duration', '45 minutes')
    project_title = data.get('projectTitle', '')

    system_prompt = """You are a documentary scriptwriter. Create detailed episode outlines with clear acts, narrative arcs, and visual storytelling elements."""

    prompt = f"""Create a detailed outline for a documentary episode titled "{title}" ({duration}) about: {topic}.
This is for the documentary "{project_title}".
Include acts, key beats, narrative arc, and suggested visuals."""

    result = generate_ai_response(prompt, system_prompt)
    return jsonify({"result": result})


@app.route("/api/ai/shot-ideas", methods=["POST"])
def ai_shot_ideas():
    """Generate shot ideas."""
    data = request.get_json()
    scene = data.get('scene', '')
    project_title = data.get('projectTitle', '')

    system_prompt = """You are a documentary cinematographer. Suggest creative, visually compelling shot ideas with specific camera movements, angles, and equipment."""

    prompt = f"""Suggest 5-7 creative shots for: {scene}.
This is for "{project_title}".
Include camera angles, movements, equipment needed, and why each shot would be compelling."""

    result = generate_ai_response(prompt, system_prompt)
    return jsonify({"result": result})


@app.route("/api/ai/expand-topic", methods=["POST"])
def ai_expand_topic():
    """Expand on a topic."""
    data = request.get_json()
    topic = data.get('topic', '')
    project_title = data.get('projectTitle', '')

    system_prompt = """You are a documentary story consultant. Help explore topics by suggesting angles, themes, narrative approaches, and key elements to investigate."""

    prompt = f"""Explore potential angles and approaches for covering "{topic}" in the documentary "{project_title}".
Suggest themes, storylines, key questions to answer, and unique perspectives."""

    result = generate_ai_response(prompt, system_prompt)
    return jsonify({"result": result})


@app.route("/api/ai/episode-research", methods=["POST"])
def ai_episode_research():
    """Episode research - disabled in this build."""
    return jsonify({
        "result": "AI Research functionality is not available in this build.",
        "saved": False,
        "sources": [],
        "disabled": True
    })


@app.route("/api/ai/generate-topics", methods=["POST"])
def ai_generate_topics():
    """Generate episode topics from project title and description."""
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    style = data.get('style', '')
    num_topics = data.get('numTopics', 5)

    system_prompt = """You are a documentary series planner. Generate compelling episode topics that would make a cohesive documentary series.

IMPORTANT: Respond ONLY with a JSON array of episode objects. No markdown, no explanation, just valid JSON.

Each episode object must have:
- "title": A compelling episode title (max 60 chars)
- "description": Brief description of what this episode covers (max 150 chars)
- "order": Episode number (1, 2, 3, etc.)

Example response format:
[
  {"title": "Episode Title Here", "description": "What this episode covers", "order": 1},
  {"title": "Another Episode", "description": "Description of content", "order": 2}
]"""

    style_instruction = f"\nStyle/Approach: {style}\nEnsure all episodes match this documentary style." if style else ""

    prompt = f"""Create {num_topics} episode topics for a documentary series:

Title: {title}
Description: {description}{style_instruction}

Generate episode topics that:
1. Cover the subject comprehensively
2. Have a logical narrative flow
3. Each could stand alone but contribute to the whole
4. Are engaging and specific, not generic

Return ONLY the JSON array, no other text."""

    result = generate_ai_response(prompt, system_prompt)

    # Parse the JSON response
    try:
        # Clean up the response - remove markdown code blocks if present
        cleaned = result.strip()
        if cleaned.startswith('```'):
            # Remove markdown code fence
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])

        import json
        topics = json.loads(cleaned)
        return jsonify({"topics": topics})
    except Exception as e:
        # If parsing fails, return the raw result for debugging
        return jsonify({"topics": [], "raw": result, "error": str(e)})


@app.route("/api/upload/init", methods=["POST"])
def init_chunked_upload():
    """Initialize a chunked upload session for large files."""
    data = request.get_json()
    filename = data.get('filename', 'upload')
    content_type = data.get('contentType', 'application/octet-stream')
    file_size = data.get('fileSize', 0)
    total_chunks = data.get('totalChunks', 1)

    # Generate unique upload ID and blob name
    upload_id = hashlib.md5(f"{filename}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    blob_name = f"uploads/{upload_id}.{ext}"

    return jsonify({
        "uploadId": upload_id,
        "gcsUri": f"gs://{STORAGE_BUCKET}/{blob_name}",
        "blobPath": blob_name,
        "totalChunks": total_chunks
    })


@app.route("/api/upload/chunk/<upload_id>", methods=["POST"])
def upload_chunk(upload_id):
    """Upload a chunk of a large file."""
    chunk_index = int(request.form.get('chunkIndex', 0))
    total_chunks = int(request.form.get('totalChunks', 1))
    blob_path = request.form.get('blobPath', '')
    content_type = request.form.get('contentType', 'application/octet-stream')

    if 'chunk' not in request.files:
        return jsonify({"error": "No chunk data"}), 400

    chunk = request.files['chunk']
    chunk_data = chunk.read()

    try:
        ensure_bucket_exists(STORAGE_BUCKET)
        bucket = storage_client.bucket(STORAGE_BUCKET)

        # Store chunk temporarily
        chunk_blob_name = f"uploads/chunks/{upload_id}/chunk_{chunk_index:04d}"
        chunk_blob = bucket.blob(chunk_blob_name)
        chunk_blob.upload_from_string(chunk_data, content_type='application/octet-stream')

        # If this is the last chunk, combine all chunks
        if chunk_index == total_chunks - 1:
            # List all chunks
            chunk_blobs = list(bucket.list_blobs(prefix=f"uploads/chunks/{upload_id}/"))
            chunk_blobs.sort(key=lambda b: b.name)

            # Combine chunks into final file
            final_blob = bucket.blob(blob_path)

            # Use compose for efficiency (works for up to 32 components)
            if len(chunk_blobs) <= 32:
                final_blob.compose(chunk_blobs)
            else:
                # For more than 32 chunks, we need to compose in stages
                # First, combine all chunk data
                combined_data = b''
                for cb in chunk_blobs:
                    combined_data += cb.download_as_bytes()
                final_blob.upload_from_string(combined_data, content_type=content_type)

            # Clean up chunks
            for cb in chunk_blobs:
                cb.delete()

            return jsonify({
                "status": "complete",
                "gcsUri": f"gs://{STORAGE_BUCKET}/{blob_path}",
                "chunkIndex": chunk_index,
                "totalChunks": total_chunks
            })

        return jsonify({
            "status": "uploaded",
            "chunkIndex": chunk_index,
            "totalChunks": total_chunks
        })

    except Exception as e:
        return jsonify({"error": f"Chunk upload failed: {str(e)}"}), 500


@app.route("/api/ai/analyze-blueprint", methods=["POST"])
def ai_analyze_blueprint():
    """Analyze an uploaded document or video to extract project blueprint.

    Supports two modes:
    1. Direct file upload (for small files < 32MB)
    2. GCS URI (for large files uploaded via signed URL)
    """
    import json
    import tempfile
    import mimetypes
    from vertexai.generative_models import Part

    # Check for GCS URI (for large files uploaded directly to GCS)
    gcs_uri = None
    if request.is_json:
        data = request.get_json()
        gcs_uri = data.get('gcsUri')
        num_episodes = int(data.get('numEpisodes', 5))
        filename = data.get('filename', 'video.mp4')
    else:
        num_episodes = int(request.form.get('numEpisodes', 5))
        gcs_uri = request.form.get('gcsUri')
        filename = request.form.get('filename', '')

    # Mode 1: GCS URI provided (large file already in GCS)
    if gcs_uri:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
        mime_type = mimetypes.guess_type(filename)[0] or 'video/mp4'
        file_content = None  # No content to read, using GCS
        print(f"Analyzing from GCS: {gcs_uri}")

    # Mode 2: Direct file upload (small files)
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        filename = file.filename
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        file_content = file.read()
    else:
        return jsonify({"error": "No file uploaded and no gcsUri provided"}), 400

    system_prompt = """You are a documentary production analyst. Analyze the provided content and create a comprehensive project blueprint document.

IMPORTANT: Respond ONLY with a JSON object. No markdown, no explanation, just valid JSON.

The JSON must have:
- "title": A compelling project title (max 80 chars)
- "description": A comprehensive description of what this documentary should cover (max 500 chars)
- "style": The documentary style/approach that fits best (e.g., "investigative journalism", "observational", "personal narrative", "educational", "cinematic")
- "episodes": An array of episode objects, each with "title", "description", and "order"
- "blueprintDocument": A detailed markdown document (1500-2500 words) that serves as the project blueprint, including:
  * Executive Summary
  * Project Overview and Goals
  * Target Audience
  * Visual Style and Tone
  * Key Themes to Explore
  * Production Approach
  * Episode Breakdown with descriptions
  * Editing Approach (detailed section covering):
    - Pacing and rhythm guidelines
    - Transition styles between scenes/segments
    - Use of B-roll and cutaways
    - Music and sound design direction
    - Graphics and text overlay style
    - Color grading/look recommendations
    - Interview editing approach (jump cuts vs continuous, etc.)
    - Narrative structure and story arc editing
  * Potential Challenges and Considerations

Example response format:
{
  "title": "Documentary Title",
  "description": "What this documentary is about...",
  "style": "investigative journalism",
  "episodes": [
    {"title": "Episode 1 Title", "description": "What this episode covers", "order": 1},
    {"title": "Episode 2 Title", "description": "What this episode covers", "order": 2}
  ],
  "blueprintDocument": "# Project Blueprint\\n\\n## Executive Summary\\n..."
}"""

    try:
        # Determine if it's a video or document
        is_video = mime_type.startswith('video/') or ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']
        is_document = ext in ['pdf', 'txt', 'doc', 'docx', 'md'] or mime_type.startswith('text/')

        # Variable to store blueprint file info
        blueprint_file = None
        source_filename = filename

        if is_video:
            # For videos, use GCS URI for Gemini analysis
            bucket = storage_client.bucket(STORAGE_BUCKET)
            temp_blob = None

            if gcs_uri:
                # Large file already in GCS - use provided URI
                video_uri = gcs_uri
                print(f"Using existing GCS file: {video_uri}")
            else:
                # Small file - upload temporarily to GCS
                file_hash = hashlib.md5(file_content).hexdigest()
                temp_blob_name = f"temp_blueprints/{file_hash}.{ext}"
                temp_blob = bucket.blob(temp_blob_name)
                temp_blob.upload_from_string(file_content, content_type=mime_type)
                video_uri = f"gs://{STORAGE_BUCKET}/{temp_blob_name}"
                print(f"Uploaded temp file: {video_uri}")

            prompt = f"""Analyze this video and create a comprehensive documentary project blueprint.
The video is a reference, sample, or outline for a documentary project.

Based on what you see and hear in the video, create:
1. A compelling project title
2. A comprehensive description
3. The appropriate documentary style
4. {num_episodes} episode topics
5. A detailed blueprint document (1000-2000 words) covering all aspects of the project

Return ONLY the JSON object as specified."""

            # Use multimodal model with video
            video_part = Part.from_uri(video_uri, mime_type=mime_type)
            response = model.generate_content([system_prompt, video_part, prompt])
            result = response.text

            # Delete the temporary video file after analysis (only if we uploaded it)
            if temp_blob:
                def cleanup_video():
                    import time
                    time.sleep(30)
                    try:
                        temp_blob.delete()
                    except:
                        pass
                threading.Thread(target=cleanup_video, daemon=True).start()

        elif is_document:
            # For documents, analyze and generate a blueprint document
            if ext == 'pdf':
                # Use Gemini to analyze PDF
                doc_part = Part.from_data(file_content, mime_type='application/pdf')
                prompt = f"""Analyze this PDF document and create a comprehensive documentary project blueprint.
The document contains information about a documentary project or subject matter.

Based on the content, create:
1. A compelling project title
2. A comprehensive description
3. The appropriate documentary style
4. {num_episodes} episode topics
5. A detailed blueprint document (1000-2000 words) covering all aspects of the project

Return ONLY the JSON object as specified."""

                response = model.generate_content([system_prompt, doc_part, prompt])
                result = response.text
            else:
                # For text files, decode and send as text
                try:
                    text_content = file_content.decode('utf-8')
                except:
                    text_content = file_content.decode('latin-1')

                prompt = f"""Analyze this document and create a comprehensive documentary project blueprint.

DOCUMENT CONTENT:
{text_content[:50000]}

Based on the content, create:
1. A compelling project title
2. A comprehensive description
3. The appropriate documentary style
4. {num_episodes} episode topics
5. A detailed blueprint document (1000-2000 words) covering all aspects of the project

Return ONLY the JSON object as specified."""

                result = generate_ai_response(prompt, system_prompt)
        else:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        # Parse the JSON response
        cleaned = result.strip()
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])

        # Clean control characters that break JSON parsing
        import re
        # Remove all ASCII control characters except newline, tab, carriage return
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        # Also remove extended control characters (0x80-0x9f)
        cleaned = re.sub(r'[\x80-\x9f]', '', cleaned)

        # Fix unescaped newlines inside JSON string values
        # This is a common issue when AI generates long text content
        def fix_json_strings(json_str):
            """Fix newlines inside JSON string values by properly escaping them."""
            result = []
            in_string = False
            escape_next = False

            for char in json_str:
                if escape_next:
                    result.append(char)
                    escape_next = False
                elif char == '\\':
                    result.append(char)
                    escape_next = True
                elif char == '"':
                    result.append(char)
                    in_string = not in_string
                elif char == '\n' and in_string:
                    # Newline inside string - escape it
                    result.append('\\n')
                elif char == '\r' and in_string:
                    # Carriage return inside string - escape it
                    result.append('\\r')
                elif char == '\t' and in_string:
                    # Tab inside string - escape it
                    result.append('\\t')
                else:
                    result.append(char)

            return ''.join(result)

        cleaned = fix_json_strings(cleaned)

        blueprint = json.loads(cleaned)

        # Save the blueprint document to GCS
        blueprint_doc_content = blueprint.get('blueprintDocument', '')
        if not blueprint_doc_content:
            # Generate a basic document if not provided
            blueprint_doc_content = f"""# {blueprint.get('title', 'Documentary Project')}

## Project Overview
{blueprint.get('description', '')}

## Documentary Style
{blueprint.get('style', 'Documentary')}

## Episodes
"""
            for ep in blueprint.get('episodes', []):
                blueprint_doc_content += f"\n### Episode {ep.get('order', '')}: {ep.get('title', '')}\n{ep.get('description', '')}\n"

        # Convert markdown to PDF
        import markdown

        # Convert markdown to HTML
        html_content = markdown.markdown(blueprint_doc_content, extensions=['tables', 'fenced_code'])

        # Create styled HTML document
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #2563eb;
            margin-top: 30px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #4b5563;
            margin-top: 20px;
        }}
        p {{
            margin-bottom: 12px;
        }}
        ul, ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}
        li {{
            margin-bottom: 6px;
        }}
        strong {{
            color: #1a1a1a;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #2563eb;
        }}
        .header h1 {{
            border: none;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #6b7280;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{blueprint.get('title', 'Documentary Blueprint')}</h1>
        <p>Project Blueprint Document</p>
    </div>
    {html_content}
</body>
</html>"""

        # Convert HTML to PDF using WeasyPrint
        pdf_content = HTML(string=styled_html).write_pdf()

        # Save PDF to GCS
        bucket = storage_client.bucket(STORAGE_BUCKET)
        doc_hash = hashlib.md5(blueprint_doc_content.encode()).hexdigest()
        doc_blob_name = f"blueprints/{doc_hash}_blueprint.pdf"
        doc_blob = bucket.blob(doc_blob_name)
        doc_blob.upload_from_string(pdf_content, content_type='application/pdf')

        # Create blueprint file info for the document
        blueprint["blueprintFile"] = {
            "path": doc_blob_name,
            "filename": f"{blueprint.get('title', 'Blueprint')[:50]}_blueprint.pdf",
            "mimeType": "application/pdf",
            "size": len(pdf_content),
            "type": "document",
            "sourceFile": source_filename if is_video else None
        }

        # Include the markdown content for inline display
        blueprint["blueprintContent"] = blueprint_doc_content

        return jsonify({"blueprint": blueprint})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Document Serving Routes ==============

@app.route("/api/document/<path:blob_path>")
def get_document(blob_path):
    """Serve a document from GCS (inline viewing)."""
    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(blob_path)

        if not blob.exists():
            return jsonify({"error": "Document not found"}), 404

        content = blob.download_as_bytes()
        content_type = blob.content_type or 'application/octet-stream'

        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'inline; filename="{blob_path.split("/")[-1]}"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<path:blob_path>")
def download_document(blob_path):
    """Download a document from GCS (attachment)."""
    try:
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(blob_path)

        if not blob.exists():
            return jsonify({"error": "Document not found"}), 404

        content = blob.download_as_bytes()
        content_type = blob.content_type or 'application/octet-stream'
        filename = blob_path.split("/")[-1]

        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/source-documents", methods=["GET"])
def get_source_documents(project_id):
    """Get all source documents for a project."""
    try:
        docs_ref = db.collection(COLLECTIONS['assets']).where(
            'projectId', '==', project_id
        ).where(
            'isSourceDocument', '==', True
        )
        documents = []
        for doc in docs_ref.stream():
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            documents.append(doc_data)
        return jsonify(documents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Initialize Sample Data ==============

@app.route("/api/init-sample-data", methods=["POST"])
def init_sample_data():
    """Initialize sample data for testing."""
    # Check if project already exists
    existing = list(db.collection(COLLECTIONS['projects']).limit(1).stream())
    if existing:
        return jsonify({"message": "Data already exists", "projectId": existing[0].id})

    # Create sample project
    project_data = {
        'title': 'Apollo 11: Journey to the Moon',
        'description': 'A comprehensive documentary series exploring the historic first moon landing',
        'status': 'In Production'
    }
    project = create_doc('projects', project_data)
    project_id = project['id']

    # Create sample episodes
    episodes = [
        {'projectId': project_id, 'title': 'Episode 1: The Race Begins', 'description': 'Cold War context and the space race', 'status': 'Research', 'duration': '45 min'},
        {'projectId': project_id, 'title': 'Episode 2: Preparation', 'description': 'Training and technical development', 'status': 'Planning', 'duration': '45 min'},
        {'projectId': project_id, 'title': 'Episode 3: Launch', 'description': 'The Saturn V launch and journey to the moon', 'status': 'Planning', 'duration': '45 min'},
        {'projectId': project_id, 'title': 'Episode 4: One Small Step', 'description': 'The lunar landing and moonwalk', 'status': 'Planning', 'duration': '45 min'}
    ]
    for ep in episodes:
        create_doc('episodes', ep)

    # Create sample research
    research_items = [
        {'projectId': project_id, 'title': 'NASA Archives Access', 'content': 'Contact: Dr. Sarah Mitchell at NASA History Office. Available footage includes mission control audio, cockpit recordings, and technical schematics.', 'category': 'Archive'},
        {'projectId': project_id, 'title': 'Cold War Context Research', 'content': 'Key sources: "The Right Stuff" by Tom Wolfe, Smithsonian Air & Space Museum archives, Kennedy Space Center historical records.', 'category': 'Background'}
    ]
    for r in research_items:
        create_doc('research', r)

    # Create sample interviews
    interviews = [
        {'projectId': project_id, 'subject': 'Buzz Aldrin', 'role': 'Lunar Module Pilot', 'status': 'Confirmed', 'questions': 'What were your thoughts during descent?\nDescribe the moment of landing.\nWhat did the lunar surface feel like?', 'notes': 'Available for 2-hour interview in Los Angeles'},
        {'projectId': project_id, 'subject': 'Gene Kranz', 'role': 'Flight Director', 'status': 'Requested', 'questions': 'Describe mission control during landing.\nWhat was the most critical moment?\nHow did the team prepare?', 'notes': 'Contact through NASA public affairs'}
    ]
    for i in interviews:
        create_doc('interviews', i)

    # Create sample shots
    shots = [
        {'projectId': project_id, 'description': 'Kennedy Space Center launch pads - modern day', 'location': 'KSC, Florida', 'equipment': '4K drone, cinema camera', 'status': 'Scheduled', 'shootDate': '2026-03-15'},
        {'projectId': project_id, 'description': 'Saturn V rocket at Space Center Houston', 'location': 'Houston, TX', 'equipment': 'Gimbal, 4K camera', 'status': 'Pending'}
    ]
    for s in shots:
        create_doc('shots', s)

    # Create sample assets
    assets = [
        {'projectId': project_id, 'title': 'Original Mission Control Audio', 'type': 'Audio', 'source': 'NASA Archives', 'status': 'Acquired', 'notes': 'Full 8-day mission audio, needs editing'},
        {'projectId': project_id, 'title': 'Apollo 11 Launch Footage', 'type': 'Video', 'source': 'NASA/CBS News Archives', 'status': 'Licensing', 'notes': 'Multiple camera angles, 16mm film transfer'},
        {'projectId': project_id, 'title': 'Lunar Surface Photos', 'type': 'Image', 'source': 'NASA/Hasselblad', 'status': 'Acquired', 'notes': 'High-res scans of original photos'}
    ]
    for a in assets:
        create_doc('assets', a)

    # Create sample script
    script = {
        'projectId': project_id,
        'title': 'Episode 1 Outline',
        'content': '''ACT 1: COLD WAR CONTEXT
- Sputnik shock (1957)
- Kennedy's moon speech (1961)
- Early Mercury/Gemini programs

ACT 2: THE APOLLO PROGRAM
- Tragedy of Apollo 1
- Technical challenges
- Team assembly

ACT 3: APOLLO 11 CREW
- Armstrong, Aldrin, Collins selection
- Training montage
- Mission objectives'''
    }
    create_doc('scripts', script)

    return jsonify({"message": "Sample data created", "projectId": project_id})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
