#!/usr/bin/env python3
"""
Test script to analyze the research API response format.
This will help debug why links aren't rendering correctly.
"""

import requests
import json
import re

# Test against local or deployed endpoint
BASE_URL = "https://doc-production-app-research-d3uk63glya-uc.a.run.app"
# BASE_URL = "http://localhost:5000"

def test_simple_research():
    """Test the simple-research endpoint and analyze the response."""

    print("=" * 60)
    print("TESTING /api/ai/simple-research ENDPOINT")
    print("=" * 60)

    payload = {
        "title": "The Apollo 11 Moon Landing",
        "description": "The first crewed mission to land on the Moon in 1969"
    }

    print(f"\nRequest payload: {json.dumps(payload, indent=2)}")
    print(f"\nCalling: {BASE_URL}/api/ai/simple-research")
    print("-" * 60)

    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/simple-research",
            json=payload,
            timeout=120
        )

        print(f"\nStatus code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")

        # Get raw response text
        raw_text = response.text
        print(f"\nRaw response length: {len(raw_text)} characters")
        print(f"\nFirst 500 chars of raw response:")
        print("-" * 40)
        print(raw_text[:500])
        print("-" * 40)

        # Parse JSON
        data = response.json()

        print(f"\n\nJSON STRUCTURE ANALYSIS:")
        print("=" * 60)
        print(f"Type of response: {type(data)}")
        print(f"Keys in response: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

        if isinstance(data, dict):
            for key, value in data.items():
                print(f"\n  Key: '{key}'")
                print(f"    Type: {type(value)}")
                if isinstance(value, str):
                    print(f"    Length: {len(value)} chars")
                    print(f"    First 200 chars: {value[:200]}...")
                elif isinstance(value, dict):
                    print(f"    Sub-keys: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"    List length: {len(value)}")
                    if value:
                        print(f"    First item type: {type(value[0])}")
                        print(f"    First item: {value[0]}")
                else:
                    print(f"    Value: {value}")

        # Specifically check 'result' field
        print(f"\n\nRESULT FIELD ANALYSIS:")
        print("=" * 60)

        result = data.get('result')
        print(f"data.get('result') type: {type(result)}")

        if result is None:
            print("WARNING: 'result' is None!")
        elif isinstance(result, str):
            print(f"Result is a STRING with {len(result)} characters")

            # Find URLs in the result
            url_pattern = r'https?://[^\s<>\[\]()\"\']+'
            urls = re.findall(url_pattern, result)
            print(f"\nFound {len(urls)} URLs in result:")
            for i, url in enumerate(urls[:10]):
                print(f"  {i+1}. {url}")

            # Check for markdown links
            md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            md_links = re.findall(md_link_pattern, result)
            print(f"\nFound {len(md_links)} markdown links:")
            for i, (text, url) in enumerate(md_links[:10]):
                print(f"  {i+1}. [{text}]({url})")

            # Print full result
            print(f"\n\nFULL RESULT TEXT:")
            print("-" * 60)
            print(result)
            print("-" * 60)

        elif isinstance(result, dict):
            print(f"WARNING: Result is a DICT, not a string!")
            print(f"Dict keys: {list(result.keys())}")
            print(f"Dict content: {json.dumps(result, indent=2)[:1000]}")
        elif isinstance(result, list):
            print(f"WARNING: Result is a LIST, not a string!")
            print(f"List length: {len(result)}")
            print(f"List content: {result[:5]}")
        else:
            print(f"WARNING: Result is unexpected type: {type(result)}")
            print(f"Value: {result}")

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        print(f"Raw response: {response.text[:500]}")


def test_generate_ai_response_directly():
    """Test what generate_ai_response returns by calling a simple endpoint."""

    print("\n\n")
    print("=" * 60)
    print("TESTING generate_ai_response OUTPUT FORMAT")
    print("=" * 60)

    # Call interview-questions which uses generate_ai_response
    payload = {
        "subject": "Neil Armstrong",
        "role": "Apollo 11 Commander",
        "context": "First person to walk on the moon",
        "projectTitle": "Apollo 11 Documentary"
    }

    print(f"\nCalling: {BASE_URL}/api/ai/interview-questions")

    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/interview-questions",
            json=payload,
            timeout=120
        )

        data = response.json()
        print(f"\nResponse type: {type(data)}")
        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

        result = data.get('result')
        print(f"\n'result' type: {type(result)}")

        if isinstance(result, str):
            print(f"'result' is a string with {len(result)} chars")
            print(f"\nFirst 300 chars:")
            print(result[:300])
        else:
            print(f"WARNING: 'result' is not a string: {type(result)}")
            print(f"Value: {result}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    test_simple_research()
    test_generate_ai_response_directly()

    print("\n\n")
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
