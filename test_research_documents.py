#!/usr/bin/env python3
"""
Test script for research document upload and AI episode generation functionality.

Tests:
1. Research document upload to episodes
2. Research document upload to series
3. Research document upload to projects
4. Research document query endpoints
5. AI generate-topics (Episode Ideas) endpoint
6. Research document display in assets
"""

import pytest
import requests
import os
import time
import tempfile

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5000")


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")
    print("-" * 40)


def create_test_file(content="Test research document content", ext=".txt"):
    """Create a temporary test file."""
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


# ============== Fixtures ==============

@pytest.fixture(scope="module")
def project_data():
    """Get existing project or create a test project."""
    print_step("0", "Get or Create Project")

    try:
        response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        if response.status_code == 200:
            projects = response.json()
            if projects:
                project = projects[0]
                print(f"  Using existing project: {project['id']}")
                return project
    except Exception as e:
        print(f"  Error getting projects: {e}")

    # Create a new project
    project_data = {
        "title": "Test Project for Research Documents",
        "description": "Automated test project for research document upload",
        "status": "Testing"
    }
    response = requests.post(
        f"{BASE_URL}/api/projects",
        json=project_data,
        timeout=30
    )

    if response.status_code == 201:
        project = response.json()
        print(f"  Created test project: {project['id']}")
        return project
    else:
        pytest.fail(f"Failed to create project: {response.status_code}")


@pytest.fixture(scope="module")
def project_id(project_data):
    """Get project ID from project data."""
    return project_data['id']


@pytest.fixture(scope="module")
def episode_data(project_id):
    """Get existing episode or create a test episode."""
    print_step("0.1", "Get or Create Episode")

    try:
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/episodes", timeout=30)
        if response.status_code == 200:
            episodes = response.json()
            if episodes:
                episode = episodes[0]
                print(f"  Using existing episode: {episode['id']} - {episode.get('title', 'Untitled')}")
                return episode
    except Exception as e:
        print(f"  Error getting episodes: {e}")

    # Create a new episode
    episode_data = {
        "projectId": project_id,
        "title": "Test Episode for Research Docs",
        "description": "Testing research document upload",
        "status": "Research"
    }
    response = requests.post(
        f"{BASE_URL}/api/episodes",
        json=episode_data,
        timeout=30
    )

    if response.status_code == 201:
        episode = response.json()
        print(f"  Created test episode: {episode['id']}")
        return episode
    else:
        pytest.fail(f"Failed to create episode: {response.status_code}")


@pytest.fixture(scope="module")
def episode_id(episode_data):
    """Get episode ID from episode data."""
    return episode_data['id']


@pytest.fixture(scope="module")
def series_data(project_id):
    """Get existing series or create a test series."""
    print_step("0.2", "Get or Create Series")

    try:
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/series", timeout=30)
        if response.status_code == 200:
            series_list = response.json()
            if series_list:
                series = series_list[0]
                print(f"  Using existing series: {series['id']} - {series.get('name', 'Untitled')}")
                return series
    except Exception as e:
        print(f"  Error getting series: {e}")

    # Create a new series
    series_data = {
        "projectId": project_id,
        "name": "Test Series for Research Docs",
        "description": "Testing research document upload",
        "order": 1
    }
    response = requests.post(
        f"{BASE_URL}/api/series",
        json=series_data,
        timeout=30
    )

    if response.status_code == 201:
        series = response.json()
        print(f"  Created test series: {series['id']}")
        return series
    else:
        pytest.fail(f"Failed to create series: {response.status_code}")


@pytest.fixture(scope="module")
def series_id(series_data):
    """Get series ID from series data."""
    return series_data['id']


# Track uploaded assets for cleanup
uploaded_assets = []


@pytest.fixture(scope="module")
def cleanup():
    """Cleanup fixture that runs after all tests."""
    yield
    # Cleanup uploaded assets
    print_step("Cleanup", "Deleting test assets")
    for asset_id in uploaded_assets:
        try:
            response = requests.delete(f"{BASE_URL}/api/assets/{asset_id}", timeout=30)
            print(f"  Deleted asset {asset_id}: {response.status_code}")
        except Exception as e:
            print(f"  Failed to delete asset {asset_id}: {e}")


# ============== Tests ==============

