"""
Unit tests for helper functions in app.py
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestDocToDict:
    """Tests for doc_to_dict function."""

    def test_converts_firestore_doc_to_dict(self):
        """Test that Firestore document is converted to dict with id."""
        from app import doc_to_dict

        mock_doc = MagicMock()
        mock_doc.id = 'test-id-123'
        mock_doc.to_dict.return_value = {'name': 'Test', 'value': 42}

        result = doc_to_dict(mock_doc)

        assert result['id'] == 'test-id-123'
        assert result['name'] == 'Test'
        assert result['value'] == 42

    def test_handles_empty_doc(self):
        """Test handling of document with empty data."""
        from app import doc_to_dict

        mock_doc = MagicMock()
        mock_doc.id = 'empty-doc'
        mock_doc.to_dict.return_value = {}

        result = doc_to_dict(mock_doc)

        assert result['id'] == 'empty-doc'
        assert len(result) == 1


class TestExtractUrls:
    """Tests for extract_urls function."""

    def test_extracts_http_urls(self):
        """Test extraction of HTTP URLs from text."""
        from app import extract_urls

        text = "Check out http://example.com and https://test.org for more info."
        urls = extract_urls(text)

        assert 'http://example.com' in urls
        assert 'https://test.org' in urls

    def test_handles_no_urls(self):
        """Test handling text with no URLs."""
        from app import extract_urls

        text = "This text has no URLs at all."
        urls = extract_urls(text)

        assert urls == []

    def test_handles_multiple_urls(self):
        """Test extraction of multiple URLs."""
        from app import extract_urls

        text = """
        Sources:
        - https://example.com/article1
        - https://example.com/article2
        - http://other-site.org/page
        """
        urls = extract_urls(text)

        assert len(urls) >= 3

    def test_removes_duplicates(self):
        """Test that duplicate URLs are removed."""
        from app import extract_urls

        text = "Visit https://example.com here and https://example.com there."
        urls = extract_urls(text)

        # Should have unique URLs
        assert len(urls) == len(set(urls))


class TestValidateUrl:
    """Tests for validate_url function."""

    @patch('app.requests.head')
    def test_valid_url_returns_true(self, mock_head):
        """Test that valid URL returns True."""
        from app import validate_url

        mock_head.return_value.status_code = 200

        result = validate_url('https://example.com', timeout=1)

        assert result is True

    @patch('app.requests.head')
    def test_invalid_url_returns_false(self, mock_head):
        """Test that invalid URL returns False."""
        from app import validate_url

        mock_head.side_effect = Exception("Connection error")

        result = validate_url('https://invalid-url-xyz.com', timeout=1)

        assert result is False

    @patch('app.requests.head')
    def test_404_returns_false(self, mock_head):
        """Test that 404 response returns False."""
        from app import validate_url

        mock_head.return_value.status_code = 404

        result = validate_url('https://example.com/notfound', timeout=1)

        assert result is False


class TestWorkflowPhases:
    """Tests for workflow phase constants and logic."""

    def test_workflow_phases_defined(self):
        """Test that all workflow phases are defined."""
        from app import EPISODE_PHASES

        expected_phases = ['research', 'archive', 'script', 'voiceover', 'assembly']

        for phase in expected_phases:
            assert phase in EPISODE_PHASES

    def test_phase_order(self):
        """Test that phases have correct order values."""
        from app import EPISODE_PHASES

        # Check that each phase has an order value
        for phase_name, phase_info in EPISODE_PHASES.items():
            assert 'order' in phase_info
            assert isinstance(phase_info['order'], int)


class TestCollectionNames:
    """Tests for collection name generation."""

    def test_collection_prefix_in_test_env(self):
        """Test that collection prefix is applied in test environment."""
        # This tests the COLLECTION_PREFIX logic
        import os
        os.environ['APP_ENV'] = 'dev'

        # Re-import to get updated prefix
        import importlib
        import app
        importlib.reload(app)

        assert app.COLLECTION_PREFIX == 'dev_'

        # Reset
        os.environ['APP_ENV'] = 'test'
        importlib.reload(app)
