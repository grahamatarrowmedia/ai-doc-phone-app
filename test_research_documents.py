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

import requests
import os
import hashlib
import time
import tempfile

BASE_URL = os.environ.get("TEST_BASE_URL", "https://doc-production-app-dev-d3uk63glya-uc.a.run.app")


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")
    print("-" * 40)


def get_or_create_project():
    """Get existing project or create a test project."""
    print_step("0", "Get or Create Project")

    try:
        response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        if response.status_code == 200:
            projects = response.json()
            if projects:
                project_id = projects[0]['id']
                print(f"  Using existing project: {project_id}")
                return projects[0]
    except:
        pass

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
        print(f"  Failed to create project: {response.status_code}")
        return None


def get_or_create_episode(project_id):
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
    except:
        pass

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
        print(f"  Failed to create episode: {response.status_code}")
        return None


def get_or_create_series(project_id):
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
    except:
        pass

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
        print(f"  Failed to create series: {response.status_code}")
        return None


def create_test_file(content="Test research document content", ext=".txt"):
    """Create a temporary test file."""
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def test_upload_research_to_episode(project_id, episode_id):
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

        if response.status_code == 201:
            result = response.json()
            asset = result.get('asset', {})
            asset_id = asset.get('id')

            checks = [
                ("Asset created", asset_id is not None),
                ("Has isResearchDocument flag", asset.get('isResearchDocument') == True),
                ("Has episodeId", asset.get('episodeId') == episode_id),
                ("Has projectId", asset.get('projectId') == project_id),
                ("Has file", asset.get('hasFile') == True),
            ]

            all_passed = True
            for name, passed in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {name}")
                if not passed:
                    all_passed = False

            print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
            return asset_id if all_passed else None
        else:
            print(f"  ✗ Upload failed: {response.text[:200]}")
            print(f"\n  Result: FAILED")
            return None

    finally:
        os.unlink(test_file_path)


def test_upload_research_to_series(project_id, series_id):
    """Test uploading a research document to a series."""
    print_step(2, "Test Upload Research Document to Series")

    test_content = f"""# Series Research Document

## Series Overview Research

This is a test research document for series {series_id}.

Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    test_file_path = create_test_file(test_content, ".txt")

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_series_research.txt', f, 'text/plain')}
            data = {
                'projectId': project_id,
                'seriesId': series_id,
                'isResearchDocument': 'true',
                'title': 'Test Series Research Document',
                'type': 'Document',
                'status': 'Acquired'
            }

            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=60
            )

        print(f"  Status code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            asset = result.get('asset', {})
            asset_id = asset.get('id')

            checks = [
                ("Asset created", asset_id is not None),
                ("Has isResearchDocument flag", asset.get('isResearchDocument') == True),
                ("Has seriesId", asset.get('seriesId') == series_id),
            ]

            all_passed = True
            for name, passed in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {name}")
                if not passed:
                    all_passed = False

            print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
            return asset_id if all_passed else None
        else:
            print(f"  ✗ Upload failed: {response.text[:200]}")
            print(f"\n  Result: FAILED")
            return None

    finally:
        os.unlink(test_file_path)


def test_upload_research_to_project(project_id):
    """Test uploading a research document to a project (no episode/series)."""
    print_step(3, "Test Upload Research Document to Project")

    test_content = f"""# Project-Level Research Document

## General Project Research