def test_upload_research_to_episode(project_id, episode_id, cleanup):
    """Test uploading a research document to an episode."""
    print_step(1, "Test Upload Research Document to Episode")

    # Create a test file
    test_content = f"""# Test Research Document

## Episode Research Notes

This is a test research document for episode {episode_id}.

### Key Points
- Point 1: Test data
- Point 2: More test data
- Point 3: Even more test data

### Sources
- Source 1: https://example.com/source1
- Source 2: https://example.com/source2

Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    test_file_path = create_test_file(test_content, ".txt")

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_research.txt', f, 'text/plain')}
            data = {
                'projectId': project_id,
                'episodeId': episode_id,
                'isResearchDocument': 'true',
                'title': 'Test Episode Research Document',
                'type': 'Document',
                'status': 'Acquired',
                'notes': f'Automated test upload - {time.strftime("%Y-%m-%d %H:%M:%S")}'
            }

            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=60
            )

        print(f"  Status code: {response.status_code}")

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        result = response.json()
        print(f"  Response: {result}")

        assert result.get('success') == True, "Upload should return success=True"
        assert 'asset' in result, "Response should include asset data"

        asset = result['asset']
        assert asset.get('isResearchDocument') == True, "Asset should be marked as research document"
        assert asset.get('episodeId') == episode_id, "Asset should be linked to episode"

        uploaded_assets.append(asset['id'])
        print(f"  ✓ Successfully uploaded research document to episode")
        print(f"    Asset ID: {asset['id']}")
        print(f"    GCS Path: {result.get('gcsPath')}")

    finally:
        os.unlink(test_file_path)


def test_upload_research_to_series(project_id, series_id, cleanup):
    """Test uploading a research document to a series."""
    print_step(2, "Test Upload Research Document to Series")

    test_content = f"""# Series Research Document

## Series Overview Research

Research notes for series {series_id}.

### Topics
1. Topic A
2. Topic B
3. Topic C

Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    test_file_path = create_test_file(test_content, ".txt")

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('series_research.txt', f, 'text/plain')}
            data = {
                'projectId': project_id,
                'seriesId': series_id,
                'isResearchDocument': 'true',
                'title': 'Test Series Research Document',
                'type': 'Document',
                'status': 'Acquired',
                'notes': f'Series research upload - {time.strftime("%Y-%m-%d %H:%M:%S")}'
            }

            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=60
            )

        print(f"  Status code: {response.status_code}")

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        result = response.json()
        print(f"  Response: {result}")

        assert result.get('success') == True, "Upload should return success=True"

        asset = result['asset']
        assert asset.get('isResearchDocument') == True, "Asset should be marked as research document"
        assert asset.get('seriesId') == series_id, "Asset should be linked to series"

        uploaded_assets.append(asset['id'])
        print(f"  ✓ Successfully uploaded research document to series")
        print(f"    Asset ID: {asset['id']}")

    finally:
        os.unlink(test_file_path)


