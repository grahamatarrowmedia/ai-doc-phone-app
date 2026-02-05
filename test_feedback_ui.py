#!/usr/bin/env python3
"""
Test script for feedback UI and API functionality.
Tests the full flow: submit feedback -> retrieve -> verify display
"""

import requests
import json
import time
import re

BASE_URL = "https://doc-production-app-feedback-d3uk63glya-uc.a.run.app"


def test_homepage_loads():
    """Test that the homepage loads correctly."""
    print("=" * 60)
    print("TEST 1: Homepage Loads")
    print("=" * 60)

    response = requests.get(BASE_URL, timeout=30)

    print(f"  Status code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Check for key elements
    checks = [
        ("Title", "Documentary Production App" in response.text),
        ("Feedback banner", "FEEDBACK BUILD" in response.text),
        ("Version badge", "version-badge" in response.text),
        ("Feedback modal", "feedback-modal" in response.text),
        ("showFeedbackPage function", "showFeedbackPage" in response.text),
    ]

    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

    all_passed = all(c[1] for c in checks)
    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_feedback_api_get():
    """Test retrieving feedback."""
    print("\n" + "=" * 60)
    print("TEST 2: Feedback API - GET")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/feedback", timeout=30)

    print(f"  Status code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"  Response type: {type(data).__name__}")
    print(f"  Feedback count: {len(data)}")

    if data:
        # Check structure of first feedback
        first = data[0]
        required_fields = ['id', 'type', 'text', 'status', 'createdAt']
        missing = [f for f in required_fields if f not in first]

        if missing:
            print(f"  ✗ Missing fields: {missing}")
            return False
        else:
            print(f"  ✓ All required fields present")
            print(f"  Sample: {first.get('type')} - {first.get('text', '')[:40]}...")

    print(f"\n  Result: PASSED")
    return True


def test_feedback_api_post():
    """Test submitting feedback."""
    print("\n" + "=" * 60)
    print("TEST 3: Feedback API - POST")
    print("=" * 60)

    test_feedback = {
        "type": "improvement",
        "text": f"Automated test feedback - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "name": "Test Script",
        "version": "test-1.0.0",
        "userAgent": "Python Test Script",
        "url": BASE_URL
    }

    response = requests.post(
        f"{BASE_URL}/api/feedback",
        json=test_feedback,
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        # Handle both 'id' and 'feedbackId' response formats
        feedback_id = data.get('id') or data.get('feedbackId')
        print(f"  ✓ Feedback created with ID: {feedback_id}")
        print(f"  ✓ Success: {data.get('success', True)}")
        print(f"\n  Result: PASSED")
        return feedback_id
    else:
        print(f"  ✗ Failed to create feedback")
        print(f"  Response: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return None


def test_feedback_api_update(feedback_id):
    """Test updating feedback status."""
    print("\n" + "=" * 60)
    print("TEST 4: Feedback API - PUT (Update)")
    print("=" * 60)

    if not feedback_id:
        print("  Skipped - no feedback ID from previous test")
        return False

    update_data = {
        "status": "in-progress",
        "response": "Thank you for your feedback, we're looking into it."
    }

    response = requests.put(
        f"{BASE_URL}/api/feedback/{feedback_id}",
        json=update_data,
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        print(f"  ✓ Feedback updated successfully")

        # Verify the update
        verify = requests.get(f"{BASE_URL}/api/feedback", timeout=30).json()
        updated = next((f for f in verify if f.get('id') == feedback_id), None)

        if updated:
            print(f"  ✓ Verified status: {updated.get('status')}")
            print(f"  ✓ Verified response: {updated.get('response', '')[:50]}...")

        print(f"\n  Result: PASSED")
        return True
    else:
        print(f"  ✗ Failed to update feedback")
        print(f"\n  Result: FAILED")
        return False


def test_feedback_modal_html():
    """Test that feedback modal HTML is correctly structured."""
    print("\n" + "=" * 60)
    print("TEST 5: Feedback Modal HTML Structure")
    print("=" * 60)

    response = requests.get(BASE_URL, timeout=30)
    html = response.text

    checks = [
        ("Feedback modal exists", 'id="feedback-modal"' in html),
        ("Feedback type select", 'id="feedback-type"' in html),
        ("Feedback text area", 'id="feedback-text"' in html),
        ("Feedback name input", 'id="feedback-name"' in html),
        ("Submit button", 'submitFeedback()' in html),
        ("Feedback list container", 'id="feedback-list"' in html),
        ("Close button", 'closeFeedbackModal()' in html),
        ("Bug option", 'value="bug"' in html),
        ("Feature option", 'value="feature"' in html),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_version_badge_clickable():
    """Test that version badge has click handler."""
    print("\n" + "=" * 60)
    print("TEST 6: Version Badge Clickable")
    print("=" * 60)

    response = requests.get(BASE_URL, timeout=30)
    html = response.text

    # Check for clickable version badge
    has_onclick = 'onclick="showFeedbackPage()"' in html
    has_clickable_class = 'version-badge clickable' in html or 'version-badge" onclick' in html

    print(f"  {'✓' if has_onclick else '✗'} onclick handler present")
    print(f"  {'✓' if has_clickable_class else '✗'} clickable styling")

    passed = has_onclick
    print(f"\n  Result: {'PASSED' if passed else 'FAILED'}")
    return passed


def test_javascript_functions():
    """Test that all required JavaScript functions exist."""
    print("\n" + "=" * 60)
    print("TEST 7: JavaScript Functions")
    print("=" * 60)

    response = requests.get(BASE_URL, timeout=30)
    html = response.text

    required_functions = [
        "showFeedbackPage",
        "closeFeedbackModal",
        "submitFeedback",
        "loadFeedbackHistory",
    ]

    all_passed = True
    for func in required_functions:
        # Check for function definition
        pattern = rf'(async\s+)?function\s+{func}\s*\('
        found = bool(re.search(pattern, html))
        status = "✓" if found else "✗"
        print(f"  {status} {func}()")
        if not found:
            all_passed = False

    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_css_styles():
    """Test that feedback CSS styles are loaded."""
    print("\n" + "=" * 60)
    print("TEST 8: CSS Styles")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/static/css/style.css", timeout=30)

    print(f"  Status code: {response.status_code}")

    if response.status_code != 200:
        print(f"  ✗ CSS file not found")
        return False

    css = response.text

    required_styles = [
        ".version-badge.clickable",
        ".feedback-container",
        ".feedback-item",
        ".feedback-item-header",
        ".feedback-item-text",
        ".feedback-response",
    ]

    all_passed = True
    for style in required_styles:
        found = style in css
        status = "✓" if found else "✗"
        print(f"  {status} {style}")
        if not found:
            all_passed = False

    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FEEDBACK UI TEST SUITE")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print("=" * 60)

    results = []

    try:
        results.append(("Homepage Loads", test_homepage_loads()))
        results.append(("Feedback API GET", test_feedback_api_get()))

        feedback_id = test_feedback_api_post()
        results.append(("Feedback API POST", feedback_id is not None))

        results.append(("Feedback API PUT", test_feedback_api_update(feedback_id)))
        results.append(("Modal HTML Structure", test_feedback_modal_html()))
        results.append(("Version Badge Clickable", test_version_badge_clickable()))
        results.append(("JavaScript Functions", test_javascript_functions()))
        results.append(("CSS Styles", test_css_styles()))

    except Exception as e:
        print(f"\n\nTEST ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

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
