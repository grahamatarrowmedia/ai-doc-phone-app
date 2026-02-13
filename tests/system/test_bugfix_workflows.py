"""
System/Integration tests for bug-fix workflows.
Tests end-to-end flows that exercise multiple endpoints together.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, call


class TestResearchToScriptWorkflow:
    """End-to-end test: research → script generation uses correct duration."""

    @patch('app.generate_ai_response')
    @patch('app.get_doc')
    @patch('app.update_doc')
    @patch('app.get_all_docs')
    def test_full_research_to_script_flow(self, mock_get_all, mock_update,
                                           mock_get_doc, mock_ai, app_client):
        """Test that research produces clean output and script uses correct duration."""
        # Step 1: Research endpoint returns clean text
        mock_get_all.return_value = []
        mock_ai.return_value = '```json\n{"findings": "French cuisine evolved over centuries"}\n```'

        response = app_client.post('/api/ai/simple-research',
            data=json.dumps({
                'title': 'French Food History',
                'query': 'Origins of French cuisine',
                'save': False
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        research_data = json.loads(response.data)
        assert '```' not in research_data['result']

        # Step 2: Script generation uses project's 60-minute duration
        mock_get_doc.return_value = {
            'id': 'project-123',
            'target_duration_minutes': 60,
            'title': 'French Food'
        }
        mock_ai.return_value = json.dumps({
            'parts': [{'title': 'Part 1', 'scenes': []}]
        })

        response = app_client.post('/api/generate-script',
            data=json.dumps({
                'projectId': 'project-123',
                'title': 'French Food History',
                'description': 'Episode about origins',
                'researchContext': [research_data['result']]
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        prompt_used = mock_ai.call_args[0][0]
        assert '60 minutes' in prompt_used


class TestPlanningToReviewWorkflow:
    """End-to-end: brief save → duration synced → compliance uses correct values."""

    @patch('app.get_docs_by_episode')
    @patch('app.update_doc')
    @patch('app.get_doc')
    def test_brief_duration_flows_to_compliance(self, mock_get_doc, mock_update,
                                                  mock_get_docs, app_client):
        """Test that saving a brief with 60min syncs to the project."""
        # Step 1: Save brief with 60-minute episodes
        mock_get_doc.return_value = {'id': 'p1', 'target_duration_minutes': 30}

        response = app_client.post('/api/projects/p1/brief',
            data=json.dumps({
                'premise': 'French food documentary',
                'format': 'documentary',
                'episode_duration_minutes': 60,
                'episode_count': 20
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

        # Verify the project update includes the synced duration
        update_call_args = mock_update.call_args[0][2]
        assert update_call_args['target_duration_minutes'] == 60


class TestUserCreationAndExpertDiscovery:
    """End-to-end: create user → expert search uses domain context."""

    @patch('app.generate_ai_response')
    @patch('app.create_doc')
    def test_new_role_user_triggers_domain_search(self, mock_create, mock_ai, app_client):
        """Test that a production_manager can be created and expert search works."""
        # Step 1: Create a production_manager user
        mock_create.return_value = {
            'id': 'user-pm', 'username': 'sarah', 'role': 'production_manager'
        }

        response = app_client.post('/api/users',
            data=json.dumps({
                'username': 'sarah',
                'role': 'production_manager',
                'bio': 'Senior production manager'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

        # Step 2: Search for experts in the correct domain
        mock_ai.return_value = json.dumps([
            {
                'name': 'Dr. Priscilla Parkhurst Ferguson',
                'title': 'Professor of Sociology',
                'affiliation': 'Columbia University',
                'expertise_area': 'French culinary culture',
                'relevance': 'Author of Accounting for Taste: The Triumph of French Cuisine',
                'relevance_score': 0.95
            }
        ])

        response = app_client.post('/api/find-experts',
            data=json.dumps({
                'topic': 'History of French haute cuisine',
                'expertise_domain': 'French Culinary History',
                'context': 'BBC Two documentary series'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        experts = json.loads(response.data)
        assert len(experts) >= 1
        # Verify AI prompt included domain context
        prompt = mock_ai.call_args[0][0]
        assert 'French Culinary History' in prompt
        assert 'Do NOT return AI' in prompt


class TestEpisodeOrderingAcrossPhases:
    """End-to-end: episodes stay ordered across different API calls."""

    @patch('app.get_all_docs')
    def test_episodes_ordered_consistently(self, mock_get_all, app_client):
        """Test episodes are sorted regardless of Firestore return order."""
        unsorted_episodes = [
            {'id': 'ep10', 'title': 'EP10', 'order': 10, 'projectId': 'p1'},
            {'id': 'ep1', 'title': 'EP01', 'order': 1, 'projectId': 'p1'},
            {'id': 'ep5', 'title': 'EP05', 'order': 5, 'projectId': 'p1'},
            {'id': 'ep20', 'title': 'EP20', 'order': 20, 'projectId': 'p1'},
            {'id': 'ep3', 'title': 'EP03', 'order': 3, 'projectId': 'p1'},
        ]
        mock_get_all.return_value = unsorted_episodes

        response = app_client.get('/api/projects/p1/episodes')
        data = json.loads(response.data)

        titles = [ep['title'] for ep in data]
        assert titles == ['EP01', 'EP03', 'EP05', 'EP10', 'EP20']


class TestComplianceWorkflowWithNewTypes:
    """End-to-end: create compliance items of all types → export includes all."""

    @patch('app.get_doc')
    @patch('app.get_docs_by_episode')
    @patch('app.create_doc')
    def test_full_compliance_workflow(self, mock_create, mock_get_docs, mock_get_doc, app_client):
        """Create items of each type, then export and verify grouping."""
        items = []
        all_types = [
            'archive_clearance', 'fact_check', 'contributor_release', 'compliance_signoff',
            'source_citation', 'archive_license', 'exif_metadata', 'legal_signoff'
        ]

        # Step 1: Create one of each type
        for i, item_type in enumerate(all_types):
            new_item = {'id': f'comp-{i}', 'episodeId': 'ep-1', 'itemType': item_type, 'status': 'pending'}
            mock_create.return_value = new_item
            items.append(new_item)

            response = app_client.post('/api/compliance',
                data=json.dumps({'episodeId': 'ep-1', 'itemType': item_type}),
                content_type='application/json'
            )
            assert response.status_code == 201

        # Step 2: Export and verify all types are grouped
        mock_get_docs.return_value = items
        mock_get_doc.return_value = {'id': 'ep-1', 'title': 'Test Episode'}

        response = app_client.get('/api/episodes/ep-1/compliance/export')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['summary']['totalItems'] == 8
        assert len(data['factChecks']) == 1
        assert len(data['archiveClearances']) == 1
        assert len(data['contributorReleases']) == 1
        assert len(data['complianceSignoffs']) == 1
        assert len(data['sourceCitations']) == 1
        assert len(data['archiveLicenses']) == 1
        assert len(data['exifMetadata']) == 1
        assert len(data['legalSignoffs']) == 1


class TestEmailBriefsEndpoint:
    """System test for the email-briefs endpoint."""

    @patch('app.requests.post')
    @patch('app.create_doc')
    def test_email_briefs_sends_via_sendgrid(self, mock_create, mock_post, app_client):
        """Test that email briefs are sent via SendGrid HTTP API."""
        import os
        os.environ['SENDGRID_API_KEY'] = 'SG.test-key'
        os.environ['EMAIL_SENDER'] = 'test@example.com'

        mock_create.return_value = {'id': 'brief-123'}
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response

        response = app_client.post('/api/email-briefs',
            data=json.dumps({
                'project_title': 'French Food Documentary',
                'recipients': ['producer@example.com'],
                'briefs': [
                    {
                        'title': 'French Cuisine Origins',
                        'description': 'Key findings about French food',
                        'prompts': [
                            {'prompt': 'Wide shot of Paris bakery', 'target': 'image', 'aspect_ratio': '16:9'}
                        ]
                    }
                ]
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True or data.get('sent') is True

        # Clean up
        os.environ.pop('SENDGRID_API_KEY', None)
        os.environ.pop('EMAIL_SENDER', None)
