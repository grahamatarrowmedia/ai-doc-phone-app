"""
Full workflow test: Video blueprint -> Project creation -> Episode research

Tests the complete flow of:
1. Uploading a video file as a blueprint
2. Creating a project from the analyzed blueprint
3. Generating verified research for the first episode
"""
import requests
import json
import time
import sys

BASE_URL = "https://doc-production-app-280939464794.us-central1.run.app"
VIDEO_FILE = "/Data/Clients/ArrowMedia/WhatsApp Video 2026-02-02 at 15.31.34.mp4"


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")
    print("-" * 40)


def test_full_workflow():
    results = {
        "blueprint_analysis": False,
        "project_creation": False,
        "episode_research": False,
        "errors": []
    }

    # ========================================
    # Step 1: Upload video and analyze blueprint
    # ========================================
    print_step(1, "Uploading video and analyzing blueprint")

    try:
        with open(VIDEO_FILE, 'rb') as f:
            files = {'file': ('blueprint_video.mp4', f, 'video/mp4')}
            data = {'numEpisodes': '4'}

            print(f"Uploading: {VIDEO_FILE}")
            print("This may take a few minutes for video analysis...")

            response = requests.post(
                f"{BASE_URL}/api/ai/analyze-blueprint",
                files=files,
                data=data,
                timeout=300  # 5 minute timeout for video
            )

        if response.status_code != 200:
            raise Exception(f"Blueprint analysis failed: {response.status_code} - {response.text[:200]}")

        blueprint_data = response.json()

        if 'error' in blueprint_data:
            raise Exception(f"Blueprint error: {blueprint_data['error']}")

        blueprint = blueprint_data.get('blueprint', {})

        print(f"✓ Title: {blueprint.get('title', 'N/A')}")
        print(f"✓ Style: {blueprint.get('style', 'N/A')}")
        print(f"✓ Description: {blueprint.get('description', 'N/A')[:100]}...")
        print(f"✓ Episodes suggested: {len(blueprint.get('episodes', []))}")

        # Check blueprint file
        bf = blueprint.get('blueprintFile', {})
        if bf:
            print(f"✓ Blueprint PDF: {bf.get('filename', 'N/A')}")
            print(f"✓ Blueprint size: {bf.get('size', 0) / 1024:.1f} KB")
            if bf.get('sourceFile'):
                print(f"✓ Source file: {bf.get('sourceFile')}")

        results["blueprint_analysis"] = True

    except Exception as e:
        results["errors"].append(f"Blueprint analysis: {str(e)}")
        print(f"✗ Error: {e}")
        return results

    # ========================================
    # Step 2: Create project from blueprint
    # ========================================
    print_step(2, "Creating project from blueprint")

    try:
        project_data = {
            'title': blueprint.get('title', 'Test Project'),
            'description': blueprint.get('description', ''),
            'style': blueprint.get('style', ''),
            'status': 'Planning',
            'blueprintFile': blueprint.get('blueprintFile')
        }

        response = requests.post(
            f"{BASE_URL}/api/projects",
            json=project_data,
            timeout=30
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Project creation failed: {response.status_code}")

        project = response.json()
        project_id = project.get('id')

        print(f"✓ Project created: {project_id}")
        print(f"✓ Title: {project.get('title')}")

        results["project_creation"] = True

    except Exception as e:
        results["errors"].append(f"Project creation: {str(e)}")
        print(f"✗ Error: {e}")
        return results

    # ========================================
    # Step 3: Create first episode
    # ========================================
    print_step(3, "Creating first episode")

    try:
        episodes = blueprint.get('episodes', [])
        if not episodes:
            raise Exception("No episodes in blueprint")

        first_episode = episodes[0]

        episode_data = {
            'projectId': project_id,
            'title': first_episode.get('title', 'Episode 1'),
            'description': first_episode.get('description', ''),
            'order': first_episode.get('order', 1),
            'status': 'Planning'
        }

        response = requests.post(
            f"{BASE_URL}/api/episodes",
            json=episode_data,
            timeout=30
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Episode creation failed: {response.status_code}")

        episode = response.json()
        episode_id = episode.get('id')

        print(f"✓ Episode created: {episode_id}")
        print(f"✓ Title: {episode.get('title')}")

    except Exception as e:
        results["errors"].append(f"Episode creation: {str(e)}")
        print(f"✗ Error: {e}")
        return results

    # ========================================
    # Step 4: Generate research for first episode
    # ========================================
    print_step(4, "Generating verified research for first episode")

    try:
        research_request = {
            'episodeId': episode_id,
            'episodeTitle': episode.get('title'),
            'episodeDescription': episode.get('description'),
            'projectId': project_id,
            'projectTitle': project.get('title'),
            'projectDescription': project.get('description'),
            'projectStyle': project.get('style', '')
        }

        print("Generating deep verified research...")
        print("This may take a minute...")

        response = requests.post(
            f"{BASE_URL}/api/ai/episode-research",
            json=research_request,
            timeout=180
        )

        if response.status_code != 200:
            raise Exception(f"Research generation failed: {response.status_code}")

        research_data = response.json()

        if 'error' in research_data:
            raise Exception(f"Research error: {research_data['error']}")

        result = research_data.get('result', '')
        sources = research_data.get('sources', [])

        print(f"✓ Research generated: {len(result)} characters")
        print(f"✓ Research saved: {research_data.get('saved', False)}")
        print(f"✓ Sources downloading: {len(sources)}")

        # Check for verification markers
        verified_count = result.count('✅ VERIFIED') + result.count('✅')
        print(f"✓ Verified facts: {verified_count}")

        # Check for URLs
        import re
        urls = re.findall(r'https?://[^\s\)\]\"<>]+', result)
        print(f"✓ Source URLs: {len(urls)}")

        # Check for issues
        issues = []
        if 'undefined' in result.lower():
            issues.append(f"'undefined' found {result.lower().count('undefined')} times")
        if '[url]' in result.lower():
            issues.append("'[URL]' placeholder found")

        if issues:
            print(f"⚠ Issues: {', '.join(issues)}")
        else:
            print("✓ No URL issues detected")

        # Show research preview
        print("\nResearch Preview:")
        print("-" * 40)
        print(result[:800])
        print("...")

        results["episode_research"] = True

    except Exception as e:
        results["errors"].append(f"Episode research: {str(e)}")
        print(f"✗ Error: {e}")
        return results

    # ========================================
    # Cleanup (optional - delete test project)
    # ========================================
    print_step(5, "Cleanup")

    try:
        response = requests.delete(
            f"{BASE_URL}/api/projects/{project_id}",
            timeout=30
        )
        if response.status_code == 200:
            print(f"✓ Test project deleted: {project_id}")
        else:
            print(f"⚠ Could not delete test project: {response.status_code}")
    except Exception as e:
        print(f"⚠ Cleanup error: {e}")

    return results


if __name__ == "__main__":
    print_header("Full Workflow Test: Video Blueprint -> Project -> Research")

    start_time = time.time()
    results = test_full_workflow()
    elapsed = time.time() - start_time

    print_header("Test Results")

    all_passed = all([
        results["blueprint_analysis"],
        results["project_creation"],
        results["episode_research"]
    ])

    print(f"Blueprint Analysis: {'✓ PASS' if results['blueprint_analysis'] else '✗ FAIL'}")
    print(f"Project Creation:   {'✓ PASS' if results['project_creation'] else '✗ FAIL'}")
    print(f"Episode Research:   {'✓ PASS' if results['episode_research'] else '✗ FAIL'}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print(f"\nTotal time: {elapsed:.1f} seconds")
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

    sys.exit(0 if all_passed else 1)
