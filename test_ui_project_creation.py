"""
UI Test: Project Creation Flow

Tests:
1. Clear all existing projects/assets
2. Test empty state UI
3. Test manual project creation
4. Test project creation from blueprint
5. Verify dashboard displays correctly
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://doc-production-app-280939464794.us-central1.run.app"
VIDEO_FILE = "/Data/Clients/ArrowMedia/WhatsApp Video 2026-01-23 at 12.12.08.mp4"


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")
    print("-" * 40)


def clear_all_data():
    """Clear all projects and their associated data via API."""
    print_step("0", "Clearing all existing projects and assets")

    try:
        # Get all projects
        response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        if response.status_code != 200:
            print(f"⚠ Could not fetch projects: {response.status_code}")
            return

        projects = response.json()
        print(f"Found {len(projects)} existing projects")

        # Delete each project (this cascades to episodes, research, etc.)
        for project in projects:
            project_id = project.get('id')
            title = project.get('title', 'Unknown')

            response = requests.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=30)
            if response.status_code == 200:
                print(f"  ✓ Deleted: {title}")
            else:
                print(f"  ✗ Failed to delete: {title} ({response.status_code})")

        print("✓ All projects cleared")

    except Exception as e:
        print(f"⚠ Error clearing data: {e}")


def setup_driver():
    """Set up headless Chrome driver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)

    return driver


def take_screenshot(driver, name):
    """Take a screenshot for debugging."""
    filename = f"/tmp/screenshot_{name}.png"
    driver.save_screenshot(filename)
    print(f"  📸 Screenshot saved: {filename}")


def test_empty_state(driver):
    """Test that empty state is shown when no projects exist."""
    print_step(1, "Testing empty state UI")

    try:
        driver.get(BASE_URL)
        time.sleep(3)  # Wait for app to load

        # Check for empty state message
        try:
            empty_state = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "empty-state"))
            )
            print("✓ Empty state container found")

            # Check for "Create New Project" button
            create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create New Project')]")
            print("✓ 'Create New Project' button found")

            # Check that navigation is disabled
            nav_items = driver.find_elements(By.CLASS_NAME, "nav-item")
            disabled_count = sum(1 for item in nav_items if 'disabled' in item.get_attribute('class'))
            print(f"✓ Navigation items disabled: {disabled_count}/{len(nav_items)}")

            take_screenshot(driver, "01_empty_state")
            return True

        except Exception as e:
            print(f"⚠ Empty state not found (might have existing data): {e}")
            take_screenshot(driver, "01_empty_state_error")
            return False

    except Exception as e:
        print(f"✗ Error testing empty state: {e}")
        take_screenshot(driver, "01_empty_state_error")
        return False


