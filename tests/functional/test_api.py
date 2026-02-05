"""
Functional tests for API endpoints.
"""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, app_client):
        """Test health endpoint returns 200 OK."""
        response = app_client.get('/health')

        assert response.status_code == 200

    def test_health_returns_json(self, app_client):
        """Test health endpoint returns JSON with status."""
        response = app_client.get('/health')
        data = json.loads(response.data)

        assert 'status' in data
        assert data['status'] == 'healthy'


class TestIndexEndpoint:
    """Tests for main index endpoint."""

    def test_index_returns_200(self, app_client):
        """Test index endpoint returns 200 OK."""
        response = app_client.get('/')

        assert response.status_code == 200

    def test_index_returns_html(self, app_client):
        """Test index endpoint returns HTML content."""
        response = app_client.get('/')

        assert b'<!DOCTYPE html>' in response.data
        assert b'AiM' in response.data


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_served(self, app_client):
        """Test CSS files are served correctly."""
        response = app_client.get('/static/css/styles.css')

        assert response.status_code == 200
        assert b'box-sizing' in response.data

    def test_js_served(self, app_client):
        """Test JavaScript files are served correctly."""
        response = app_client.get('/static/js/app.js')

        assert response.status_code == 200
        assert b'state' in response.data

    def test_nonexistent_static_returns_404(self, app_client):
        """Test that nonexistent static file returns 404."""
        response = app_client.get('/static/nonexistent.xyz')

        assert response.status_code == 404


