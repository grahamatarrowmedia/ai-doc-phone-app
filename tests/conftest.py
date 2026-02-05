"""
Pytest configuration and fixtures for AiM Documentary Workflow tests.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ['APP_ENV'] = 'test'
os.environ['GCP_PROJECT_ID'] = 'test-project'


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    with patch('app.db') as mock_db:
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        yield mock_db


@pytest.fixture
def mock_storage():
    """Mock Cloud Storage client."""
    with patch('app.storage_client') as mock_storage:
        mock_bucket = MagicMock()
        mock_storage.bucket.return_value = mock_bucket
        yield mock_storage


@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI model."""
    with patch('app.model') as mock_model:
        mock_response = MagicMock()
        mock_response.text = "Test AI response"
        mock_model.generate_content.return_value = mock_response
        yield mock_model


@pytest.fixture
def app_client():
    """Create Flask test client."""
    # Import here to avoid initialization issues
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        'id': 'test-project-1',
        'name': 'Test Documentary',
        'description': 'A test documentary project',
        'type': 'DOCUMENTARY',
        'created_at': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_episode():
    """Sample episode data."""
    return {
        'id': 'test-episode-1',
        'project_id': 'test-project-1',
        'title': 'Episode 1: The Beginning',
        'code': 'EP01',
        'synopsis': 'The first episode',
        'current_phase': 'research',
        'phase_progress': 0
    }


@pytest.fixture
def sample_research():
    """Sample research document data."""
    return {
        'id': 'test-research-1',
        'project_id': 'test-project-1',
        'episode_id': 'test-episode-1',
        'title': 'Research Topic',
        'query': 'What are the key facts?',
        'status': 'completed',
        'findings': 'Key findings here'
    }


@pytest.fixture
def sample_workflow_status():
    """Sample workflow status."""
    return {
        'research': {'status': 'in_progress', 'progress': 50},
        'archive': {'status': 'pending', 'progress': 0},
        'script': {'status': 'pending', 'progress': 0},
        'voiceover': {'status': 'pending', 'progress': 0},
        'assembly': {'status': 'pending', 'progress': 0}
    }
