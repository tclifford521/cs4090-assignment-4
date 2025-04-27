import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os
from src.app import (
    run_tests,
    main,
    manage_categories,
    display_tasks_with_colors,
    get_due_date_notifications,
    get_priority_color,
    task_creation_form,
    filter_tasks,
)
from datetime import datetime, timedelta
import streamlit as st
import json


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components"""
    with patch("src.app.st") as mock:
        # Create mock components
        mock.container = MagicMock()
        mock.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        mock.button = MagicMock(return_value=False)
        mock.text_input = MagicMock(return_value="")
        mock.text_area = MagicMock(return_value="")
        mock.selectbox = MagicMock(return_value="Low")
        mock.date_input = MagicMock(return_value=datetime.now())
        mock.checkbox = MagicMock(return_value=False)
        mock.markdown = MagicMock()
        mock.warning = MagicMock()
        mock.error = MagicMock()
        mock.info = MagicMock()
        mock.success = MagicMock()
        mock.write = MagicMock()
        mock.title = MagicMock()
        mock.header = MagicMock()
        mock.subheader = MagicMock()
        mock.code = MagicMock()
        mock.form = MagicMock()
        mock.form_submit_button = MagicMock(return_value=False)
        mock.session_state = MagicMock()

        # Setup sidebar
        mock_sidebar = MagicMock()
        mock_sidebar.header = MagicMock()
        mock_sidebar.form = MagicMock()
        mock_sidebar.text_input = mock.text_input
        mock_sidebar.selectbox = mock.selectbox
        mock_sidebar.date_input = mock.date_input
        mock.sidebar = mock_sidebar

        yield mock


@pytest.fixture
def mock_save_tasks():
    with patch("src.app.save_tasks") as mock_save:
        yield mock_save


@pytest.fixture
def mock_load_tasks():
    """Mock the load_tasks function"""
    with patch("src.app.load_tasks") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_tasks():
    """Mock tasks list"""
    return []


def test_run_tests(mock_subprocess):
    """Test the run_tests function."""
    # Setup mock return value for successful test run
    mock_result = MagicMock()
    mock_result.stdout = "Test output\n\nCoverage\nTOTAL 100%"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    # Test successful test execution
    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    # The implementation splits at "TOTAL" and strips the first part
    assert result["test_results"] == "Test output\n\nCoverage"
    assert result["coverage"] == "TOTAL 100%"

    # Test with error
    error = subprocess.CalledProcessError(1, "pytest")
    error.stdout = "Test execution failed"
    error.stderr = ""
    mock_subprocess.side_effect = error

    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    assert result["test_results"] == "Test execution failed"
    assert result["coverage"] is None

    # Test with no coverage info
    mock_result.stdout = "Test output without coverage"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result
    mock_subprocess.side_effect = None

    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    assert result["test_results"] == "Test output without coverage"
    assert result["coverage"] is None

    # Test HTML report generation
    mock_result.stdout = "HTML coverage report generated in htmlcov directory"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result
    mock_subprocess.side_effect = None

    result = run_tests("html")
    assert isinstance(result, str)  # HTML report returns a string
    assert result == "HTML coverage report generated in htmlcov directory"

    # Test with stderr output
    mock_result.stdout = "Test output"
    mock_result.stderr = "Error output"
    mock_subprocess.return_value = mock_result
    mock_subprocess.side_effect = None

    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    # The implementation combines stdout and stderr
    assert result["test_results"] == "Test output\nError output"
    assert result["coverage"] is None

    # Test with coverage info in stderr
    mock_result.stdout = "Test output"
    mock_result.stderr = "Error output\n\nCoverage\nTOTAL 100%"
    mock_subprocess.return_value = mock_result
    mock_subprocess.side_effect = None

    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    # The implementation splits at "TOTAL" after combining stdout and stderr
    assert result["test_results"] == "Test output\nError output\n\nCoverage"
    assert result["coverage"] == "TOTAL 100%"


def test_run_tests_with_error(mock_subprocess):
    """Test error handling in run_tests function."""
    # Setup mock error
    error = subprocess.CalledProcessError(1, "pytest")
    error.output = "Test output\n"
    mock_subprocess.side_effect = error

    # Run tests and check result
    result = run_tests()
    assert isinstance(result, dict)
    assert "test_results" in result
    assert "coverage" in result
    assert "Test execution failed" in result["test_results"]
    assert result["coverage"] is None


def test_main_with_test_button(mock_streamlit, mock_subprocess, mock_save_tasks):
    """Test the main function with test button interaction."""

    # Setup mock button to return True only for the "Run Tests" button
    def button_side_effect(*args, **kwargs):
        if args and args[0] == "Run All Tests":
            return True
        return False

    mock_streamlit.button.side_effect = button_side_effect

    # Setup mock test results
    mock_result = MagicMock()
    mock_result.stdout = "Test output\nTOTAL 100%"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    # Call main function
    main()

    # Verify test output was displayed
    mock_streamlit.code.assert_any_call("Test output\n")
    mock_streamlit.code.assert_any_call("TOTAL 100%")


def test_main_without_test_button(mock_streamlit, mock_subprocess, mock_save_tasks):
    # Setup mock button to always return False
    mock_streamlit["button"].return_value = False

    # Setup session state
    mock_streamlit["session_state"].__getitem__.return_value = None
    mock_streamlit["session_state"].__setitem__.side_effect = None

    # Call main function
    main()

    # Verify no test output was displayed
    mock_streamlit["write"].assert_not_called()
    mock_streamlit["subheader"].assert_not_called()
    mock_streamlit["code"].assert_not_called()


def test_main_with_empty_coverage(mock_streamlit, mock_subprocess, mock_save_tasks):
    """Test the main function with empty coverage information."""

    # Setup mock button to return True only for the "Run Tests" button
    def button_side_effect(*args, **kwargs):
        if args and args[0] == "Run All Tests":
            return True
        return False

    mock_streamlit.button.side_effect = button_side_effect

    # Setup mock test results without coverage
    mock_result = MagicMock()
    mock_result.stdout = "Test output\n"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    # Call main function
    main()

    # Verify test output was displayed
    mock_streamlit.code.assert_called_with("Test output\n")
    # Verify no coverage section was displayed
    assert mock_streamlit.markdown.call_count == 1  # Only the test results header


def test_task_creation_form(mock_streamlit, mock_save_tasks):
    """Test the task creation form functionality."""
    # Setup mock form inputs
    mock_streamlit.text_input.return_value = "Test Task"
    mock_streamlit.text_area.return_value = "Test Description"
    mock_streamlit.selectbox.side_effect = ["Work", "High"]
    mock_streamlit.date_input.return_value = datetime.now().date()
    mock_streamlit.form_submit_button.return_value = True

    # Call the form function
    task_creation_form()

    # Verify form was created with correct inputs
    mock_streamlit.text_input.assert_called_with(
        "Title*", value="", placeholder="Enter task title"
    )
    mock_streamlit.text_area.assert_called_with(
        "Description*", value="", placeholder="Enter task description", height=100
    )
    mock_streamlit.selectbox.assert_any_call(
        "Category*", options=["Work", "Personal", "Shopping", "Health", "Other"]
    )
    mock_streamlit.selectbox.assert_any_call(
        "Priority*", options=["High", "Medium", "Low"]
    )
    mock_streamlit.date_input.assert_called_with(
        "Due Date*", value=datetime.now().date(), min_value=datetime.now().date()
    )


def test_task_filtering(mock_streamlit, mock_tasks):
    """Test task filtering functionality."""
    # Setup mock tasks
    mock_tasks.extend(
        [
            {
                "title": "Task 1",
                "description": "Description 1",
                "category": "Work",
                "priority": "High",
                "due_date": "2024-03-01",
                "completed": False,
            },
            {
                "title": "Task 2",
                "description": "Description 2",
                "category": "Personal",
                "priority": "Medium",
                "due_date": "2024-03-02",
                "completed": True,
            },
        ]
    )

    # Setup mock filter inputs
    mock_streamlit.checkbox.return_value = True
    mock_streamlit.selectbox.side_effect = ["Work", "High"]

    # Call the main function
    main()

    # Verify filters were applied
    mock_streamlit.checkbox.assert_called_with("Show Completed Tasks", value=False)
    mock_streamlit.selectbox.assert_any_call(
        "Filter by Category", ["All", "Work", "Personal"]
    )
    mock_streamlit.selectbox.assert_any_call(
        "Filter by Priority", ["All", "High", "Medium", "Low"]
    )


def test_task_display_and_interaction(mocker):
    """Test task display and interaction functionality."""
    # Mock Streamlit components
    mock_st = mocker.patch("src.app.st")
    mock_st.session_state = {}
    mock_st.columns.return_value = [mocker.MagicMock() for _ in range(3)]
    mock_st.checkbox.return_value = True
    mock_st.button.return_value = False

    # Create a mock task
    mock_task = {
        "title": "Test Task",
        "description": "Test Description",
        "category": "Work",
        "priority": "High",
        "due_date": "2024-03-20",
        "completed": False,
    }
    mock_tasks = [mock_task]

    # Call the display function
    display_tasks_with_colors(mock_tasks)

    # Verify checkbox was called with correct parameters
    mock_st.checkbox.assert_called_with(
        "Complete", value=False, key=f"task_{mock_task['title']}_completed"
    )

    # Verify task completion was updated
    assert mock_tasks[0]["completed"] == True


def test_main_execution(mock_streamlit):
    """Test the main function execution."""
    # Call the main function
    main()

    # Verify main UI elements were created
    mock_streamlit.set_page_config.assert_called_with(
        page_title="Task Manager", page_icon="📋", layout="wide"
    )
    mock_streamlit.title.assert_called_with("📋 Task Manager")
    mock_streamlit.header.assert_any_call("✏️ Task Form")
    mock_streamlit.header.assert_any_call("📝 Tasks")
    mock_streamlit.header.assert_any_call("🧪 Testing")
    mock_streamlit.header.assert_any_call("📝 BDD Testing")


def test_category_management(mock_streamlit, mock_load_tasks):
    """Test the category management functionality"""
    # Mock initial state
    mock_load_tasks.return_value = []

    # Test adding a new category
    mock_streamlit["text_input"].return_value = "NewCategory"
    mock_streamlit["button"].return_value = True

    result = manage_categories()

    assert "NewCategory" in result
    mock_streamlit["text_input"].assert_called_once_with("Enter new category name")


def test_priority_colors():
    """Test priority color assignment."""
    assert get_priority_color("High") == "red"
    assert get_priority_color("Medium") == "orange"
    assert get_priority_color("Low") == "green"
    assert (
        get_priority_color("Invalid") == "black"
    )  # Default color for invalid priority


def test_due_date_notifications(mock_streamlit, mock_tasks):
    """Test due date notification functionality."""
    # Setup mock tasks with various due dates
    today = datetime.now().date()
    mock_tasks.extend(
        [
            {
                "title": "Overdue Task",
                "description": "Overdue",
                "category": "Work",
                "priority": "High",
                "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                "completed": False,
            },
            {
                "title": "Due Today Task",
                "description": "Due Today",
                "category": "Personal",
                "priority": "Medium",
                "due_date": today.strftime("%Y-%m-%d"),
                "completed": False,
            },
            {
                "title": "Due Soon Task",
                "description": "Due Soon",
                "category": "Shopping",
                "priority": "Low",
                "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "completed": False,
            },
        ]
    )

    # Call the notification function
    notifications = get_due_date_notifications(mock_tasks)

    # Verify notifications were generated correctly
    assert len(notifications) == 3
    assert "Overdue Task" in notifications[0]
    assert "Due Today Task" in notifications[1]
    assert "Due Soon Task" in notifications[2]
    assert "⚠️" in notifications[0]  # Overdue indicator
    assert "📅" in notifications[1]  # Due today indicator
    assert "⏰" in notifications[2]  # Due soon indicator


def test_task_notifications(mock_streamlit):
    """Test the task notification display."""
    # Create test tasks with notifications
    today = datetime.now().date()
    tasks = [
        {
            "title": "Overdue Task",
            "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
        }
    ]

    # Call main function
    main()

    # Verify notifications were displayed
    mock_streamlit.markdown.assert_any_call("### 🔔 Notifications")
    mock_streamlit.warning.assert_called()


def test_task_priority_color(mock_streamlit):
    """Test the task priority color display."""
    # Create test task
    task = {"title": "Test Task", "priority": "High", "completed": False}

    # Call display function
    display_tasks_with_colors([task])

    # Verify priority color was displayed
    mock_streamlit.markdown.assert_any_call(
        "**Priority:** <span style='color: red'>High</span>", unsafe_allow_html=True
    )


def test_task_creation_with_priority(mock_streamlit, mock_tasks):
    """Test task creation with priority selection."""
    # Setup mock form inputs
    mock_streamlit.text_input.return_value = "Test Task"
    mock_streamlit.text_area.return_value = "Test Description"
    mock_streamlit.selectbox.side_effect = ["Work", "High"]
    mock_streamlit.date_input.return_value = datetime.now().date()
    mock_streamlit.form_submit_button.return_value = True

    # Call task creation form
    task_creation_form()

    # Verify task was created
    assert len(mock_tasks) == 1
    assert mock_tasks[0]["title"] == "Test Task"
    assert mock_tasks[0]["priority"] == "High"
    assert mock_tasks[0]["category"] == "Work"


def test_task_completion(mock_streamlit):
    """Test task completion functionality."""
    mock_tasks = [
        {
            "title": "Test Task",
            "description": "Test Description",
            "category": "Work",
            "priority": "High",
            "due_date": "2024-03-20",
            "completed": False,
        }
    ]

    # Mock the checkbox to return True (task completed)
    mock_streamlit.checkbox.return_value = True

    # Call the display function
    display_tasks_with_colors(mock_tasks)

    # Verify the checkbox was called with correct parameters
    mock_streamlit.checkbox.assert_called_with(
        "Test Task", value=False, key="task_Test Task_completed"
    )

    # Verify task completion status was updated
    assert mock_tasks[0]["completed"] == True


def test_task_deletion(mocker):
    """Test task deletion functionality."""
    mock_streamlit = mocker.patch("src.app.st")
    mock_container = mocker.MagicMock()
    mock_streamlit.container.return_value.__enter__.return_value = mock_container
    mock_col = mocker.MagicMock()
    mock_streamlit.columns.return_value = [mock_col, mock_col, mock_col]

    mock_tasks = [
        {
            "title": "Test Task",
            "description": "Test Description",
            "category": "Work",
            "priority": "High",
            "due_date": "2024-03-20",
            "completed": False,
        }
    ]

    # Mock delete button to return True
    mock_streamlit.button.side_effect = [
        False,
        True,
    ]  # First Edit button False, then Delete button True

    # Call the function
    display_tasks_with_colors(mock_tasks)

    # Verify delete button was called
    mock_streamlit.button.assert_any_call("Delete", key="delete_0")

    # Verify task was removed
    assert len(mock_tasks) == 0

    # Verify rerun was called
    mock_streamlit.rerun.assert_called_once()


def test_task_editing(mocker):
    """Test task editing functionality."""
    mock_streamlit = mocker.patch("src.app.st")
    mock_container = mocker.MagicMock()
    mock_streamlit.container.return_value.__enter__.return_value = mock_container
    mock_col = mocker.MagicMock()
    mock_streamlit.columns.return_value = [mock_col, mock_col, mock_col]

    # Initialize session state
    mock_streamlit.session_state = {}

    mock_tasks = [
        {
            "title": "Test Task",
            "description": "Test Description",
            "category": "Work",
            "priority": "High",
            "due_date": "2024-03-20",
            "completed": False,
        }
    ]

    # Mock edit button to return True
    mock_streamlit.button.side_effect = [
        True,
        False,
    ]  # First Edit button True, then Delete button False

    # Call the function
    display_tasks_with_colors(mock_tasks)

    # Verify edit button was called
    mock_streamlit.button.assert_any_call("Edit", key="edit_0")

    # Verify task was set for editing in session state
    assert mock_streamlit.session_state.get("editing_task_index") == 0
    assert mock_streamlit.session_state.get("editing_task") == mock_tasks[0]


def test_task_creation(mock_streamlit):
    """Test task creation functionality."""
    # Setup mock form inputs
    mock_streamlit.text_input.return_value = "Test Task"
    mock_streamlit.text_area.return_value = "Test Description"
    mock_streamlit.selectbox.side_effect = ["Work", "High"]
    mock_streamlit.date_input.return_value = datetime.now().date()
    mock_streamlit.form_submit_button.return_value = True

    # Call task creation form
    task_creation_form()

    # Verify form was created with correct inputs
    mock_streamlit.text_input.assert_called_with(
        "Title*", value="", placeholder="Enter task title"
    )
    mock_streamlit.text_area.assert_called_with(
        "Description*", value="", placeholder="Enter task description", height=100
    )
    mock_streamlit.selectbox.assert_any_call(
        "Category*", options=["Work", "Personal", "Shopping", "Health", "Other"]
    )
    mock_streamlit.selectbox.assert_any_call(
        "Priority*", options=["High", "Medium", "Low"]
    )
    mock_streamlit.date_input.assert_called_with(
        "Due Date*", value=datetime.now().date(), min_value=datetime.now().date()
    )


def test_task_priority(mock_streamlit, mock_tasks):
    """Test task priority functionality."""
    # Setup mock task
    task = {
        "title": "Test Task",
        "description": "Test Description",
        "category": "Work",
        "priority": "High",
        "due_date": "2024-03-01",
        "completed": False,
    }
    mock_tasks.append(task)

    # Setup mock form inputs for editing
    mock_streamlit.text_input.return_value = "Test Task"
    mock_streamlit.text_area.return_value = "Test Description"
    mock_streamlit.selectbox.side_effect = [
        "Work",
        "Medium",
    ]  # Change priority to Medium
    mock_streamlit.date_input.return_value = datetime.now().date()
    mock_streamlit.form_submit_button.return_value = True

    # Call task creation form (which handles editing)
    task_creation_form()

    # Verify priority was updated
    assert mock_tasks[0]["priority"] == "Medium"


def test_task_due_date(mock_streamlit, mock_tasks):
    """Test task due date functionality."""
    # Setup mock task
    task = {
        "title": "Test Task",
        "description": "Test Description",
        "category": "Work",
        "priority": "High",
        "due_date": "2024-03-01",
        "completed": False,
    }
    mock_tasks.append(task)

    # Setup mock form inputs for editing
    new_date = datetime(2024, 3, 15).date()
    mock_streamlit.text_input.return_value = "Test Task"
    mock_streamlit.text_area.return_value = "Test Description"
    mock_streamlit.selectbox.side_effect = ["Work", "High"]
    mock_streamlit.date_input.return_value = new_date
    mock_streamlit.form_submit_button.return_value = True

    # Call task creation form (which handles editing)
    task_creation_form()

    # Verify due date was updated
    assert mock_tasks[0]["due_date"] == new_date.strftime("%Y-%m-%d")


def test_task_categories(mock_streamlit, mock_tasks):
    """Test task categories functionality."""
    # Setup mock tasks with different categories
    mock_tasks.extend(
        [
            {
                "title": "Work Task",
                "category": "Work",
                "priority": "High",
                "completed": False,
            },
            {
                "title": "Personal Task",
                "category": "Personal",
                "priority": "Medium",
                "completed": False,
            },
        ]
    )

    # Setup mock filter inputs
    mock_streamlit.selectbox.side_effect = ["Work", "High"]

    # Call main function
    main()

    # Verify category filter was applied
    mock_streamlit.selectbox.assert_any_call(
        "Filter by Category", ["All", "Work", "Personal"]
    )
    mock_streamlit.selectbox.assert_any_call(
        "Filter by Priority", ["All", "High", "Medium", "Low"]
    )


def test_display_tasks_with_colors(mock_streamlit):
    """Test task display with color coding."""
    # Setup test task
    task = {
        "title": "Test Task",
        "description": "Test Description",
        "category": "Work",
        "priority": "High",
        "due_date": "2024-03-01",
        "completed": False,
    }

    # Call display function
    display_tasks_with_colors([task])

    # Verify task was displayed correctly
    mock_streamlit.checkbox.assert_called_with("Test Task", key="task_0", value=False)
    mock_streamlit.markdown.assert_any_call("_Test Description_")
    mock_streamlit.markdown.assert_any_call("**Category:** Work")
    mock_streamlit.markdown.assert_any_call(
        "**Priority:** <span style='color: red'>High</span>", unsafe_allow_html=True
    )
    mock_streamlit.markdown.assert_any_call("**Due:** 2024-03-01")
    mock_streamlit.button.assert_any_call("✏️", key="edit_0")
    mock_streamlit.button.assert_any_call("🗑️", key="delete_0")


def test_get_due_date_notifications():
    """Test the due date notification system."""
    # Create test tasks with different due dates
    today = datetime.now().date()
    tasks = [
        {
            "title": "Overdue Task",
            "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Due Today Task",
            "due_date": today.strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Upcoming Task",
            "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Completed Task",
            "due_date": today.strftime("%Y-%m-%d"),
            "completed": True,
        },
    ]

    # Get notifications
    notifications = get_due_date_notifications(tasks)

    # Verify notifications
    assert (
        len(notifications) == 3
    )  # Should have 3 notifications (excluding completed task)
    assert any("overdue" in notification.lower() for notification in notifications)
    assert any("due today" in notification.lower() for notification in notifications)
    assert any(
        "due in 2 days" in notification.lower() for notification in notifications
    )


def create_task(title, description, priority, category="Other", due_date=None):
    """Create a new task with all required fields"""
    if due_date is None:
        due_date = datetime.now().strftime("%Y-%m-%d")
    return {
        "id": None,  # Will be set when adding to tasks list
        "title": title,
        "description": description,
        "priority": priority,
        "category": category,
        "due_date": due_date,
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def manage_categories():
    """Manage task categories"""
    categories = ["Work", "Personal", "School", "Other"]
    new_category = st.text_input("Add new category")
    if st.button("Add Category") and new_category:
        categories.append(new_category)
    return categories
