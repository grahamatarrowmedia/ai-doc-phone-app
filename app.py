"""
Documentary Production App - Flask backend with Firestore and Vertex AI
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel

app = Flask(__name__)

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.0-flash-001")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_NAME)

# Initialize Firestore
db = firestore.Client()

# Collection names
COLLECTIONS = {
    'projects': 'doc_projects',
    'episodes': 'doc_episodes',
    'research': 'doc_research',
    'interviews': 'doc_interviews',
    'shots': 'doc_shots',
    'assets': 'doc_assets',
    'scripts': 'doc_scripts'
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


# ============== Routes ==============

@app.route("/")
def index():
    """Render the main app interface."""
    return render_template("index.html")


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
    """Delete a project."""
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
    """Delete an asset."""
    delete_doc('assets', asset_id)
    return jsonify({"success": True})


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


# ============== AI Routes ==============

@app.route("/api/ai/research", methods=["POST"])
def ai_research():
    """AI-assisted research."""
    data = request.get_json()
    query = data.get('query', '')
    project_context = data.get('projectContext', '')

    system_prompt = f"""You are a documentary research assistant. Help find sources, archives, contacts, and background information. Be specific and actionable.

Project context: {project_context}"""

    result = generate_ai_response(query, system_prompt)
    return jsonify({"result": result})


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