class TestProjectsAPI:
    """Tests for projects API endpoints."""

    @patch('app.get_all_docs')
    def test_get_projects(self, mock_get_all, app_client, sample_project):
        """Test GET /api/projects returns list of projects."""
        mock_get_all.return_value = [sample_project]

        response = app_client.get('/api/projects')
        data = json.loads(response.data)

        assert response.status_code == 200
        # API returns list directly
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Test Documentary'

    @patch('app.create_doc')
    def test_create_project(self, mock_create, app_client):
        """Test POST /api/projects creates a project."""
        mock_create.return_value = 'new-project-id'

        response = app_client.post('/api/projects',
            data=json.dumps({
                'name': 'New Project',
                'description': 'A new test project'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)

        # API returns 201 CREATED for new resources
        assert response.status_code == 201
        assert 'id' in data
        mock_create.assert_called_once()

    @patch('app.get_doc')
    def test_get_project_by_id(self, mock_get, app_client, sample_project):
        """Test GET /api/projects/<id> returns specific project."""
        mock_get.return_value = sample_project

        response = app_client.get('/api/projects/test-project-1')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['name'] == 'Test Documentary'

    @patch('app.get_doc')
    def test_get_nonexistent_project(self, mock_get, app_client):
        """Test GET /api/projects/<id> returns 404 for nonexistent."""
        mock_get.return_value = None

        response = app_client.get('/api/projects/nonexistent-id')

        assert response.status_code == 404

    @patch('app.update_doc')
    def test_update_project(self, mock_update, app_client):
        """Test PUT /api/projects/<id> updates a project."""
        mock_update.return_value = None

        response = app_client.put('/api/projects/test-project-1',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        mock_update.assert_called_once()

    @patch('app.db')
    @patch('app.delete_doc')
    def test_delete_project(self, mock_delete, mock_db, app_client):
        """Test DELETE /api/projects/<id> deletes a project."""
        # Mock Firestore collection operations
        mock_collection = MagicMock()
        mock_collection.where.return_value.stream.return_value = iter([])
        mock_db.collection.return_value = mock_collection
        mock_delete.return_value = None

        response = app_client.delete('/api/projects/test-project-1')

        assert response.status_code == 200


class TestEpisodesAPI:
    """Tests for episodes API endpoints."""

    @patch('app.get_all_docs')
    def test_get_episodes_by_project(self, mock_get_all, app_client, sample_episode):
        """Test GET /api/projects/<id>/episodes returns episodes."""
        mock_get_all.return_value = [sample_episode]

        response = app_client.get('/api/projects/test-project-1/episodes')
        data = json.loads(response.data)

        assert response.status_code == 200
        # API returns list directly
        assert isinstance(data, list)
        assert len(data) == 1

    @patch('app.create_doc')
    def test_create_episode(self, mock_create, app_client):
        """Test POST /api/episodes creates an episode."""
        mock_create.return_value = {'id': 'new-episode-id', 'title': 'New Episode'}

        response = app_client.post('/api/episodes',
            data=json.dumps({
                'project_id': 'test-project-1',
                'title': 'New Episode',
                'code': 'EP01'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)

        # Returns 201 CREATED
        assert response.status_code == 201
        assert 'id' in data

    @patch('app.update_doc')
    def test_update_episode(self, mock_update, app_client):
        """Test PUT /api/episodes/<id> updates an episode."""
        mock_update.return_value = None

        response = app_client.put('/api/episodes/test-episode-1',
            data=json.dumps({'title': 'Updated Title'}),
            content_type='application/json'
        )

        assert response.status_code == 200


class TestResearchAPI:
    """Tests for research API endpoints."""

    @patch('app.get_all_docs')
    def test_get_research_by_project(self, mock_get_all, app_client, sample_research):
        """Test GET /api/projects/<id>/research returns research docs."""
        mock_get_all.return_value = [sample_research]

        response = app_client.get('/api/projects/test-project-1/research')
        data = json.loads(response.data)

        assert response.status_code == 200
        # API returns list directly
        assert isinstance(data, list)

    @patch('app.create_doc')
    def test_create_research(self, mock_create, app_client):
        """Test POST /api/research creates a research document."""
        mock_create.return_value = 'new-research-id'

        response = app_client.post('/api/research',
            data=json.dumps({
                'project_id': 'test-project-1',
                'episode_id': 'test-episode-1',
                'title': 'Research Topic'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)

        # API returns 201 for created resources
        assert response.status_code == 201
        assert 'id' in data


class TestWorkflowAPI:
    """Tests for workflow-related API endpoints."""

    @patch('app.get_episode_workflow_status')
    def test_get_workflow_status(self, mock_get_status, app_client, sample_workflow_status):
        """Test GET /api/episodes/<id>/workflow returns workflow status."""
        mock_get_status.return_value = sample_workflow_status

        response = app_client.get('/api/episodes/test-episode-1/workflow')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert 'research' in data
        assert 'archive' in data

    @patch('app.update_episode_phase')
    def test_update_phase_status(self, mock_update, app_client):
        """Test PUT /api/episodes/<id>/workflow/phase updates phase."""
        mock_update.return_value = {'status': 'approved', 'progress': 100}

        # Correct route: /api/episodes/<id>/workflow/phase
        # Valid statuses: pending, in_progress, review, approved, rejected
        response = app_client.put('/api/episodes/test-episode-1/workflow/phase',
            data=json.dumps({'phase': 'research', 'status': 'approved'}),
            content_type='application/json'
        )

        assert response.status_code == 200


class TestArchiveAPI:
    """Tests for archive-related API endpoints."""

    @patch('app.get_docs_by_episode')
    def test_get_archive_logs(self, mock_get_docs, app_client):
        """Test GET /api/episodes/<id>/archive-logs returns archive logs."""
        mock_get_docs.return_value = [
            {'id': 'log-1', 'filename': 'video.mp4', 'category': 'video'}
        ]

        response = app_client.get('/api/episodes/test-episode-1/archive-logs')
        data = json.loads(response.data)

        assert response.status_code == 200
        # API returns list directly
        assert isinstance(data, list)


class TestComplianceAPI:
    """Tests for compliance-related API endpoints."""

    @patch('app.get_docs_by_episode')
    def test_get_compliance_items(self, mock_get_docs, app_client):
        """Test GET /api/episodes/<id>/compliance returns compliance items."""
        mock_get_docs.return_value = [
            {'id': 'item-1', 'type': 'source_citation', 'status': 'pending'}
        ]

        response = app_client.get('/api/episodes/test-episode-1/compliance')
        data = json.loads(response.data)

        assert response.status_code == 200
        # API returns list directly
        assert isinstance(data, list)
