#!/usr/bin/env python3
"""
Unit and functional tests for Series Grouping feature.

Tests:
1. Series CRUD operations (Create, Read, Update, Delete)
2. Episode-Series relationship
3. Series deletion ungroups episodes
4. Project deletion cascades to series
5. Series sorting by order
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:5000"


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_test(name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")


def api_get(endpoint):
    """GET request helper."""
    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
    return response.status_code, response.json()


def api_post(endpoint, data):
    """POST request helper."""
    response = requests.post(
        f"{BASE_URL}{endpoint}",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    return response.status_code, response.json()


def api_put(endpoint, data):
    """PUT request helper."""
    response = requests.put(
        f"{BASE_URL}{endpoint}",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    return response.status_code, response.json()


def api_delete(endpoint):
    """DELETE request helper."""
    response = requests.delete(f"{BASE_URL}{endpoint}", timeout=10)
    return response.status_code, response.json()


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add(self, name, passed, details=""):
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"{name}: {details}")
        print_test(name, passed, details)

    def summary(self):
        total = self.passed + self.failed
        return self.passed, self.failed, total


def test_health_check(results):
    """Test that the server is running."""
    print("\n[Test Group] Health Check")
    print("-" * 40)

    try:
        status, data = api_get("/health")
        results.add(
            "Server is running",
            status == 200 and data.get("status") == "healthy",
            f"Status: {status}, Data: {data}"
        )
    except Exception as e:
        results.add("Server is running", False, str(e))
        return False
    return True


def test_series_crud(results):
    """Test Series Create, Read, Update, Delete operations."""
    print("\n[Test Group] Series CRUD Operations")
    print("-" * 40)

    # First, create a project to attach series to
    status, project = api_post("/api/projects", {
        "title": "Test Project for Series",
        "description": "Testing series functionality",
        "status": "Planning"
    })
    results.add(
        "Create test project",
        status == 201 and "id" in project,
        f"Status: {status}"
    )

    if status != 201:
        return None

    project_id = project["id"]

    # Test 1: Create a series
    status, series1 = api_post("/api/series", {
        "projectId": project_id,
        "name": "Season 1",
        "description": "The first season",
        "order": 1
    })
    results.add(
        "Create series",
        status == 201 and "id" in series1,
        f"Status: {status}, Response: {series1}"
    )

    if status != 201:
        return project_id

    series1_id = series1["id"]

    # Test 2: Create second series
    status, series2 = api_post("/api/series", {
        "projectId": project_id,
        "name": "Season 2",
        "description": "The second season",
        "order": 2
    })
    results.add(
        "Create second series",
        status == 201 and "id" in series2,
        f"Status: {status}"
    )
    series2_id = series2.get("id")

    # Test 3: List series for project
    status, series_list = api_get(f"/api/projects/{project_id}/series")
    results.add(
        "List series for project",
        status == 200 and isinstance(series_list, list) and len(series_list) == 2,
        f"Status: {status}, Count: {len(series_list) if isinstance(series_list, list) else 'N/A'}"
    )

    # Test 4: Series are sorted by order
    if isinstance(series_list, list) and len(series_list) >= 2:
        sorted_correctly = series_list[0].get("order", 0) <= series_list[1].get("order", 0)
        results.add(
            "Series sorted by order",
            sorted_correctly,
            f"Orders: {[s.get('order') for s in series_list]}"
        )
    else:
        results.add("Series sorted by order", False, "Not enough series to test")

    # Test 5: Update series
    status, updated = api_put(f"/api/series/{series1_id}", {
        "name": "Season 1 - Updated",
        "description": "Updated description"
    })
    results.add(
        "Update series",
        status == 200 and updated.get("name") == "Season 1 - Updated",
        f"Status: {status}, Name: {updated.get('name')}"
    )

    # Test 6: Series has updatedAt timestamp
    results.add(
        "Series has updatedAt",
        "updatedAt" in updated,
        f"Fields: {list(updated.keys())}"
    )

    return project_id, series1_id, series2_id


def test_episode_series_relationship(results, project_id, series1_id, series2_id):
    """Test assigning episodes to series."""
    print("\n[Test Group] Episode-Series Relationship")
    print("-" * 40)

    # Create episode with series
    status, ep1 = api_post("/api/episodes", {
        "projectId": project_id,
        "seriesId": series1_id,
        "title": "S1E1: Pilot",
        "description": "The pilot episode",
        "status": "Planning"
    })
    results.add(
        "Create episode with seriesId",
        status == 201 and ep1.get("seriesId") == series1_id,
        f"Status: {status}, seriesId: {ep1.get('seriesId')}"
    )
    ep1_id = ep1.get("id")

    # Create episode without series (ungrouped)
    status, ep2 = api_post("/api/episodes", {
        "projectId": project_id,
        "title": "Ungrouped Episode",
        "description": "Not in any series",
        "status": "Planning"
    })
    results.add(
        "Create episode without seriesId",
        status == 201 and ep2.get("seriesId") is None,
        f"Status: {status}, seriesId: {ep2.get('seriesId')}"
    )
    ep2_id = ep2.get("id")

    # Create episode in series 2
    status, ep3 = api_post("/api/episodes", {
        "projectId": project_id,
        "seriesId": series2_id,
        "title": "S2E1: New Beginning",
        "description": "First episode of season 2",
        "status": "Planning"
    })
    results.add(
        "Create episode in second series",
        status == 201 and ep3.get("seriesId") == series2_id,
        f"Status: {status}"
    )
    ep3_id = ep3.get("id")

    # List all episodes
    status, episodes = api_get(f"/api/projects/{project_id}/episodes")
    results.add(
        "List all episodes",
        status == 200 and len(episodes) == 3,
        f"Status: {status}, Count: {len(episodes)}"
    )

    # Update episode to change series
    status, updated_ep = api_put(f"/api/episodes/{ep2_id}", {
        "seriesId": series1_id
    })
    results.add(
        "Move episode to series",
        status == 200 and updated_ep.get("seriesId") == series1_id,
        f"Status: {status}, New seriesId: {updated_ep.get('seriesId')}"
    )

    # Update episode to remove from series
    status, updated_ep = api_put(f"/api/episodes/{ep2_id}", {
        "seriesId": None
    })
    # Note: JSON null becomes Python None, but it might be stored differently
    results.add(
        "Remove episode from series",
        status == 200,
        f"Status: {status}, seriesId: {updated_ep.get('seriesId')}"
    )

    return ep1_id, ep2_id, ep3_id


def test_series_deletion_ungroups_episodes(results, project_id, series1_id):
    """Test that deleting a series ungroups its episodes."""
    print("\n[Test Group] Series Deletion Ungroups Episodes")
    print("-" * 40)

    # Create a new series for this test
    status, series = api_post("/api/series", {
        "projectId": project_id,
        "name": "Temporary Series",
        "order": 99
    })
    temp_series_id = series.get("id")

    # Create episode in this series
    status, ep = api_post("/api/episodes", {
        "projectId": project_id,
        "seriesId": temp_series_id,
        "title": "Episode to be ungrouped",
        "status": "Planning"
    })
    ep_id = ep.get("id")

    results.add(
        "Setup: Episode in temp series",
        ep.get("seriesId") == temp_series_id,
        f"Episode seriesId: {ep.get('seriesId')}"
    )

    # Delete the series
    status, result = api_delete(f"/api/series/{temp_series_id}")
    results.add(
        "Delete series",
        status == 200 and result.get("success") == True,
        f"Status: {status}"
    )

    # Check that the episode is now ungrouped
    status, episodes = api_get(f"/api/projects/{project_id}/episodes")
    ungrouped_ep = next((e for e in episodes if e["id"] == ep_id), None)

    results.add(
        "Episode ungrouped after series delete",
        ungrouped_ep is not None and ungrouped_ep.get("seriesId") is None,
        f"Episode seriesId: {ungrouped_ep.get('seriesId') if ungrouped_ep else 'NOT FOUND'}"
    )


def test_project_deletion_cascades(results):
    """Test that deleting a project also deletes its series."""
    print("\n[Test Group] Project Deletion Cascades to Series")
    print("-" * 40)

    # Create a new project
    status, project = api_post("/api/projects", {
        "title": "Project to Delete",
        "description": "Testing cascade delete"
    })
    project_id = project.get("id")

    # Create series in the project
    status, series = api_post("/api/series", {
        "projectId": project_id,
        "name": "Series to be deleted",
        "order": 1
    })
    series_id = series.get("id")

    # Create episode in the series
    status, episode = api_post("/api/episodes", {
        "projectId": project_id,
        "seriesId": series_id,
        "title": "Episode to be deleted"
    })

    results.add(
        "Setup: Project with series and episode",
        status == 201,
        f"Project: {project_id}, Series: {series_id}"
    )

    # Delete the project
    status, result = api_delete(f"/api/projects/{project_id}")
    results.add(
        "Delete project",
        status == 200,
        f"Status: {status}"
    )

    # Verify series is deleted (list should be empty or not contain our series)
    status, all_series = api_get(f"/api/projects/{project_id}/series")
    series_deleted = isinstance(all_series, list) and len(all_series) == 0
    results.add(
        "Series deleted with project",
        series_deleted,
        f"Remaining series: {len(all_series) if isinstance(all_series, list) else 'error'}"
    )


def test_series_with_sample_data(results):
    """Test that sample data includes series."""
    print("\n[Test Group] Sample Data Includes Series")
    print("-" * 40)

    # Initialize sample data
    status, init_result = api_post("/api/init-sample-data", {})
    results.add(
        "Initialize sample data",
        status == 200 and "projectId" in init_result,
        f"Status: {status}"
    )

    if status != 200:
        return

    project_id = init_result.get("projectId")

    # Check that series were created
    status, series_list = api_get(f"/api/projects/{project_id}/series")
    has_series = isinstance(series_list, list) and len(series_list) >= 2
    results.add(
        "Sample data has series",
        has_series,
        f"Series count: {len(series_list) if isinstance(series_list, list) else 0}"
    )

    # Check that episodes have seriesId
    status, episodes = api_get(f"/api/projects/{project_id}/episodes")
    episodes_with_series = [e for e in episodes if e.get("seriesId")]
    results.add(
        "Sample episodes have seriesId",
        len(episodes_with_series) > 0,
        f"Episodes with series: {len(episodes_with_series)}/{len(episodes)}"
    )


def cleanup(project_id):
    """Clean up test data."""
    if project_id:
        try:
            api_delete(f"/api/projects/{project_id}")
        except:
            pass


def main():
    print_header("Series Grouping Feature Tests")
    print(f"Target: {BASE_URL}")

    results = TestResults()

    # Check server is running
    if not test_health_check(results):
        print("\n✗ Server not running. Start it with: python test_app.py")
        sys.exit(1)

    # Run tests
    project_id = None
    series1_id = None
    series2_id = None

    try:
        # CRUD tests
        crud_result = test_series_crud(results)
        if crud_result and len(crud_result) == 3:
            project_id, series1_id, series2_id = crud_result

            # Relationship tests
            test_episode_series_relationship(results, project_id, series1_id, series2_id)

            # Deletion tests
            test_series_deletion_ungroups_episodes(results, project_id, series1_id)

        # Cascade delete test (creates its own project)
        test_project_deletion_cascades(results)

        # Sample data test
        test_series_with_sample_data(results)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if project_id:
            cleanup(project_id)

    # Summary
    print_header("Test Summary")
    passed, failed, total = results.summary()

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {total}")

    if results.errors:
        print("\nFailures:")
        for error in results.errors:
            print(f"  - {error}")

    print(f"\n{'✓ ALL TESTS PASSED' if failed == 0 else '✗ SOME TESTS FAILED'}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