This is a project-level research document for project {project_id}.

Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    test_file_path = create_test_file(test_content, ".txt")

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_project_research.txt', f, 'text/plain')}
            data = {
                'projectId': project_id,
                'isResearchDocument': 'true',
                'title': 'Test Project Research Document',
                'type': 'Document',
                'status': 'Acquired'
            }

            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=60
            )

        print(f"  Status code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            asset = result.get('asset', {})
            asset_id = asset.get('id')

            checks = [
                ("Asset created", asset_id is not None),
                ("Has isResearchDocument flag", asset.get('isResearchDocument') == True),
                ("No episodeId", not asset.get('episodeId')),
                ("No seriesId", not asset.get('seriesId')),
            ]

            all_passed = True
            for name, passed in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {name}")
                if not passed:
                    all_passed = False

            print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
            return asset_id if all_passed else None
        else:
            print(f"  ✗ Upload failed: {response.text[:200]}")
            print(f"\n  Result: FAILED")
            return None

    finally:
        os.unlink(test_file_path)


def test_query_episode_research_documents(episode_id, expected_count=1):
    """Test querying research documents for an episode."""
    print_step(4, "Test Query Episode Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/episodes/{episode_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        docs = response.json()

        checks = [
            ("Returns list", isinstance(docs, list)),
            ("Has expected documents", len(docs) >= expected_count),
            ("All are research docs", all(d.get('isResearchDocument') for d in docs)),
            ("All have episodeId", all(d.get('episodeId') == episode_id for d in docs)),
        ]

        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False

        print(f"  Found {len(docs)} research document(s)")
        print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    else:
        print(f"  ✗ Query failed: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False


def test_query_series_research_documents(series_id, expected_count=1):
    """Test querying research documents for a series."""
    print_step(5, "Test Query Series Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/series/{series_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        docs = response.json()

        checks = [
            ("Returns list", isinstance(docs, list)),
            ("Has expected documents", len(docs) >= expected_count),
            ("All are research docs", all(d.get('isResearchDocument') for d in docs)),
            ("All have seriesId", all(d.get('seriesId') == series_id for d in docs)),
        ]

        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False

        print(f"  Found {len(docs)} research document(s)")
        print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    else:
        print(f"  ✗ Query failed: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False


def test_query_project_research_documents(project_id, expected_count=1):
    """Test querying project-level research documents."""
    print_step(6, "Test Query Project Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        docs = response.json()

        checks = [
            ("Returns list", isinstance(docs, list)),
            ("Has expected documents", len(docs) >= expected_count),
            ("All are research docs", all(d.get('isResearchDocument') for d in docs)),
            ("None have episodeId", all(not d.get('episodeId') for d in docs)),
            ("None have seriesId", all(not d.get('seriesId') for d in docs)),
        ]

        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False

        print(f"  Found {len(docs)} project-level research document(s)")
        print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    else:
        print(f"  ✗ Query failed: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False


def test_query_all_research_documents(project_id, expected_count=3):
    """Test querying all research documents for a project."""
    print_step(7, "Test Query All Project Research Documents")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/all-research-documents",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        docs = response.json()

        checks = [
            ("Returns list", isinstance(docs, list)),
            ("Has all documents", len(docs) >= expected_count),
            ("All are research docs", all(d.get('isResearchDocument') for d in docs)),
        ]

        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False

        print(f"  Found {len(docs)} total research document(s)")
        print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    else:
        print(f"  ✗ Query failed: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False


def test_ai_generate_topics():
    """Test the AI generate-topics endpoint for episode ideas."""
    print_step(8, "Test AI Generate Topics (Episode Ideas)")

    request_data = {
        "title": "The History of Space Exploration",
        "description": "A documentary series exploring the history of human space exploration from early rockets to the modern era.",
        "style": "Educational documentary",
        "numTopics": 5
    }

    print(f"  Project: {request_data['title']}")
    print(f"  Requesting {request_data['numTopics']} episode ideas...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-topics",
            json=request_data,
            timeout=60
        )

        print(f"  Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            topics = result.get('topics', [])

            checks = [
                ("Returns topics array", isinstance(topics, list)),
                ("Has topics", len(topics) > 0),
            ]

            # Check if topics have required fields
            if topics:
                first_topic = topics[0]
                checks.append(("Topics have title", 'title' in first_topic))
                checks.append(("Topics have description", 'description' in first_topic))
                checks.append(("Topics have order", 'order' in first_topic))

            all_passed = True
            for name, passed in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {name}")
                if not passed:
                    all_passed = False

            if topics:
                print(f"\n  Generated {len(topics)} episode ideas:")
                for i, topic in enumerate(topics[:3]):  # Show first 3
                    print(f"    {i+1}. {topic.get('title', 'Untitled')}")
                if len(topics) > 3:
                    print(f"    ... and {len(topics) - 3} more")

            print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
            return all_passed
        else:
            print(f"  ✗ Request failed: {response.text[:200]}")
            print(f"\n  Result: FAILED")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        print(f"\n  Result: FAILED")
        return False


def test_research_documents_in_assets(project_id):
    """Test that research documents appear in the assets list."""
    print_step(9, "Test Research Documents Appear in Assets")

    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/assets",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        assets = response.json()

        # Filter to research documents
        research_assets = [a for a in assets if a.get('isResearchDocument')]

        checks = [
            ("Assets returned", isinstance(assets, list)),
            ("Research docs found in assets", len(research_assets) > 0),
        ]

        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False

        print(f"  Total assets: {len(assets)}")
        print(f"  Research documents: {len(research_assets)}")

        print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    else:
        print(f"  ✗ Query failed: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False


def cleanup_test_assets(asset_ids):
    """Clean up test assets."""
    print_step("Cleanup", "Deleting Test Assets")

    deleted = 0
    for asset_id in asset_ids:
        if asset_id:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/assets/{asset_id}",
                    timeout=30
                )
                if response.status_code == 200:
                    deleted += 1
            except:
                pass

    print(f"  Deleted {deleted}/{len(asset_ids)} test assets")


def run_all_tests():
    """Run all tests."""
    print_header("RESEARCH DOCUMENTS & AI EPISODE IDEAS TEST SUITE")
    print(f"Testing: {BASE_URL}")

    results = []
    asset_ids = []

    try:
        # Setup
        project = get_or_create_project()
        if not project:
            print("FATAL: Could not get/create project")
            return False

        project_id = project['id']

        episode = get_or_create_episode(project_id)
        if not episode:
            print("FATAL: Could not get/create episode")
            return False

        episode_id = episode['id']

        series = get_or_create_series(project_id)
        if not series:
            print("FATAL: Could not get/create series")
            return False

        series_id = series['id']

        # Test uploads
        asset_id = test_upload_research_to_episode(project_id, episode_id)
        results.append(("Upload to Episode", asset_id is not None))
        if asset_id:
            asset_ids.append(asset_id)

        asset_id = test_upload_research_to_series(project_id, series_id)
        results.append(("Upload to Series", asset_id is not None))
        if asset_id:
            asset_ids.append(asset_id)

        asset_id = test_upload_research_to_project(project_id)
        results.append(("Upload to Project", asset_id is not None))
        if asset_id:
            asset_ids.append(asset_id)

        # Test queries
        results.append(("Query Episode Research Docs", test_query_episode_research_documents(episode_id)))
        results.append(("Query Series Research Docs", test_query_series_research_documents(series_id)))
        results.append(("Query Project Research Docs", test_query_project_research_documents(project_id)))
        results.append(("Query All Research Docs", test_query_all_research_documents(project_id)))

        # Test AI endpoint
        results.append(("AI Generate Topics", test_ai_generate_topics()))

        # Test assets integration
        results.append(("Research Docs in Assets", test_research_documents_in_assets(project_id)))

    except Exception as e:
        print(f"\n\nTEST ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if asset_ids:
            cleanup_test_assets(asset_ids)

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
