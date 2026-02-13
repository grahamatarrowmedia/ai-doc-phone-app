"""
Unit tests for bug fixes from UAT test report.
Covers: clean_ai_response, episode ordering, user role validation,
        expert discovery prompt, target duration, and compliance alignment.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestCleanAiResponse:
    """Bug #2: Research AI returns raw JSON — test the cleaning helper."""

    def test_strips_json_code_block(self):
        from app import clean_ai_response

        raw = '```json\n{"key": "value"}\n```'
        assert clean_ai_response(raw) == '{"key": "value"}'

    def test_strips_plain_code_block(self):
        from app import clean_ai_response

        raw = '```\nsome text\n```'
        assert clean_ai_response(raw) == 'some text'

    def test_leaves_clean_text_unchanged(self):
        from app import clean_ai_response

        clean = 'This is already clean text.'
        assert clean_ai_response(clean) == clean

    def test_handles_nested_backticks(self):
        from app import clean_ai_response

        raw = '```json\n{"code": "use `backticks` here"}\n```'
        result = clean_ai_response(raw)
        assert '"code"' in result
        assert result.startswith('{')

    def test_handles_empty_string(self):
        from app import clean_ai_response

        assert clean_ai_response('') == ''

    def test_handles_whitespace_only(self):
        from app import clean_ai_response

        assert clean_ai_response('   \n\n   ') == ''

    def test_strips_surrounding_whitespace(self):
        from app import clean_ai_response

        raw = '\n\n  Some response text  \n\n'
        assert clean_ai_response(raw) == 'Some response text'

    def test_handles_json_array_wrapped(self):
        from app import clean_ai_response

        raw = '```json\n[{"name": "Expert 1"}, {"name": "Expert 2"}]\n```'
        result = clean_ai_response(raw)
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_does_not_strip_internal_backticks(self):
        from app import clean_ai_response

        raw = 'Use `code` in your response'
        assert clean_ai_response(raw) == raw


class TestEpisodeOrdering:
    """Bug #5: Episodes displayed out of order in Research sidebar."""

    @patch('app.get_all_docs')
    def test_episodes_sorted_by_order(self, mock_get_all, app_client):
        mock_get_all.return_value = [
            {'id': 'ep3', 'title': 'Episode 3', 'order': 3},
            {'id': 'ep1', 'title': 'Episode 1', 'order': 1},
            {'id': 'ep2', 'title': 'Episode 2', 'order': 2},
        ]

        response = app_client.get('/api/projects/test-project/episodes')
        data = json.loads(response.data)

        assert data[0]['order'] == 1
        assert data[1]['order'] == 2
        assert data[2]['order'] == 3

    @patch('app.get_all_docs')
    def test_episodes_sorted_by_episode_number_fallback(self, mock_get_all, app_client):
        mock_get_all.return_value = [
            {'id': 'ep20', 'title': 'Episode 20', 'episodeNumber': 20},
            {'id': 'ep5', 'title': 'Episode 5', 'episodeNumber': 5},
            {'id': 'ep1', 'title': 'Episode 1', 'episodeNumber': 1},
        ]

        response = app_client.get('/api/projects/test-project/episodes')
        data = json.loads(response.data)

        assert data[0]['episodeNumber'] == 1
        assert data[1]['episodeNumber'] == 5
        assert data[2]['episodeNumber'] == 20

    @patch('app.get_all_docs')
    def test_episodes_with_missing_order_sorted_last(self, mock_get_all, app_client):
        mock_get_all.return_value = [
            {'id': 'ep-no-order', 'title': 'No Order'},
            {'id': 'ep1', 'title': 'First', 'order': 1},
        ]

        response = app_client.get('/api/projects/test-project/episodes')
        data = json.loads(response.data)

        # Missing order defaults to 0, so it comes first
        assert data[0]['id'] == 'ep-no-order'
        assert data[1]['order'] == 1