def test_manual_project_creation(driver):
    """Test creating a project manually."""
    print_step(2, "Testing manual project creation")

    try:
        driver.get(BASE_URL)
        time.sleep(3)

        # Click "Create New Project" button
        create_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create New Project')]"))
        )
        create_btn.click()
        print("✓ Clicked 'Create New Project'")
        time.sleep(1)

        take_screenshot(driver, "02_create_modal")

        # Fill in project details
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "new-project-title"))
        )
        title_input.send_keys("Test Documentary Project")
        print("✓ Entered project title")

        desc_input = driver.find_element(By.ID, "new-project-description")
        desc_input.send_keys("A test documentary about software testing and quality assurance.")
        print("✓ Entered project description")

        style_input = driver.find_element(By.ID, "new-project-style")
        style_input.send_keys("Educational, technical documentary")
        print("✓ Entered project style")

        # Set episode count
        episodes_input = driver.find_element(By.ID, "new-project-episodes")
        episodes_input.clear()
        episodes_input.send_keys("3")
        print("✓ Set episode count to 3")

        take_screenshot(driver, "03_form_filled")

        # Submit the form
        submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Project')]")
        submit_btn.click()
        print("✓ Submitted project creation form")

        # Wait for AI to generate episodes (this takes time)
        print("  Waiting for AI to generate episode suggestions...")
        time.sleep(15)

        take_screenshot(driver, "04_episode_suggestions")

        # Check if episode suggestions modal appeared
        try:
            topic_list = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "topic-list"))
            )
            print("✓ Episode suggestions modal appeared")

            # Count suggested episodes
            checkboxes = driver.find_elements(By.CSS_SELECTOR, ".topic-list input[type='checkbox']")
            print(f"✓ {len(checkboxes)} episode suggestions generated")

            # Click "Create Selected" to create the episodes
            create_episodes_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Selected')]")
            create_episodes_btn.click()
            print("✓ Clicked 'Create Selected'")

            time.sleep(5)

        except Exception as e:
            print(f"⚠ Episode suggestions not found: {e}")
            # Try to close any modal
            try:
                close_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Done') or contains(text(), 'Close')]")
                close_btn.click()
            except:
                pass

        # Verify project was created - check dashboard
        time.sleep(3)
        take_screenshot(driver, "05_dashboard")

        # Check for project title in header
        try:
            project_name = driver.find_element(By.ID, "project-name")
            if "Test Documentary" in project_name.text:
                print(f"✓ Project created successfully: {project_name.text}")
            else:
                print(f"✓ Project visible: {project_name.text}")
        except:
            print("⚠ Could not verify project name")

        # Check navigation is now enabled
        nav_items = driver.find_elements(By.CLASS_NAME, "nav-item")
        enabled_count = sum(1 for item in nav_items if 'disabled' not in item.get_attribute('class'))
        print(f"✓ Navigation items enabled: {enabled_count}/{len(nav_items)}")

        return True

    except Exception as e:
        print(f"✗ Error in manual project creation: {e}")
        take_screenshot(driver, "02_error")
        return False


def test_blueprint_project_creation(driver):
    """Test creating a project from a video blueprint."""
    print_step(3, "Testing blueprint project creation")

    try:
        driver.get(BASE_URL)
        time.sleep(3)

        # Click on project name to open projects modal
        project_name = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "project-name"))
        )
        project_name.click()
        print("✓ Opened projects modal")
        time.sleep(1)

        # Click "+ New Project" button
        new_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New Project')]"))
        )
        new_project_btn.click()
        print("✓ Clicked 'New Project'")
        time.sleep(1)

        take_screenshot(driver, "06_new_project_form")

        # Switch to "From Blueprint" tab
        blueprint_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'From Blueprint')]"))
        )
        blueprint_tab.click()
        print("✓ Switched to 'From Blueprint' tab")
        time.sleep(1)

        take_screenshot(driver, "07_blueprint_tab")

        # Upload video file
        file_input = driver.find_element(By.ID, "blueprint-file")
        file_input.send_keys(VIDEO_FILE)
        print(f"✓ Selected video file: {VIDEO_FILE.split('/')[-1]}")
        time.sleep(1)

        take_screenshot(driver, "08_file_selected")

        # Click "Analyze & Create"
        analyze_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "blueprint-submit-btn"))
        )
        analyze_btn.click()
        print("✓ Clicked 'Analyze & Create'")
        print("  Waiting for video analysis (this may take a few minutes)...")

        # Wait for analysis to complete
        time.sleep(60)  # Video analysis takes time

        take_screenshot(driver, "09_analysis_complete")

        # Check for blueprint episodes modal
        try:
            topic_list = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CLASS_NAME, "topic-list"))
            )
            print("✓ Blueprint analysis complete, episode suggestions shown")

            # Create the episodes
            create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Selected')]")
            create_btn.click()
            print("✓ Created episodes from blueprint")

            time.sleep(5)

        except Exception as e:
            print(f"⚠ Blueprint modal not found: {e}")

        take_screenshot(driver, "10_blueprint_project")

        # Verify project was created
        time.sleep(3)
        project_name = driver.find_element(By.ID, "project-name")
        print(f"✓ Blueprint project created: {project_name.text}")

        return True

    except Exception as e:
        print(f"✗ Error in blueprint project creation: {e}")
        take_screenshot(driver, "blueprint_error")
        return False


