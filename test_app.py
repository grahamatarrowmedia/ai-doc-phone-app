"""
Documentary Production App - Local test version with mocked responses
No GCP dependencies required for UI testing
"""
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory storage for testing
storage = {
    'projects': [],
    'episodes': [],
    'research': [],
    'interviews': [],
    'shots': [],
    'assets': [],
    'scripts': []
}


def init_sample_data():
    """Initialize sample data."""
    if storage['projects']:
        return storage['projects'][0]['id']

    project_id = str(uuid.uuid4())

    storage['projects'] = [{
        'id': project_id,
        'title': 'Apollo 11: Journey to the Moon',
        'description': 'A comprehensive documentary series exploring the historic first moon landing',
        'status': 'In Production',
        'createdAt': datetime.utcnow().isoformat()
    }]

    storage['episodes'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Episode 1: The Race Begins', 'description': 'Cold War context and the space race', 'status': 'Research', 'duration': '45 min'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Episode 2: Preparation', 'description': 'Training and technical development', 'status': 'Planning', 'duration': '45 min'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Episode 3: Launch', 'description': 'The Saturn V launch and journey to the moon', 'status': 'Planning', 'duration': '45 min'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Episode 4: One Small Step', 'description': 'The lunar landing and moonwalk', 'status': 'Planning', 'duration': '45 min'}
    ]

    storage['research'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'NASA Archives Access', 'content': 'Contact: Dr. Sarah Mitchell at NASA History Office.', 'category': 'Archive'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Cold War Context', 'content': 'Key sources: "The Right Stuff" by Tom Wolfe', 'category': 'Background'}
    ]

    storage['interviews'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'subject': 'Buzz Aldrin', 'role': 'Lunar Module Pilot', 'status': 'Confirmed', 'questions': 'What were your thoughts during descent?', 'notes': 'Available for 2-hour interview'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'subject': 'Gene Kranz', 'role': 'Flight Director', 'status': 'Requested', 'questions': 'Describe mission control during landing.', 'notes': 'Contact through NASA'}
    ]

    storage['shots'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'description': 'Kennedy Space Center launch pads', 'location': 'KSC, Florida', 'equipment': '4K drone', 'status': 'Scheduled', 'shootDate': '2026-03-15'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'description': 'Saturn V rocket at Space Center Houston', 'location': 'Houston, TX', 'equipment': 'Gimbal, 4K camera', 'status': 'Pending'}
    ]

    storage['assets'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Mission Control Audio', 'type': 'Audio', 'source': 'NASA Archives', 'status': 'Acquired', 'notes': 'Full mission audio'},
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Apollo 11 Launch Footage', 'type': 'Video', 'source': 'NASA/CBS', 'status': 'Licensing', 'notes': '16mm film transfer'}
    ]

    storage['scripts'] = [
        {'id': str(uuid.uuid4()), 'projectId': project_id, 'title': 'Episode 1 Outline', 'content': 'ACT 1: COLD WAR CONTEXT\n- Sputnik shock (1957)\n- Kennedy\'s moon speech (1961)'}
    ]

    return project_id


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "mode": "test"})


# Project routes
@app.route("/api/projects", methods=["GET"])
def get_projects():
    return jsonify(storage['projects'])


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    data['id'] = str(uuid.uuid4())
    data['createdAt'] = datetime.utcnow().isoformat()
    storage['projects'].append(data)
    return jsonify(data), 201


@app.route("/api/init-sample-data", methods=["POST"])
def init_data():
    project_id = init_sample_data()
    return jsonify({"message": "Sample data created", "projectId": project_id})


# Generic CRUD for collections
def get_collection_routes(collection_name):
    @app.route(f"/api/projects/<project_id>/{collection_name}", methods=["GET"])
    def get_items(project_id):
        items = [i for i in storage[collection_name] if i.get('projectId') == project_id]
        return jsonify(items)
    get_items.__name__ = f"get_{collection_name}"

    @app.route(f"/api/{collection_name}", methods=["POST"])
    def create_item():
        data = request.get_json()
        data['id'] = str(uuid.uuid4())
        data['createdAt'] = datetime.utcnow().isoformat()
        storage[collection_name].append(data)
        return jsonify(data), 201
    create_item.__name__ = f"create_{collection_name}"

    @app.route(f"/api/{collection_name}/<item_id>", methods=["PUT"])
    def update_item(item_id):
        data = request.get_json()
        for i, item in enumerate(storage[collection_name]):
            if item['id'] == item_id:
                storage[collection_name][i].update(data)
                return jsonify(storage[collection_name][i])
        return jsonify({"error": "Not found"}), 404
    update_item.__name__ = f"update_{collection_name}"

    @app.route(f"/api/{collection_name}/<item_id>", methods=["DELETE"])
    def delete_item(item_id):
        storage[collection_name] = [i for i in storage[collection_name] if i['id'] != item_id]
        return jsonify({"success": True})
    delete_item.__name__ = f"delete_{collection_name}"


