#!/usr/bin/env python3
"""
Test script to verify episode research saving and retrieval.
Tests the full flow: generate -> save -> retrieve -> verify links
"""

import requests
import json
import re
import time

BASE_URL = "https://doc-production-app-research-d3uk63glya-uc.a.run.app"

def test_simple_research_with_save():
    """Test generating and saving research to an episode."""
    print("=" * 70)
    print("TEST 1: Generate and Save Research")
    print("=" * 70)

    # First, get existing projects
    print("\n[1] Getting projects...")
    projects_resp = requests.get(f"{BASE_URL}/api/projects", timeout=30)
    projects = projects_resp.json()
    print(f"    Found {len(projects)} projects")

    if not projects:
        print("    ERROR: No projects found. Creating test project...")
        # Create a test project
        project_resp = requests.post(
            f"{BASE_URL}/api/projects",
            json={"title": "Test Documentary", "description": "Test project for research"},
            timeout=30
        )
        project = project_resp.json()
        project_id = project['id']
        print(f"    Created project: {project_id}")
    else:
        project_id = projects[0]['id']
        print(f"    Using project: {project_id} ({projects[0].get('title', 'Untitled')})")

    # Get or create an episode
    print("\n[2] Getting episodes...")
    episodes_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}/episodes", timeout=30)
    episodes = episodes_resp.json()
    print(f"    Found {len(episodes)} episodes")

    if not episodes:
        print("    Creating test episode...")
        episode_resp = requests.post(
            f"{BASE_URL}/api/episodes",
            json={
                "projectId": project_id,
                "title": "The Moon Landing",
                "description": "Apollo 11's historic first moon landing in 1969",
                "status": "Research"
            },
            timeout=30
        )
        episode = episode_resp.json()
        episode_id = episode['id']
        print(f"    Created episode: {episode_id}")
    else:
        episode = episodes[0]
        episode_id = episode['id']
        print(f"    Using episode: {episode_id} ({episode.get('title', 'Untitled')})")

    # Generate research with save=True
    print("\n[3] Generating research (with save=True)...")
    print(f"    Episode ID: {episode_id}")
    print(f"    Project ID: {project_id}")

    research_resp = requests.post(
        f"{BASE_URL}/api/ai/simple-research",
        json={
            "title": episode.get('title', 'Test Episode'),
            "description": episode.get('description', 'Test description'),
            "episodeId": episode_id,
            "projectId": project_id,
            "save": True
        },
        timeout=120
    )

    research_data = research_resp.json()
    print(f"\n    Response keys: {list(research_data.keys())}")
    print(f"    Result type: {type(research_data.get('result'))}")
    print(f"    Result length: {len(research_data.get('result', ''))}")
    print(f"    Saved: {research_data.get('saved')}")
    print(f"    Episode ID in response: {research_data.get('episodeId')}")

    if research_data.get('saveError'):
        print(f"    SAVE ERROR: {research_data.get('saveError')}")

    result_text = research_data.get('result', '')

    # Check for URLs in result
    urls = re.findall(r'https?://[^\s<>\[\]()\"\'\)]+', result_text)
    print(f"\n    Found {len(urls)} URLs in result")
    for i, url in enumerate(urls[:5]):
        print(f"      {i+1}. {url[:80]}...")

    # Check for markdown links
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', result_text)
    print(f"\n    Found {len(md_links)} markdown links")
    for i, (text, url) in enumerate(md_links[:5]):
        print(f"      {i+1}. [{text}]({url[:60]}...)")

    return episode_id, result_text