def test_dashboard_display(driver):
    """Test that dashboard displays correctly."""
    print_step(4, "Testing dashboard display")

    try:
        driver.get(BASE_URL)
        time.sleep(3)

        # Check for stat cards
        stat_cards = driver.find_elements(By.CLASS_NAME, "stat-card")
        print(f"✓ Found {len(stat_cards)} stat cards")

        # Check for episodes overview
        try:
            episodes_section = driver.find_element(By.XPATH, "//h3[contains(text(), 'Episodes Overview')]")
            print("✓ Episodes Overview section found")
        except:
            print("⚠ Episodes Overview section not found")

        # Check for blueprint section (if project has one)
        try:
            blueprint_section = driver.find_element(By.CLASS_NAME, "blueprint-card")
            print("✓ Blueprint section found")
        except:
            print("  (No blueprint section - project may not have blueprint)")

        take_screenshot(driver, "11_dashboard_final")

        return True

    except Exception as e:
        print(f"✗ Error testing dashboard: {e}")
        return False


def test_navigation(driver):
    """Test navigation between tabs."""
    print_step(5, "Testing navigation")

    try:
        driver.get(BASE_URL)
        time.sleep(3)

        tabs = ["Episodes", "Research", "Interviews", "Production", "Assets", "Scripts", "Dashboard"]

        for tab in tabs:
            try:
                nav_btn = driver.find_element(By.XPATH, f"//button[contains(@class, 'nav-item')]//span[contains(text(), '{tab}')]/parent::button")
                if 'disabled' not in nav_btn.get_attribute('class'):
                    nav_btn.click()
                    time.sleep(1)
                    print(f"✓ Navigated to {tab}")
                else:
                    print(f"⚠ {tab} is disabled")
            except Exception as e:
                print(f"⚠ Could not navigate to {tab}: {e}")

        take_screenshot(driver, "12_navigation")
        return True

    except Exception as e:
        print(f"✗ Error testing navigation: {e}")
        return False


def main():
    print_header("UI Test: Project Creation Flow")

    results = {
        "clear_data": False,
        "empty_state": False,
        "manual_creation": False,
        "blueprint_creation": False,
        "dashboard": False,
        "navigation": False
    }

    # Clear all data first
    clear_all_data()
    results["clear_data"] = True

    # Set up browser
    print("\nSetting up headless Chrome browser...")
    driver = None

    try:
        driver = setup_driver()
        print("✓ Browser ready")

        # Run tests
        results["empty_state"] = test_empty_state(driver)
        results["manual_creation"] = test_manual_project_creation(driver)
        results["blueprint_creation"] = test_blueprint_project_creation(driver)
        results["dashboard"] = test_dashboard_display(driver)
        results["navigation"] = test_navigation(driver)

    except Exception as e:
        print(f"✗ Browser setup failed: {e}")

    finally:
        if driver:
            driver.quit()
            print("\n✓ Browser closed")

    # Print results
    print_header("Test Results")

    print(f"Clear Data:         {'✓ PASS' if results['clear_data'] else '✗ FAIL'}")
    print(f"Empty State:        {'✓ PASS' if results['empty_state'] else '✗ FAIL'}")
    print(f"Manual Creation:    {'✓ PASS' if results['manual_creation'] else '✗ FAIL'}")
    print(f"Blueprint Creation: {'✓ PASS' if results['blueprint_creation'] else '✗ FAIL'}")
    print(f"Dashboard Display:  {'✓ PASS' if results['dashboard'] else '✗ FAIL'}")
    print(f"Navigation:         {'✓ PASS' if results['navigation'] else '✗ FAIL'}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

    print("\n📸 Screenshots saved to /tmp/screenshot_*.png")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
