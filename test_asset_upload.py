#!/usr/bin/env python3
"""
Test script for asset file upload and download functionality.
Tests the full flow: upload file -> verify asset created -> download -> verify content
Supports chunked uploads for files >30MB.
"""

import requests
import os
import hashlib
import time
import math

BASE_URL = "https://doc-production-app-dev-d3uk63glya-uc.a.run.app"
TEST_FILE = "/Data/Clients/ArrowMedia/WhatsApp Video 2026-02-03 at 12.43.04.mp4"
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
MAX_DIRECT_UPLOAD = 30 * 1024 * 1024  # 30MB - use chunked upload for larger files


def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_or_create_project():
    """Get existing project or create a test project."""
    print("=" * 60)
    print("SETUP: Get or Create Project")
    print("=" * 60)

    # Try to get existing projects
    response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
    if response.status_code == 200:
        projects = response.json()
        if projects:
            project_id = projects[0]['id']
            print(f"  Using existing project: {project_id}")
            return project_id

    # Create a new project
    project_data = {
        "title": "Test Project for Asset Upload",
        "description": "Automated test project",
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
        return project['id']
    else:
        print(f"  Failed to create project: {response.status_code}")
        return None


def test_file_exists():
    """Test that the test file exists."""
    print("\n" + "=" * 60)
    print("TEST 1: Test File Exists")
    print("=" * 60)

    exists = os.path.exists(TEST_FILE)
    file_size = os.path.getsize(TEST_FILE) if exists else 0

    print(f"  File path: {TEST_FILE}")
    print(f"  {'✓' if exists else '✗'} File exists")

    if exists:
        print(f"  ✓ File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        file_hash = get_file_hash(TEST_FILE)
        print(f"  ✓ MD5 hash: {file_hash}")

    print(f"\n  Result: {'PASSED' if exists else 'FAILED'}")
    return exists


def test_upload_asset(project_id):
    """Test uploading a file as an asset (uses chunked upload for large files)."""
    print("\n" + "=" * 60)
    print("TEST 2: Upload Asset File")
    print("=" * 60)

    if not project_id:
        print("  Skipped - no project ID")
        return None

    file_size = os.path.getsize(TEST_FILE)
    filename = os.path.basename(TEST_FILE)
    print(f"  Uploading: {filename}")
    print(f"  Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

    start_time = time.time()

    # Use chunked upload for large files
    if file_size > MAX_DIRECT_UPLOAD:
        print(f"  Using chunked upload (file > {MAX_DIRECT_UPLOAD / 1024 / 1024:.0f}MB)")
        asset_id = upload_chunked(project_id, filename, file_size)
    else:
        print(f"  Using direct upload")
        asset_id = upload_direct(project_id, filename)

    elapsed = time.time() - start_time
    speed = file_size / elapsed / 1024 / 1024 if elapsed > 0 else 0

    print(f"  Total upload time: {elapsed:.1f} seconds")
    print(f"  Average speed: {speed:.2f} MB/s")

    if asset_id:
        print(f"\n  Result: PASSED")
    else:
        print(f"\n  Result: FAILED")

    return asset_id


def upload_direct(project_id, filename):
    """Upload a small file directly."""
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (filename, f, 'video/mp4')}
        data = {
            'projectId': project_id,
            'title': 'Test Video Upload',
            'type': 'Video',
            'status': 'Acquired',
            'notes': f'Automated upload test - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        }

        response = requests.post(
            f"{BASE_URL}/api/assets/upload",
            files=files,
            data=data,
            timeout=300
        )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 201:
        result = response.json()
        asset = result.get('asset', {})
        asset_id = asset.get('id')
        print(f"  ✓ Asset created with ID: {asset_id}")
        print(f"  ✓ GCS path: {result.get('gcsPath', 'N/A')}")
        return asset_id
    else:
        print(f"  ✗ Upload failed: {response.text[:200]}")
        return None


def upload_chunked(project_id, filename, file_size):
    """Upload a large file using chunked upload."""
    total_chunks = math.ceil(file_size / CHUNK_SIZE)

    # Step 1: Initialize upload
    print(f"  Initializing chunked upload ({total_chunks} chunks)...")
    init_response = requests.post(
        f"{BASE_URL}/api/assets/upload/init",
        json={
            'filename': filename,
            'contentType': 'video/mp4',
            'fileSize': file_size,
            'totalChunks': total_chunks,
            'projectId': project_id,
            'title': 'Test Video Upload',
            'type': 'Video',
            'status': 'Acquired',
            'notes': f'Automated chunked upload test - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        },
        timeout=30
    )

    if init_response.status_code != 200:
        print(f"  ✗ Failed to initialize upload: {init_response.text[:200]}")
        return None

    init_data = init_response.json()
    upload_id = init_data['uploadId']
    blob_path = init_data['blobPath']
    print(f"  ✓ Upload initialized: {upload_id}")

    # Step 2: Upload chunks
    bytes_uploaded = 0
    with open(TEST_FILE, 'rb') as f:
        for chunk_index in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)
            chunk_size = len(chunk_data)

            response = requests.post(
                f"{BASE_URL}/api/assets/upload/chunk/{upload_id}",
                files={'chunk': ('chunk', chunk_data, 'application/octet-stream')},
                data={
                    'chunkIndex': chunk_index,
                    'totalChunks': total_chunks,
                    'blobPath': blob_path,
                    'contentType': 'video/mp4'
                },
                timeout=120
            )

            if response.status_code != 200:
                print(f"  ✗ Chunk {chunk_index + 1} failed: {response.text[:100]}")
                return None

            bytes_uploaded += chunk_size
            progress = (bytes_uploaded / file_size) * 100
            print(f"  Chunk {chunk_index + 1}/{total_chunks}: {chunk_size:,} bytes ({progress:.1f}%)")

    print(f"  ✓ All chunks uploaded")

    # Step 3: Complete upload
    print(f"  Completing upload...")
    complete_response = requests.post(
        f"{BASE_URL}/api/assets/upload/complete/{upload_id}",
        json={
            'blobPath': blob_path,
            'contentType': 'video/mp4',
            'projectId': project_id,
            'filename': filename,
            'title': 'Test Video Upload',
            'type': 'Video',
            'status': 'Acquired',
            'notes': f'Automated chunked upload test - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        },
        timeout=120
    )

    if complete_response.status_code != 201:
        print(f"  ✗ Failed to complete upload: {complete_response.text[:200]}")
        return None

    result = complete_response.json()
    asset = result.get('asset', {})
    asset_id = asset.get('id')

    print(f"  ✓ Asset created with ID: {asset_id}")
    print(f"  ✓ GCS path: {result.get('gcsPath', 'N/A')}")
    print(f"  ✓ Size: {result.get('size', 0):,} bytes")

    return asset_id


def test_verify_asset(asset_id):
    """Test that the asset was created correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Verify Asset Created")
    print("=" * 60)

    if not asset_id:
        print("  Skipped - no asset ID")
        return False

    # Get all assets and find ours
    response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
    if response.status_code != 200:
        print(f"  ✗ Failed to get projects")
        return False

    projects = response.json()
    if not projects:
        print(f"  ✗ No projects found")
        return False

    project_id = projects[0]['id']
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/assets", timeout=30)

    if response.status_code != 200:
        print(f"  ✗ Failed to get assets: {response.status_code}")
        return False

    assets = response.json()
    asset = next((a for a in assets if a.get('id') == asset_id), None)

    if not asset:
        print(f"  ✗ Asset not found in project assets")
        return False

    checks = [
        ("Has ID", asset.get('id') == asset_id),
        ("Has title", asset.get('title') == 'Test Video Upload'),
        ("Has type", asset.get('type') == 'Video'),
        ("Has GCS path", bool(asset.get('gcsPath'))),
        ("Has filename", bool(asset.get('filename'))),
        ("Has size", asset.get('sizeBytes', 0) > 0),
        ("Has file flag", asset.get('hasFile') == True),
        ("Has mime type", 'video' in asset.get('mimeType', '')),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"  Asset details:")
        print(f"    - Filename: {asset.get('filename')}")
        print(f"    - Size: {asset.get('sizeBytes', 0):,} bytes")
        print(f"    - MIME: {asset.get('mimeType')}")

    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_download_asset(asset_id):
    """Test downloading the asset file and verify integrity."""
    print("\n" + "=" * 60)
    print("TEST 4: Download Asset File")
    print("=" * 60)

    if not asset_id:
        print("  Skipped - no asset ID")
        return False

    original_hash = get_file_hash(TEST_FILE)
    original_size = os.path.getsize(TEST_FILE)

    print(f"  Original file hash: {original_hash}")
    print(f"  Original file size: {original_size:,} bytes")

    start_time = time.time()

    response = requests.get(
        f"{BASE_URL}/api/assets/{asset_id}/file",
        timeout=300,
        stream=True
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code != 200:
        print(f"  ✗ Download failed")
        print(f"  Response: {response.text[:200]}")
        print(f"\n  Result: FAILED")
        return False

    # Download content
    content = response.content
    elapsed = time.time() - start_time
    speed = len(content) / elapsed / 1024 / 1024 if elapsed > 0 else 0

    print(f"  Download time: {elapsed:.1f} seconds")
    print(f"  Speed: {speed:.2f} MB/s")
    print(f"  Downloaded size: {len(content):,} bytes")

    # Calculate hash of downloaded content
    downloaded_hash = hashlib.md5(content).hexdigest()
    print(f"  Downloaded hash: {downloaded_hash}")

    # Verify
    size_match = len(content) == original_size
    hash_match = downloaded_hash == original_hash

    print(f"  {'✓' if size_match else '✗'} Size matches: {len(content):,} == {original_size:,}")
    print(f"  {'✓' if hash_match else '✗'} Hash matches: {downloaded_hash} == {original_hash}")

    # Check content-disposition header
    content_disp = response.headers.get('Content-Disposition', '')
    has_filename = 'filename=' in content_disp
    print(f"  {'✓' if has_filename else '✗'} Content-Disposition header: {content_disp[:60]}...")

    passed = size_match and hash_match
    print(f"\n  Result: {'PASSED' if passed else 'FAILED'}")
    return passed


def test_delete_asset(asset_id):
    """Test deleting the test asset (cleanup)."""
    print("\n" + "=" * 60)
    print("TEST 5: Delete Test Asset (Cleanup)")
    print("=" * 60)

    if not asset_id:
        print("  Skipped - no asset ID")
        return False

    response = requests.delete(
        f"{BASE_URL}/api/assets/{asset_id}",
        timeout=30
    )

    print(f"  Status code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Asset deleted successfully")
        print(f"  ✓ Success: {result.get('success', False)}")
        print(f"\n  Result: PASSED")
        return True
    else:
        print(f"  ✗ Failed to delete asset")
        print(f"\n  Result: FAILED")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ASSET UPLOAD/DOWNLOAD TEST SUITE")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print(f"Test file: {TEST_FILE}")
    print("=" * 60)

    results = []
    asset_id = None

    try:
        # Setup
        project_id = get_or_create_project()

        # Tests
        results.append(("Test File Exists", test_file_exists()))

        asset_id = test_upload_asset(project_id)
        results.append(("Upload Asset", asset_id is not None))

        results.append(("Verify Asset Created", test_verify_asset(asset_id)))
        results.append(("Download Asset", test_download_asset(asset_id)))
        results.append(("Delete Asset (Cleanup)", test_delete_asset(asset_id)))

    except Exception as e:
        print(f"\n\nTEST ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Try to cleanup even on error
        if asset_id:
            try:
                requests.delete(f"{BASE_URL}/api/assets/{asset_id}", timeout=10)
                print(f"\nCleanup: Deleted test asset {asset_id}")
            except:
                pass

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