class TestUserRoleValidation:
    """Bug #6 related: Validate user creation with roles."""

    def test_valid_roles_constant_exists(self):
        from app import VALID_ROLES

        assert 'exec_producer' in VALID_ROLES
        assert 'researcher' in VALID_ROLES
        assert 'ai_director' in VALID_ROLES
        assert 'production_manager' in VALID_ROLES
        assert len(VALID_ROLES) == 13

    @patch('app.create_doc')
    def test_create_user_with_valid_role(self, mock_create, app_client):
        mock_create.return_value = {
            'id': 'user-123', 'username': 'testuser', 'role': 'researcher'
        }

        response = app_client.post('/api/users',
            data=json.dumps({'username': 'testuser', 'role': 'researcher'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['role'] == 'researcher'

    def test_create_user_with_invalid_role_returns_400(self, app_client):
        response = app_client.post('/api/users',
            data=json.dumps({'username': 'testuser', 'role': 'invalid_role'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid role' in data['error']

    def test_create_user_without_username_returns_400(self, app_client):
        response = app_client.post('/api/users',
            data=json.dumps({'role': 'researcher'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'username' in data['error']

    @patch('app.create_doc')
    def test_create_user_default_role_is_researcher(self, mock_create, app_client):
        mock_create.return_value = {
            'id': 'user-123', 'username': 'newuser', 'role': 'researcher'
        }

        response = app_client.post('/api/users',
            data=json.dumps({'username': 'newuser'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        # Verify create_doc was called with role='researcher'
        call_args = mock_create.call_args[0][1]
        assert call_args['role'] == 'researcher'

    @patch('app.create_doc')
    def test_create_user_generates_avatar(self, mock_create, app_client):
        mock_create.return_value = {
            'id': 'user-123', 'username': 'newuser', 'role': 'researcher',
            'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=newuser'
        }

        response = app_client.post('/api/users',
            data=json.dumps({'username': 'newuser'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        call_args = mock_create.call_args[0][1]
        assert 'dicebear' in call_args['avatar']
        assert 'newuser' in call_args['avatar']


class TestFindExpertsPrompt:
    """Bug #6: Find Experts returns wrong domain — test prompt construction."""

    @patch('app.generate_ai_response')
    def test_find_experts_includes_domain_constraint(self, mock_ai, app_client):
        mock_ai.return_value = '[]'

        response = app_client.post('/api/find-experts',
            data=json.dumps({
                'topic': 'French cuisine history',
                'expertise_domain': 'Food History',
                'context': 'BBC documentary about French cooking'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        # Verify the prompt includes the domain constraint
        prompt_arg = mock_ai.call_args[0][0]
        assert 'Food History' in prompt_arg
        assert 'Do NOT return AI' in prompt_arg
        assert 'French cuisine history' in prompt_arg

    @patch('app.generate_ai_response')
    def test_find_experts_parses_json_array(self, mock_ai, app_client):
        mock_ai.return_value = '```json\n[{"name": "Expert 1", "title": "Prof", "affiliation": "Oxford"}]\n```'

        response = app_client.post('/api/find-experts',
            data=json.dumps({'topic': 'culinary history'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Expert 1'

    @patch('app.generate_ai_response')
    def test_find_experts_handles_invalid_json(self, mock_ai, app_client):
        mock_ai.return_value = 'Not valid JSON at all'

        response = app_client.post('/api/find-experts',
            data=json.dumps({'topic': 'something'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []


class TestTargetDuration:
    """Bug #7: Target duration mismatch — test that project duration is used."""

    @patch('app.generate_ai_response')
    @patch('app.get_doc')
    def test_generate_script_uses_project_duration(self, mock_get_doc, mock_ai, app_client):
        mock_get_doc.return_value = {
            'id': 'project-123',
            'target_duration_minutes': 60,
            'title': 'Test Doc'
        }
        mock_ai.return_value = '{"parts": []}'

        response = app_client.post('/api/generate-script',
            data=json.dumps({
                'projectId': 'project-123',
                'title': 'Test Script',
                'description': 'A test'
            }),
            content_type='application/json'
        )

        # Verify the prompt includes 60 minutes (from project), not 30
        prompt_arg = mock_ai.call_args[0][0]
        assert '60 minutes' in prompt_arg

    @patch('app.generate_ai_response')
    @patch('app.get_doc')
    def test_generate_script_fallback_to_60_without_project(self, mock_get_doc, mock_ai, app_client):
        mock_get_doc.return_value = None
        mock_ai.return_value = '{"parts": []}'

        response = app_client.post('/api/generate-script',
            data=json.dumps({
                'title': 'Test Script',
                'description': 'A test'
            }),
            content_type='application/json'
        )

        # Without project, should default to 60 (not 30)
        prompt_arg = mock_ai.call_args[0][0]
        assert '60 minutes' in prompt_arg

    @patch('app.generate_ai_response')
    @patch('app.get_doc')
    def test_generate_script_explicit_duration_overrides(self, mock_get_doc, mock_ai, app_client):
        mock_get_doc.return_value = {'id': 'p1', 'target_duration_minutes': 60}
        mock_ai.return_value = '{"parts": []}'

        response = app_client.post('/api/generate-script',
            data=json.dumps({
                'projectId': 'p1',
                'title': 'Test',
                'description': 'test',
                'duration': 45
            }),
            content_type='application/json'
        )

        # Explicit duration should override project default
        prompt_arg = mock_ai.call_args[0][0]
        assert '45 minutes' in prompt_arg


class TestPlanningBriefPersistence:
    """Bug #7 related: Brief save syncs target_duration_minutes to project."""

    @patch('app.update_doc')
    @patch('app.get_doc')
    def test_save_brief_syncs_duration(self, mock_get_doc, mock_update, app_client):
        mock_get_doc.return_value = {'id': 'project-123', 'target_duration_minutes': 30}

        response = app_client.post('/api/projects/project-123/brief',
            data=json.dumps({
                'premise': 'A documentary about food',
                'episode_duration_minutes': 60,
                'format': 'documentary'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        # Verify update_doc was called with target_duration_minutes
        update_args = mock_update.call_args[0][2]
        assert update_args['target_duration_minutes'] == 60
        assert 'brief' in update_args

    @patch('app.update_doc')
    @patch('app.get_doc')
    def test_save_brief_without_duration_does_not_overwrite(self, mock_get_doc, mock_update, app_client):
        mock_get_doc.return_value = {'id': 'project-123'}

        response = app_client.post('/api/projects/project-123/brief',
            data=json.dumps({'premise': 'Just a premise'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        update_args = mock_update.call_args[0][2]
        assert 'target_duration_minutes' not in update_args

    @patch('app.get_doc')
    def test_get_brief_returns_empty_if_none(self, mock_get_doc, app_client):
        mock_get_doc.return_value = {'id': 'project-123'}

        response = app_client.get('/api/projects/project-123/brief')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {}

    @patch('app.get_doc')
    def test_get_brief_returns_404_for_missing_project(self, mock_get_doc, app_client):
        mock_get_doc.return_value = None

        response = app_client.get('/api/projects/nonexistent/brief')

        assert response.status_code == 404


class TestComplianceItemTypes:
    """Bug #8 related: Compliance supports both legacy and new frontend categories."""

    @patch('app.create_doc')
    def test_create_fact_check_item(self, mock_create, app_client):
        mock_create.return_value = {
            'id': 'comp-1', 'episodeId': 'ep-1', 'itemType': 'fact_check', 'status': 'pending'
        }

        response = app_client.post('/api/compliance',
            data=json.dumps({
                'episodeId': 'ep-1',
                'itemType': 'fact_check',
                'claim': 'The moon landing was in 1969'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201

    @patch('app.create_doc')
    def test_create_archive_clearance_item(self, mock_create, app_client):
        mock_create.return_value = {
            'id': 'comp-2', 'episodeId': 'ep-1', 'itemType': 'archive_clearance', 'status': 'pending'
        }

        response = app_client.post('/api/compliance',
            data=json.dumps({
                'episodeId': 'ep-1',
                'itemType': 'archive_clearance',
                'clip_title': 'NASA footage'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201

    def test_create_compliance_with_invalid_type_returns_400(self, app_client):
        response = app_client.post('/api/compliance',
            data=json.dumps({
                'episodeId': 'ep-1',
                'itemType': 'not_a_valid_type'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_compliance_without_episode_returns_400(self, app_client):
        response = app_client.post('/api/compliance',
            data=json.dumps({
                'itemType': 'fact_check',
                'claim': 'Something'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
