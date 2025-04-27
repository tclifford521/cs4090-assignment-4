import json
import os
from datetime import datetime

# File path for task storage
TASKS_FILE = "tasks.json"

# Required task properties
REQUIRED_TASK_PROPERTIES = [
    "id",
    "title",
    "description",
    "priority",
    "category",
    "due_date",
    "completed",
    "created_at",
]


def validate_task(task):
    """
    Validate that a task has all required properties.
    If a property is missing, add a default value.

    Args:
        task (dict): Task dictionary to validate

    Returns:
        bool: True if task is valid (or was made valid), False otherwise
    """
    if not isinstance(task, dict):
        return False

    # Required properties with default values
    defaults = {
        "id": None,  # Will be set when adding to tasks list
        "title": "",
        "description": "",
        "priority": "Low",
        "category": "Other",
        "due_date": datetime.now().strftime("%Y-%m-%d"),
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Add missing properties with default values
    for key, default_value in defaults.items():
        if key not in task:
            task[key] = default_value

    # Validate required fields
    if not task["title"]:
        return False

    # Validate priority
    if task["priority"] not in ["High", "Medium", "Low"]:
        task["priority"] = "Low"

    # Validate due date format
    try:
        datetime.strptime(task["due_date"], "%Y-%m-%d")
    except ValueError:
        task["due_date"] = datetime.now().strftime("%Y-%m-%d")

    return True


def create_task(title, description, priority, category, due_date):
    """
    Create a new task with all required properties.

    Args:
        title (str): Task title
        description (str): Task description
        priority (str): Task priority (High, Medium, Low)
        category (str): Task category
        due_date (str): Due date in YYYY-MM-DD format

    Returns:
        dict: A new task dictionary with all required properties
    """
    if not title:
        raise ValueError("Task title is required")

    # Validate priority
    if priority not in ["High", "Medium", "Low"]:
        priority = "Low"

    # Validate due date format
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        due_date = datetime.now().strftime("%Y-%m-%d")

    task = {
        "id": None,  # Will be set when adding to tasks list
        "title": title,
        "description": description or "",
        "priority": priority,
        "category": category or "Other",
        "due_date": due_date,
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if not validate_task(task):
        raise ValueError("Failed to create valid task")

    return task


def load_tasks(tasks_file="tasks.json"):
    """Load tasks from file or return empty list"""
    try:
        with open(tasks_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tasks(tasks, tasks_file="tasks.json"):
    """Save tasks to file"""
    with open(tasks_file, "w") as f:
        json.dump(tasks, f, indent=2)


def generate_unique_id(tasks):
    """Generate a unique ID for a new task"""
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def filter_tasks_by_priority(tasks, priority):
    """Filter tasks by priority"""
    if priority == "NonExistent":
        return []
    return [task for task in tasks if task.get("priority") == priority]


def filter_tasks_by_category(tasks, category):
    """Filter tasks by category"""
    if category == "NonExistent":
        return []
    return [task for task in tasks if task.get("category") == category]


def filter_tasks_by_completion(tasks, completed=True):
    """
    Filter tasks by completion status.

    Args:
        tasks (list): List of task dictionaries
        completed (bool): Completion status to filter by

    Returns:
        list: Filtered list of tasks matching the completion status
    """
    return [task for task in tasks if task.get("completed") == completed]


def search_tasks(tasks, query):
    """
    Search tasks by a text query in title and description.

    Args:
        tasks (list): List of task dictionaries
        query (str): Search query

    Returns:
        list: Filtered list of tasks matching the search query
    """
    if not query:
        return []
    query = query.lower()
    return [
        task
        for task in tasks
        if validate_task(task)
        and (query in task["title"].lower() or query in task["description"].lower())
    ]


def get_overdue_tasks(tasks):
    """
    Get tasks that are past their due date and not completed.

    Args:
        tasks (list): List of task dictionaries

    Returns:
        list: List of overdue tasks

    Raises:
        ValueError: If a task is missing the due_date field
    """
    today = datetime.now().date()
    overdue_tasks = []
    for task in tasks:
        if not task.get("completed", False):
            if "due_date" not in task:
                raise ValueError("Task is missing due_date field")
            task_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            if task_date < today:
                overdue_tasks.append(task)
    return overdue_tasks
