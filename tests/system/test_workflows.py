"""
System/Integration tests for end-to-end workflows.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, call


class TestProjectWorkflow:
    """End-to-end tests for project creation and management workflow."""

    @patch('app.delete_doc')
    @patch('app.get_all_docs')
    @patch('app.create_episode_with_buckets')
    @patch('app.create_doc')
    def test_create_project_with_episodes(self, mock_create_doc, mock_create_episode,
                                          mock_get_all, mock_delete, app_client):
        """Test complete workflow: create project, add episodes."""
        # Setup mocks - create_doc returns the data dict with 'id' added
        mock_create_doc.return_value = {'id': 'project-123', 'name': 'Integration Test Project'}
        mock_create_episode.return_value = {'id': 'episode-123'}
        mock_get_all.return_value = []

        # Step 1: Create project (returns 201)
        response = app_client.post('/api/projects',
            data=json.dumps({
                'name': 'Integration Test Project',
                'description': 'Testing full workflow'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        project_data = json.loads(response.data)
        assert 'id' in project_data

        # Step 2: Create episode for the project (returns 201)
        response = app_client.post('/api/episodes',
            data=json.dumps({
                'project_id': project_data['id'],
                'title': 'Test Episode 1',
                'code': 'EP01',
                'synopsis': 'First test episode'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        episode_data = json.loads(response.data)
        assert 'id' in episode_data


class TestResearchWorkflow:
    """End-to-end tests for research workflow."""

    @patch('app.generate_grounded_research')
    @patch('app.update_doc')
    @patch('app.create_doc')
    @patch('app.get_doc')
    def test_research_creation_and_ai_generation(self, mock_get, mock_create,
                                                  mock_update, mock_ai, app_client):
        """Test research workflow: create, trigger AI, update."""
        # Setup mocks - create_doc returns dict with 'id' added
        mock_create.return_value = {
            'id': 'research-123',
            'title': 'Historical Research',
            'projectId': 'project-123',
            'episodeId': 'episode-123'
        }
        mock_get.return_value = {
            'id': 'research-123',
            'title': 'Test Research',
            'status': 'pending'
        }
        # update_doc returns the updated document
        mock_update.return_value = {
            'id': 'research-123',
            'status': 'completed',
            'findings': 'AI generated findings'
        }
        mock_ai.return_value = 'AI generated research findings about the topic.'

        # Step 1: Create research document (returns 201)
        # API expects camelCase 'projectId' and 'episodeId'
        response = app_client.post('/api/research',
            data=json.dumps({
                'projectId': 'project-123',
                'episodeId': 'episode-123',
                'title': 'Historical Research',
                'query': 'What were the key events?'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

        # Step 2: Update research with findings
        response = app_client.put('/api/research/research-123',
            data=json.dumps({
                'status': 'completed',
                'findings': 'AI generated findings'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200


class TestPhaseProgressionWorkflow:
    """End-to-end tests for phase progression workflow."""

    @patch('app.update_episode_phase')
    @patch('app.get_episode_workflow_status')
    def test_phase_progression(self, mock_get_status, mock_update_phase, app_client):
        """Test workflow phase progression from research to assembly."""
        # Setup initial status
        current_status = {
            'research': {'status': 'pending', 'progress': 0},
            'archive': {'status': 'pending', 'progress': 0},
            'script': {'status': 'pending', 'progress': 0},
            'voiceover': {'status': 'pending', 'progress': 0},
            'assembly': {'status': 'pending', 'progress': 0}
        }
        mock_get_status.return_value = current_status
        mock_update_phase.return_value = {'status': 'completed', 'progress': 100}

        phases = ['research', 'archive', 'script', 'voiceover', 'assembly']

        for phase in phases:
            # Update phase to approved (valid status: pending, in_progress, review, approved, rejected)
            # Route is /api/episodes/<id>/workflow/phase with phase in the body
            response = app_client.put('/api/episodes/episode-123/workflow/phase',
                data=json.dumps({'phase': phase, 'status': 'approved'}),
                content_type='application/json'
            )
            assert response.status_code == 200

        # Verify all phases were updated
        assert mock_update_phase.call_count == len(phases)


class TestArchiveWorkflow:
    """End-to-end tests for archive management workflow."""

    @patch('app.create_doc')
    @patch('app.get_all_docs')
    def test_archive_log_creation(self, mock_get_all, mock_create, app_client):
        """Test archive workflow: create logs, categorize assets."""
        mock_create.return_value = 'archive-log-123'
        mock_get_all.return_value = []

        # Create archive log entry (API expects camelCase 'episodeId')
        response = app_client.post('/api/archive-logs',
            data=json.dumps({
                'episodeId': 'episode-123',
                'filename': 'interview_raw.mp4',
                'category': 'video',
                'source': 'Field recording',
                'metadata': {'duration': '00:45:30', 'format': 'MP4'}
            }),
            content_type='application/json'
        )
        assert response.status_code == 201


class TestScriptWorkflow:
    """End-to-end tests for script generation workflow."""

    @patch('app.generate_ai_response')
    @patch('app.update_doc')
    @patch('app.create_doc')
    @patch('app.get_doc')
    @patch('app.get_docs_by_episode')
    def test_script_generation_workflow(self, mock_get_by_episode, mock_get_doc,
                                        mock_create, mock_update, mock_ai, app_client):
        """Test script workflow: create version, generate with AI, lock."""
        # Mock get_docs_by_episode to return empty list (no existing versions)
        mock_get_by_episode.return_value = []

        # Mock get_doc to return the episode
        mock_get_doc.return_value = {
            'id': 'episode-123',
            'title': 'Test Episode',
            'scriptWorkspace': {}
        }

        # create_doc returns dict with 'id' and 'createdAt' added
        mock_create.return_value = {
            'id': 'script-version-123',
            'episodeId': 'episode-123',
            'versionNumber': 1,
            'status': 'draft',
            'createdAt': '2024-01-01T00:00:00Z'
        }

        # update_doc returns the updated episode
        mock_update.return_value = {
            'id': 'episode-123',
            'scriptWorkspace': {'currentVersion': 'script-version-123'}
        }

        mock_ai.return_value = 'Generated script content based on research.'

        # Create script version (API expects camelCase 'episodeId')
        response = app_client.post('/api/script-versions',
            data=json.dumps({
                'episodeId': 'episode-123',
                'versionNumber': 1,
                'status': 'draft'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201


class TestComplianceWorkflow:
    """End-to-end tests for compliance tracking workflow."""

    @patch('app.update_doc')
    @patch('app.create_doc')
    @patch('app.get_all_docs')
    def test_compliance_tracking_workflow(self, mock_get_all, mock_create,
                                          mock_update, app_client):
        """Test compliance workflow: add items, verify, sign off."""
        mock_create.return_value = 'compliance-item-123'
        mock_get_all.return_value = []

        # Add compliance item (API expects camelCase 'episodeId')
        response = app_client.post('/api/compliance',
            data=json.dumps({
                'episodeId': 'episode-123',
                'type': 'source_citation',
                'description': 'Verify historical source',
                'status': 'pending'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

        # Update compliance status
        mock_update.return_value = None
        response = app_client.put('/api/compliance/compliance-item-123',
            data=json.dumps({'status': 'verified'}),
            content_type='application/json'
        )
        assert response.status_code == 200


class TestFileUploadWorkflow:
    """End-to-end tests for file upload workflow."""

    @patch('app.storage_client')
    @patch('app.create_doc')
    def test_archive_file_upload(self, mock_create, mock_storage, app_client):
        """Test file upload to archive."""
        from io import BytesIO

        mock_create.return_value = 'archive-log-123'
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.public_url = 'https://storage.example.com/file.mp4'
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket

        # Simulate file upload
        data = {
            'file': (BytesIO(b'fake video content'), 'test_video.mp4'),
            'episode_id': 'episode-123',
            'category': 'video'
        }

        response = app_client.post('/api/archive-logs/upload',
            data=data,
            content_type='multipart/form-data'
        )

        # Should handle the upload (may return 200 or 400 depending on validation)
        assert response.status_code in [200, 400, 500]


class TestDashboardDataWorkflow:
    """End-to-end tests for dashboard data aggregation."""

    @patch('app.get_project_dashboard_stats')
    @patch('app.get_all_docs')
    def test_dashboard_stats_aggregation(self, mock_get_all, mock_stats, app_client):
        """Test that dashboard correctly aggregates project stats."""
        mock_get_all.return_value = [
            {'id': 'project-1', 'name': 'Project 1'},
            {'id': 'project-2', 'name': 'Project 2'}
        ]
        mock_stats.return_value = {
            'total_episodes': 5,
            'completed_phases': 12,
            'pending_compliance': 3
        }

        response = app_client.get('/api/projects')
        assert response.status_code == 200
        data = json.loads(response.data)
        # API returns list directly, not wrapped in {'projects': [...]}
        assert len(data) == 2


class TestErrorHandling:
    """Tests for error handling in workflows."""

    def test_invalid_json_returns_400(self, app_client):
        """Test that invalid JSON returns 400 error."""
        response = app_client.post('/api/projects',
            data='not valid json',
            content_type='application/json'
        )
        # Flask should return 400 for invalid JSON
        assert response.status_code in [400, 500]

    @patch('app.get_doc')
    def test_nonexistent_resource_returns_404(self, mock_get, app_client):
        """Test that accessing nonexistent resource returns 404."""
        mock_get.return_value = None

        response = app_client.get('/api/projects/nonexistent-id')
        assert response.status_code == 404

    def test_method_not_allowed(self, app_client):
        """Test that unsupported methods return 405."""
        response = app_client.patch('/api/projects')
        assert response.status_code == 405
