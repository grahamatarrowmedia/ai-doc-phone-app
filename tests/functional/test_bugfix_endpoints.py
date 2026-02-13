"""
Functional tests for bug-fix endpoints.
Tests the HTTP API contract for endpoints modified during UAT bug-fix cycle.
"""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestSimpleResearchCleaning:
    """Bug #2: /api/ai/simple-research should return clean text, not raw JSON wrappers."""

    @patch('app.db')
    @patch('app.generate_ai_response')
    @patch('app.get_all_docs')
    def test_simple_research_strips_json_wrapper(self, mock_get_all, mock_ai, mock_db, app_client):
        mock_get_all.return_value = []  # no research docs
        mock_ai.return_value = '```json\n{"response": "Clean research about food history"}\n```'

        response = app_client.post('/api/ai/simple-research',
            data=json.dumps({
                'title': 'French Food History',
                'query': 'Tell me about French cuisine',
                'projectId': 'test-project',
                'episodeId': 'test-episode',
                'save': False
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Result should NOT start with ```json
        assert not data['result'].startswith('```')
        assert '```' not in data['result']

    @patch('app.db')
    @patch('app.generate_ai_response')
    @patch('app.get_all_docs')
    def test_simple_research_preserves_clean_response(self, mock_get_all, mock_ai, mock_db, app_client):
        mock_get_all.return_value = []
        clean_text = 'This is clean research about French cuisine.'
        mock_ai.return_value = clean_text

        response = app_client.post('/api/ai/simple-research',
            data=json.dumps({
                'title': 'Test',
                'query': 'Tell me',
                'save': False
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == clean_text


class TestResearchAgentCleaning:
    """Bug #2: /api/ai/research-agent should return clean text."""

    @patch('app.create_doc')
    @patch('app.update_agent_task')
    @patch('app.create_agent_task')
    @patch('app.generate_ai_response')
    def test_research_agent_strips_wrapper(self, mock_ai, mock_create_task,
                                            mock_update_task, mock_create_doc, app_client):
        mock_ai.return_value = '```\nResearch package content\n```'
        mock_create_task.return_value = {'id': 'task-123'}
        mock_create_doc.return_value = {'id': 'doc-123'}

        response = app_client.post('/api/ai/research-agent',
            data=json.dumps({
                'episodeId': 'ep-1',
                'brief': {'summary': 'French cuisine', 'storyBeats': [], 'targetInterviewees': [], 'archiveRequirements': []}
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert not data['researchPackage'].startswith('```')


class TestEpisodesEndpointOrdering:
    """Bug #5: GET /api/projects/{id}/episodes must return sorted episodes."""

    @patch('app.get_all_docs')
    def test_returns_episodes_in_order(self, mock_get_all, app_client):
        mock_get_all.return_value = [
            {'id': 'ep17', 'title': 'EP17', 'order': 17},
            {'id': 'ep5', 'title': 'EP05', 'order': 5},
            {'id': 'ep1', 'title': 'EP01', 'order': 1},
            {'id': 'ep20', 'title': 'EP20', 'order': 20},
            {'id': 'ep6', 'title': 'EP06', 'order': 6},
        ]

        response = app_client.get('/api/projects/test-project/episodes')
        data = json.loads(response.data)

        orders = [ep['order'] for ep in data]
        assert orders == sorted(orders)


class TestFindExpertsEndpoint:
    """Bug #6: /api/find-experts must use domain context."""

    @patch('app.generate_ai_response')
    def test_includes_expertise_domain_in_prompt(self, mock_ai, app_client):
        mock_ai.return_value = '[]'

        app_client.post('/api/find-experts',
            data=json.dumps({
                'topic': 'History of French patisserie',
                'expertise_domain': 'Culinary History',
            }),
            content_type='application/json'
        )

        prompt = mock_ai.call_args[0][0]
        assert 'Culinary History' in prompt
        assert 'Do NOT return AI' in prompt

    @patch('app.generate_ai_response')
    def test_returns_empty_array_on_bad_ai_response(self, mock_ai, app_client):
        mock_ai.return_value = 'I cannot find experts on this topic.'

        response = app_client.post('/api/find-experts',
            data=json.dumps({'topic': 'obscure topic'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert json.loads(response.data) == []

    @patch('app.generate_ai_response')
    def test_works_without_optional_fields(self, mock_ai, app_client):
        mock_ai.return_value = '[{"name": "Dr Test", "title": "Prof", "affiliation": "Uni"}]'

        response = app_client.post('/api/find-experts',
            data=json.dumps({'topic': 'food history'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1


class TestUserCreationEndpoint:
    """Tests for POST /api/users with role validation."""

    @patch('app.create_doc')
    def test_creates_user_with_new_roles(self, mock_create, app_client):
        """Test that the 3 new roles are accepted."""
        new_roles = ['production_manager', 'line_producer', 'ai_director']
        for role in new_roles:
            mock_create.return_value = {'id': f'user-{role}', 'username': f'test_{role}', 'role': role}

            response = app_client.post('/api/users',
                data=json.dumps({'username': f'test_{role}', 'role': role}),
                content_type='application/json'
            )

            assert response.status_code == 201, f'Failed for role: {role}'


class TestPlanningBriefEndpoints:
    """Tests for brief/bible persistence endpoints."""

    @patch('app.update_doc')
    @patch('app.get_doc')
    def test_save_and_get_brief(self, mock_get_doc, mock_update, app_client):
        brief_data = {'premise': 'A test doc', 'format': 'documentary', 'episode_duration_minutes': 60}
        mock_get_doc.return_value = {'id': 'p1', 'brief': brief_data}

        # Save
        response = app_client.post('/api/projects/p1/brief',
            data=json.dumps(brief_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert json.loads(response.data)['success'] is True

        # Get
        response = app_client.get('/api/projects/p1/brief')
        assert response.status_code == 200

    @patch('app.update_doc')
    @patch('app.get_doc')
    def test_save_and_get_bible(self, mock_get_doc, mock_update, app_client):
        bible_data = {'themes': ['food', 'culture'], 'concept': 'French cuisine'}
        mock_get_doc.return_value = {'id': 'p1', 'bible': bible_data}

        response = app_client.post('/api/projects/p1/bible',
            data=json.dumps(bible_data),
            content_type='application/json'
        )
        assert response.status_code == 200

        response = app_client.get('/api/projects/p1/bible')
        assert response.status_code == 200


class TestComplianceEndpoints:
    """Bug #8: Compliance supports all item types including fact_check."""

    @patch('app.create_doc')
    def test_all_compliance_types_accepted(self, mock_create, app_client):
        valid_types = [
            'source_citation', 'archive_license', 'exif_metadata', 'legal_signoff',
            'archive_clearance', 'fact_check', 'contributor_release', 'compliance_signoff',
        ]

        for item_type in valid_types:
            mock_create.return_value = {'id': f'comp-{item_type}', 'episodeId': 'ep-1', 'itemType': item_type}

            response = app_client.post('/api/compliance',
                data=json.dumps({'episodeId': 'ep-1', 'itemType': item_type}),
                content_type='application/json'
            )

            assert response.status_code == 201, f'Failed for type: {item_type}'

    @patch('app.get_docs_by_episode')
    @patch('app.get_doc')
    def test_compliance_export_includes_fact_checks(self, mock_get_doc, mock_get_docs, app_client):
        mock_get_doc.return_value = {'id': 'ep-1', 'title': 'Test Episode'}
        mock_get_docs.return_value = [
            {'id': 'c1', 'itemType': 'fact_check', 'status': 'pending', 'claim': 'Test claim'},
            {'id': 'c2', 'itemType': 'archive_clearance', 'status': 'cleared'},
        ]

        response = app_client.get('/api/episodes/ep-1/compliance/export')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['factChecks']) == 1
        assert len(data['archiveClearances']) == 1
        assert data['summary']['totalItems'] == 2
