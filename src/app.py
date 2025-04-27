import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import os
import sys
import json
from typing import Dict, List, Optional

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tasks import (
    load_tasks,
    save_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    create_task,
    generate_unique_id,
    validate_task,
)
import subprocess

# Constants for category management
CATEGORIES_FILE = "categories.json"
DEFAULT_CATEGORIES = ["Work", "Personal", "School", "Other"]

# Color mapping for priorities
PRIORITY_COLORS = {"High": "red", "Medium": "orange", "Low": "green"}


def load_categories():
    """Load categories from file or return default categories"""
    try:
        with open(CATEGORIES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CATEGORIES.copy()


def save_categories(categories):
    """Save categories to file"""
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(categories, f, indent=2)


def get_categories() -> List[str]:
    """Get list of available task categories."""
    if "categories" not in st.session_state:
        st.session_state["categories"] = ["Work", "Personal", "School", "Other"]
    return st.session_state["categories"]


def add_category(new_category: str) -> None:
    """Add a new category to the list of available categories."""
    if "categories" not in st.session_state:
        st.session_state["categories"] = ["Work", "Personal", "School", "Other"]
    if new_category and new_category not in st.session_state["categories"]:
        st.session_state["categories"].append(new_category)


def manage_categories():
    """Manage task categories."""
    categories = ["Work", "Personal", "Shopping", "Health", "Other"]

    # Add new category
    new_category = st.text_input("Add New Category")
    if st.button("Add Category") and new_category:
        if new_category not in categories:
            categories.append(new_category)
            st.success(f"Added new category: {new_category}")

    return categories


def get_priority_color(priority: str) -> str:
    """Get color based on task priority."""
    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green",
    }
    return colors.get(priority, "black")  # Black for unknown priority


def filter_tasks(tasks, show_completed=False, category=None, priority=None):
    """Filter tasks based on completion status, category, and priority.

    Args:
        tasks (list): List of tasks to filter
        show_completed (bool): Whether to show completed tasks
        category (str): Category to filter by
        priority (str): Priority to filter by

    Returns:
        list: Filtered list of tasks
    """
    filtered_tasks = tasks

    # Filter by completion status
    if not show_completed:
        filtered_tasks = [
            task for task in filtered_tasks if not task.get("completed", False)
        ]

    # Filter by category
    if category and category != "All":
        filtered_tasks = [
            task for task in filtered_tasks if task.get("category") == category
        ]

    # Filter by priority
    if priority and priority != "All":
        filtered_tasks = [
            task for task in filtered_tasks if task.get("priority") == priority
        ]

    return filtered_tasks


def display_tasks_with_colors(tasks):
    """Display tasks with color coding based on priority."""
    if not tasks:
        st.info("No tasks to display.")
        return

    for i, task in enumerate(tasks):
        with st.container():
            cols = st.columns([2, 2, 1])

            # Column 1: Task title and completion status
            with cols[0]:
                completed = st.checkbox(
                    task.get("title", ""),
                    value=task.get("completed", False),
                    key=f"task_{i}_completed",
                )
                if completed != task.get("completed", False):
                    task["completed"] = completed
                    st.rerun()

            # Column 2: Task details
            with cols[1]:
                priority_color = get_priority_color(task.get("priority", "Low"))
                st.markdown(f"_{task.get('title', '')}_")
                st.markdown(f"_{task.get('description', '')}_")
                st.markdown(f"**Category:** {task.get('category', '')}")
                st.markdown(
                    f"**Priority:** <span style='color: {priority_color}'>{task.get('priority', '')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Due Date:** {task.get('due_date', '')}")

            # Column 3: Action buttons
            with cols[2]:
                if st.button("Edit", key=f"edit_{i}"):
                    st.session_state.editing_task = task
                    st.rerun()
                if st.button("Delete", key=f"delete_{i}"):
                    tasks.remove(task)
                    st.rerun()

            st.markdown("---")  # Add a separator between tasks