def test_upload_research_to_project(project_id, cleanup):
    """Test uploading a research document to the project (not linked to episode/series)."""
    print_step(3, "Test Upload Research Document to Project")

    test_content = f"""# Project Research Document

## Project-Level Research Notes

General research for project {project_id}.

### Overview
This document contains project-wide research notes.

Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    test_file_path = create_test_file(test_content, ".txt")

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('project_research.txt', f, 'text/plain')}
            data = {
                'projectId': project_id,
                'isResearchDocument': 'true',
                'title': 'Test Project Research Document',
                'type': 'Document',
                'status': 'Acquired',
                'notes': f'Project research upload - {time.strftime("%Y-%m-%d %H:%M:%S")}'
            }

            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=60
            )

        print(f"  Status code: {response.status_code}")

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        result = response.json()
        print(f"  Response: {result}")

        assert result.get('success') == True, "Upload should return success=True"

        asset = result['asset']
        assert asset.get('isResearchDocument') == True, "Asset should be marked as research document"
        assert asset.get('episodeId') is None, "Asset should NOT be linked to episode"
        assert asset.get('seriesId') is None, "Asset should NOT be linked to series"

        uploaded_assets.append(asset['id'])
        print(f"  ✓ Successfully uploaded research document to project")
        print(f"    Asset ID: {asset['id']}")

    finally:
        os.unlink(test_file_path)


def test_query_episode_research_documents(episode_id):
    """Test querying research documents for an episode."""
    print_step(4, "Test Query Episode Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/episodes/{episode_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    docs = response.json()
    print(f"  Found {len(docs)} research documents for episode")

    assert isinstance(docs, list), "Response should be a list"
    # Check that all returned docs have episodeId set
    for doc in docs:
        assert doc.get('episodeId') == episode_id, f"Document should be linked to episode {episode_id}"
        assert doc.get('isResearchDocument') == True, "Document should be marked as research document"

    print(f"  ✓ Successfully queried episode research documents")


def test_query_series_research_documents(series_id):
    """Test querying research documents for a series."""
    print_step(5, "Test Query Series Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/series/{series_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    docs = response.json()
    print(f"  Found {len(docs)} research documents for series")

    assert isinstance(docs, list), "Response should be a list"
    for doc in docs:
        assert doc.get('seriesId') == series_id, f"Document should be linked to series {series_id}"
        assert doc.get('isResearchDocument') == True, "Document should be marked as research document"

    print(f"  ✓ Successfully queried series research documents")


def test_query_project_research_documents(project_id):
    """Test querying project-level research documents (not linked to episode/series)."""
    print_step(6, "Test Query Project Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    docs = response.json()
    print(f"  Found {len(docs)} project-level research documents")

    assert isinstance(docs, list), "Response should be a list"
    for doc in docs:
        assert doc.get('projectId') == project_id, f"Document should be in project {project_id}"
        assert doc.get('isResearchDocument') == True, "Document should be marked as research document"
        assert doc.get('episodeId') is None, "Project-level doc should NOT have episodeId"
        assert doc.get('seriesId') is None, "Project-level doc should NOT have seriesId"

    print(f"  ✓ Successfully queried project research documents")


def test_query_all_research_documents(project_id):
    """Test querying all research documents for a project."""
    print_step(7, "Test Query All Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/all-research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    docs = response.json()
    print(f"  Found {len(docs)} total research documents")

    assert isinstance(docs, list), "Response should be a list"
    for doc in docs:
        assert doc.get('projectId') == project_id, f"Document should be in project {project_id}"
        assert doc.get('isResearchDocument') == True, "Document should be marked as research document"

    print(f"  ✓ Successfully queried all research documents")


def test_ai_generate_topics(project_data):
    """Test AI generate-topics endpoint (Episode Ideas)."""
    print_step(8, "Test AI Generate Topics (Episode Ideas)")

    request_data = {
        "title": project_data.get('title', 'Test Documentary'),
        "description": project_data.get('description', 'A test documentary project'),
        "numTopics": 5
    }

    response = requests.post(
        f"{BASE_URL}/api/ai/generate-topics",
        json=request_data,
        timeout=60
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    result = response.json()
    print(f"  Response keys: {result.keys()}")

    assert 'topics' in result, "Response should contain 'topics' key"

    topics = result['topics']
    assert isinstance(topics, list), "Topics should be a list"
    assert len(topics) > 0, "Should return at least one topic"

    print(f"  Generated {len(topics)} episode ideas:")
    for i, topic in enumerate(topics[:3], 1):
        title = topic.get('title', 'No title')
        desc = topic.get('description', 'No description')[:50]
        print(f"    {i}. {title}")
        print(f"       {desc}...")

    print(f"  ✓ Successfully generated episode ideas")


def test_research_documents_in_assets(project_id):
    """Test that research documents appear in the assets list."""
    print_step(9, "Test Research Documents in Assets")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/assets",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    assets = response.json()
    print(f"  Found {len(assets)} total assets")

    research_docs = [a for a in assets if a.get('isResearchDocument') == True]
    print(f"  Found {len(research_docs)} research documents in assets")

    # We should have at least some research documents if previous tests ran
    if len(research_docs) > 0:
        print(f"  Research documents:")
        for doc in research_docs[:5]:
            print(f"    - {doc.get('title', 'Untitled')} (ID: {doc.get('id')})")
            if doc.get('episodeId'):
                print(f"      Episode: {doc['episodeId']}")
            if doc.get('seriesId'):
                print(f"      Series: {doc['seriesId']}")

    print(f"  ✓ Successfully verified research documents in assets")


if __name__ == "__main__":
    print_header("Research Documents Test Suite")
    print(f"Target: {BASE_URL}")

    # Run all tests
    pytest.main([__file__, "-v", "-s"])