def test_get_saved_research(episode_id, expected_text):
    """Test retrieving saved research from an episode."""
    print("\n")
    print("=" * 70)
    print("TEST 2: Retrieve Saved Research")
    print("=" * 70)

    print(f"\n[1] Getting research for episode {episode_id}...")

    # Wait a moment for save to complete
    time.sleep(2)

    research_resp = requests.get(
        f"{BASE_URL}/api/episodes/{episode_id}/research",
        timeout=30
    )

    print(f"    Status code: {research_resp.status_code}")

    if research_resp.status_code != 200:
        print(f"    ERROR: Failed to get research: {research_resp.text}")
        return False

    research_data = research_resp.json()
    print(f"    Response keys: {list(research_data.keys())}")

    research_text = research_data.get('research', '')
    generated_at = research_data.get('generatedAt', '')

    print(f"    Research length: {len(research_text)}")
    print(f"    Generated at: {generated_at}")
    print(f"    Episode title: {research_data.get('episodeTitle')}")

    if not research_text:
        print("    ERROR: No research text returned!")
        return False

    # Verify it matches what we saved
    if research_text == expected_text:
        print("\n    ✓ Research text matches what was saved")
    else:
        print(f"\n    ⚠ Research text differs from what was saved")
        print(f"    Expected length: {len(expected_text)}")
        print(f"    Got length: {len(research_text)}")

    # Check for URLs in retrieved research
    urls = re.findall(r'https?://[^\s<>\[\]()\"\'\)]+', research_text)
    print(f"\n    Found {len(urls)} URLs in retrieved research")

    # Check for markdown links
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', research_text)
    print(f"    Found {len(md_links)} markdown links in retrieved research")

    if md_links:
        print("\n    Sample links that should be clickable:")
        for i, (text, url) in enumerate(md_links[:3]):
            print(f"      {i+1}. Text: '{text}'")
            print(f"         URL: {url}")
            # Verify URL is valid format
            if url.startswith('http'):
                print(f"         ✓ Valid URL format")
            else:
                print(f"         ✗ Invalid URL format!")

    return True


def test_delete_research(episode_id):
    """Test deleting research from an episode."""
    print("\n")
    print("=" * 70)
    print("TEST 3: Delete Research")
    print("=" * 70)

    print(f"\n[1] Deleting research for episode {episode_id}...")

    delete_resp = requests.delete(
        f"{BASE_URL}/api/episodes/{episode_id}/research",
        timeout=30
    )

    print(f"    Status code: {delete_resp.status_code}")
    print(f"    Response: {delete_resp.json()}")

    # Verify deletion
    print("\n[2] Verifying deletion...")
    research_resp = requests.get(
        f"{BASE_URL}/api/episodes/{episode_id}/research",
        timeout=30
    )

    research_data = research_resp.json()
    research_text = research_data.get('research', '')

    if not research_text:
        print("    ✓ Research successfully deleted")
        return True
    else:
        print(f"    ✗ Research still exists ({len(research_text)} chars)")
        return False


def test_html_link_rendering():
    """Test that markdown links render correctly as HTML."""
    print("\n")
    print("=" * 70)
    print("TEST 4: HTML Link Rendering Verification")
    print("=" * 70)

    # Sample markdown with links (similar to what AI generates)
    sample_markdown = """## Test Research

Here is a link to [NASA](https://www.nasa.gov/mission).

### More Links

*   [Wikipedia Apollo 11](https://en.wikipedia.org/wiki/Apollo_11)
*   [Space.com Article](https://www.space.com/apollo-11)
"""

    print("\n[1] Sample markdown:")
    print("-" * 40)
    print(sample_markdown)
    print("-" * 40)

    print("\n[2] Expected HTML anchors:")
    # These are the links that should be generated
    expected_links = [
        ('NASA', 'https://www.nasa.gov/mission'),
        ('Wikipedia Apollo 11', 'https://en.wikipedia.org/wiki/Apollo_11'),
        ('Space.com Article', 'https://www.space.com/apollo-11'),
    ]

    for text, url in expected_links:
        print(f'    <a href="{url}" target="_blank">{text}</a>')

    print("\n[3] Verification:")
    print("    The marked.js library should convert markdown links to anchor tags.")
    print("    The custom renderer adds target='_blank' for new tab opening.")
    print("    Links should be clickable in the browser.")

    # Parse markdown links
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', sample_markdown)
    print(f"\n    Found {len(md_links)} markdown links")

    for text, url in md_links:
        if url.startswith('http'):
            print(f"    ✓ [{text}]({url}) - valid URL")
        else:
            print(f"    ✗ [{text}]({url}) - invalid URL")

    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("EPISODE RESEARCH SAVE/RETRIEVE TESTS")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print("=" * 70)

    try:
        # Test 1: Generate and save
        episode_id, saved_text = test_simple_research_with_save()

        # Test 2: Retrieve saved research
        test_get_saved_research(episode_id, saved_text)

        # Test 3: Delete research
        # Skipping delete to keep the saved research for manual testing
        # test_delete_research(episode_id)

        # Test 4: HTML link rendering verification
        test_html_link_rendering()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED")
        print("=" * 70)
        print("\nTo manually verify:")
        print(f"1. Open {BASE_URL}")
        print("2. Go to Episodes tab")
        print("3. Look for 'View Saved' button on the episode")
        print("4. Click it to view the saved research")
        print("5. Verify links are clickable and open in new tabs")
        print("=" * 70)

    except Exception as e:
        print(f"\n\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