def get_due_date_notifications(tasks: List[Dict]) -> List[str]:
    """Generate notifications for tasks based on due dates."""
    notifications = []
    today = datetime.now().date()

    for task in tasks:
        if task.get("completed", False):
            continue

        due_date = task.get("due_date")
        if not due_date:
            continue

        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        days_until_due = (due_date - today).days

        if days_until_due < 0:
            notifications.append(
                f"⚠️ Task '{task.get('title', '')}' is overdue by {abs(days_until_due)} days!"
            )
        elif days_until_due == 0:
            notifications.append(f"📅 Task '{task.get('title', '')}' is due today!")
        elif days_until_due <= 3:
            notifications.append(
                f"⏰ Task '{task.get('title', '')}' is due in {days_until_due} days."
            )

    return notifications


def display_notifications(tasks):
    """Display task notifications."""
    notifications = get_due_date_notifications(tasks)
    if notifications:
        st.markdown("### 🔔 Notifications")
        for notification in notifications:
            st.markdown(notification)


def run_tests():
    """Run pytest and return test results and coverage."""
    try:
        # Run pytest with coverage
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=src", "tests/"],
            capture_output=True,
            text=True,
        )

        # Split output into test results and coverage
        output = result.stdout + result.stderr
        lines = output.split("\n")

        # Find where coverage report starts
        coverage_start = -1
        for i, line in enumerate(lines):
            if "TOTAL" in line:
                coverage_start = i
                break

        # Extract test results and coverage
        test_results = (
            "\n".join(lines[:coverage_start]) if coverage_start > 0 else output
        )
        coverage = lines[coverage_start] if coverage_start >= 0 else None

        # Format coverage line if it exists
        if coverage:
            coverage = coverage.replace("TOTAL", "TOTAL ")

        return {
            "test_results": test_results,
            "coverage": coverage,
            "success": result.returncode == 0,
        }
    except Exception as e:
        return {
            "test_results": f"Test execution failed: {str(e)}",
            "coverage": None,
            "success": False,
        }