# Register routes for all collections
for collection in ['episodes', 'research', 'interviews', 'shots', 'assets', 'scripts']:
    get_collection_routes(collection)


# AI routes (mocked)
@app.route("/api/ai/research", methods=["POST"])
def ai_research():
    data = request.get_json()
    return jsonify({"result": f"""## Research Results for: {data.get('query', 'your query')}

### Suggested Sources
1. **NASA History Office** - Primary source for Apollo documentation
2. **Smithsonian Air & Space Museum** - Extensive artifact collection
3. **Kennedy Space Center Archives** - Launch documentation

### Key Contacts
- Dr. Sarah Mitchell, NASA Historian
- Space Center Houston Research Department

### Next Steps
1. Submit FOIA request for classified documents
2. Schedule archive visit
3. Contact listed experts for interviews

*This is a mock AI response for testing purposes.*"""})


@app.route("/api/ai/interview-questions", methods=["POST"])
def ai_interview():
    data = request.get_json()
    return jsonify({"result": f"""## Interview Questions for {data.get('subject', 'Subject')}
Role: {data.get('role', 'Role')}

1. Can you describe the moment you first learned you would be part of this mission?
2. What was going through your mind during the most critical moments?
3. How did the training prepare you for the unexpected?
4. What surprised you most about the experience?
5. How has this shaped your perspective on life?
6. What would you want future generations to understand?
7. Were there moments of doubt, and how did you overcome them?
8. What was the team dynamic like during high-pressure situations?

*This is a mock AI response for testing purposes.*"""})


@app.route("/api/ai/script-outline", methods=["POST"])
def ai_script():
    data = request.get_json()
    return jsonify({"result": f"""## Script Outline: {data.get('title', 'Episode')}
Duration: {data.get('duration', '45 minutes')}

### ACT 1: SETUP (0:00 - 10:00)
- Opening hook with archival footage
- Introduce main characters/subjects
- Establish the stakes and context

### ACT 2: DEVELOPMENT (10:00 - 30:00)
- Deep dive into the main narrative
- Expert interviews and analysis
- Build tension toward climax

### ACT 3: RESOLUTION (30:00 - 45:00)
- Climactic sequence
- Reflect on significance
- Closing thoughts and legacy

### VISUAL ELEMENTS
- Archival footage integration
- Modern interviews
- Graphics and animation

*This is a mock AI response for testing purposes.*"""})


@app.route("/api/ai/shot-ideas", methods=["POST"])
def ai_shots():
    data = request.get_json()
    return jsonify({"result": f"""## Shot Ideas for: {data.get('scene', 'Scene')}

1. **Wide Establishing Shot**
   - Drone flyover at golden hour
   - Equipment: DJI Inspire 3, 4K

2. **Detail Close-ups**
   - Macro lens on artifacts/documents
   - Equipment: 100mm macro, slider

3. **Interview Setup**
   - Two-camera setup with rim lighting
   - Equipment: Cinema cameras, softboxes

4. **B-Roll Sequence**
   - Slow motion environmental details
   - Equipment: High-speed camera

5. **Time-lapse**
   - Day-to-night transition
   - Equipment: Intervalometer, stabilized mount

*This is a mock AI response for testing purposes.*"""})


@app.route("/api/ai/expand-topic", methods=["POST"])
def ai_expand():
    data = request.get_json()
    return jsonify({"result": f"""## Topic Exploration: {data.get('topic', 'Topic')}

### Potential Angles
1. **Human Interest** - Personal stories and sacrifices
2. **Technical Achievement** - Engineering challenges overcome
3. **Historical Context** - Political and social factors
4. **Legacy** - Long-term impact and relevance today

### Key Themes
- Courage in the face of uncertainty
- Collaboration and teamwork
- Innovation under pressure
- The cost of progress

### Story Threads to Explore
- Untold stories from behind the scenes
- International perspective
- What-if scenarios
- Modern parallels

*This is a mock AI response for testing purposes.*"""})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Documentary Production App - LOCAL TEST MODE")
    print("  AI responses are mocked (no GCP required)")
    print("=" * 50)
    print("\n  Open: http://localhost:5000\n")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