def run_bdd_tests():
    """Run BDD tests and return the results"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(
            ["pytest", "tests/test_bdd.py", "-v"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_output = e.output if e.output else "BDD test execution failed"
        return f"{error_output}"


def task_creation_form(editing_task=None):
    """Create a form for adding or editing tasks."""
    with st.form("task_form"):
        st.subheader("✏️ Task Form")

        # Get existing values if editing
        title = editing_task.get("title", "") if editing_task else ""
        description = editing_task.get("description", "") if editing_task else ""
        category = editing_task.get("category", "Work") if editing_task else "Work"
        priority = editing_task.get("priority", "High") if editing_task else "High"
        due_date = (
            datetime.strptime(
                editing_task.get("due_date", datetime.now().strftime("%Y-%m-%d")),
                "%Y-%m-%d",
            ).date()
            if editing_task
            else datetime.now().date()
        )

        # Form fields
        title = st.text_input("Title*", value=title, placeholder="Enter task title")
        description = st.text_area(
            "Description", value=description, placeholder="Enter task description"
        )
        category = st.selectbox(
            "Category",
            ["Work", "Personal", "School", "Other"],
            index=["Work", "Personal", "School", "Other"].index(category),
        )
        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(priority),
        )
        due_date = st.date_input("Due Date", value=due_date)

        # Submit button
        submitted = st.form_submit_button("Submit")

        if submitted and title:
            task = {
                "title": title,
                "description": description,
                "category": category,
                "priority": priority,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "completed": False,
            }
            return task
        return None


def check_overdue_tasks(tasks: List[Dict]) -> None:
    """Check for overdue tasks and display notifications."""
    today = datetime.now().date()

    for task in tasks:
        if task.get("completed", False):
            continue

        due_date = datetime.strptime(task.get("due_date", ""), "%Y-%m-%d").date()
        days_until_due = (due_date - today).days

        if days_until_due < 0:
            st.error(
                f"⚠️ Task '{task['title']}' is overdue by {abs(days_until_due)} days!"
            )
        elif days_until_due == 0:
            st.warning(f"⏰ Task '{task['title']}' is due today!")
        elif days_until_due <= 3:
            st.info(f"📅 Task '{task['title']}' is due in {days_until_due} days.")


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Task Manager", layout="wide")
    st.title("📋 Task Manager")

    # Initialize session state
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    # Task creation/editing form
    st.header("📝 Tasks")
    task = task_creation_form()
    if task:
        if "editing_task" in st.session_state:
            # Update existing task
            index = st.session_state.tasks.index(st.session_state.editing_task)
            st.session_state.tasks[index] = task
            del st.session_state.editing_task
        else:
            # Add new task
            st.session_state.tasks.append(task)
        st.rerun()

    # Task filtering
    filter_cols = st.columns([1, 1, 1])
    with filter_cols[0]:
        category_filter = st.selectbox(
            "Filter by Category", ["All"] + get_categories(), key="category_filter"
        )
    with filter_cols[1]:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "High", "Medium", "Low"],
            key="priority_filter",
        )
    with filter_cols[2]:
        show_completed = st.checkbox("Show Completed Tasks", value=True)

    # Filter tasks
    filtered_tasks = filter_tasks(
        st.session_state.tasks,
        show_completed,
        category_filter if category_filter != "All" else None,
        priority_filter if priority_filter != "All" else None,
    )

    # Display notifications
    display_notifications(filtered_tasks)

    # Display tasks
    display_tasks_with_colors(filtered_tasks)

    # Testing section
    st.markdown("---")
    st.subheader("🧪 Testing")

    # Create three rows of test buttons
    test_row1 = st.columns(2)
    test_row2 = st.columns(2)
    test_row3 = st.columns(2)

    with test_row1[0]:
        if st.button("Run All Tests"):
            import pytest
            import sys
            from io import StringIO

            # Capture test output
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(["--cov=src", "tests/"])
            sys.stdout = old_stdout

            # Display test results
            test_output = mystdout.getvalue()
            st.code(test_output)

            # Display coverage summary if available
            if "TOTAL" in test_output:
                coverage_line = [
                    line for line in test_output.split("\n") if "TOTAL" in line
                ]
                if coverage_line:
                    st.markdown(f"**Coverage Summary:** {coverage_line[0]}")

    with test_row1[1]:
        if st.button("Run BDD Tests"):
            import pytest
            import sys
            from io import StringIO

            # Capture BDD test output
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(["tests/test_bdd.py", "-v"])
            sys.stdout = old_stdout

            # Display BDD test results
            st.code(mystdout.getvalue())

    with test_row2[0]:
        if st.button("Run Coverage Report"):
            import pytest
            import sys
            from io import StringIO

            # Run coverage report with branch coverage
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(
                ["--cov=src", "--cov-branch", "--cov-report=term-missing", "tests/"]
            )
            sys.stdout = old_stdout

            # Display detailed coverage results
            st.code(mystdout.getvalue())

    with test_row2[1]:
        if st.button("Generate HTML Report"):
            import pytest
            import sys
            from io import StringIO
            import webbrowser
            import os

            # Generate HTML coverage report
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(["--cov=src", "--cov-report=html", "tests/"])
            sys.stdout = old_stdout

            # Get the absolute path to the HTML report
            html_report = os.path.abspath("htmlcov/index.html")

            # Display success message and path
            st.success("HTML coverage report generated!")
            st.markdown(f"Report generated at: `{html_report}`")

            # Try to open the report in the default browser
            try:
                webbrowser.open(f"file://{html_report}")
                st.info("Report opened in your default browser")
            except:
                st.warning(
                    "Could not automatically open the report. Please open it manually."
                )

    with test_row3[0]:
        if st.button("Run Parameterized Tests"):
            import pytest
            import sys
            from io import StringIO

            # Run tests with -v to show individual parameter cases
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(
                ["-v", "-k", "test_task_priority or test_task_due_date", "tests/"]
            )
            sys.stdout = old_stdout

            # Display parameterized test results
            st.code(mystdout.getvalue())

    with test_row3[1]:
        if st.button("Run Mock Tests"):
            import pytest
            import sys
            from io import StringIO

            # Run mock-specific tests
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            pytest.main(
                [
                    "-v",
                    "-k",
                    "test_task_completion or test_task_deletion or test_task_display",
                    "tests/",
                ]
            )
            sys.stdout = old_stdout

            # Display mock test results
            st.code(mystdout.getvalue())


if __name__ == "__main__":
    main()
