from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from datetime import datetime, timedelta
from src.app import load_tasks, save_tasks, load_categories, save_categories
from src.tasks import create_task

# Load scenarios from feature files
scenarios("../features")


# Fixtures
@pytest.fixture
def context():
    return {}


# Given steps
@given("I have an empty task list")
def empty_task_list(context):
    context["tasks"] = []
    save_tasks(context["tasks"])


@given(parsers.parse('I have a task with title "{title}" and due date "{due_date}"'))
def task_with_title_and_due_date(context, title, due_date):
    context["tasks"] = [
        create_task(
            title=title,
            description="Test description",
            priority="Medium",
            category="Work",
            due_date=due_date,
        )
    ]
    save_tasks(context["tasks"])


@given(parsers.parse('I have a task with priority "{priority}"'))
def task_with_priority(context, priority):
    context["tasks"] = [
        create_task(
            title="Test Task",
            description="Test description",
            priority=priority,
            category="Work",
            due_date=datetime.now().strftime("%Y-%m-%d"),
        )
    ]
    save_tasks(context["tasks"])


@given(parsers.parse('I have a task in category "{category}"'))
def task_in_category(context, category):
    context["tasks"] = [
        create_task(
            title="Test Task",
            description="Test description",
            priority="Medium",
            category=category,
            due_date=datetime.now().strftime("%Y-%m-%d"),
        )
    ]
    save_tasks(context["tasks"])


# When steps
@when(parsers.parse('I add a new task with title "{title}"'))
def add_new_task(context, title):
    new_task = create_task(
        title=title,
        description="Test description",
        priority="Medium",
        category="Work",
        due_date=datetime.now().strftime("%Y-%m-%d"),
    )
    context["tasks"].append(new_task)
    save_tasks(context["tasks"])


@when("I mark the task as completed")
def mark_task_completed(context):
    context["tasks"][0]["completed"] = True
    save_tasks(context["tasks"])


@when(parsers.parse('I add a new category "{category}"'))
def add_new_category(context, category):
    categories = load_categories()
    if category not in categories:
        categories.append(category)
        save_categories(categories)


# Then steps
@then(parsers.parse('the task list should contain "{count}" tasks'))
def verify_task_count(context, count):
    tasks = load_tasks()
    assert len(tasks) == int(count)


@then("the task should be marked as completed")
def verify_task_completed(context):
    tasks = load_tasks()
    assert tasks[0]["completed"] is True


@then(parsers.parse('the task should be displayed with "{color}" color'))
def verify_task_color(context, color):
    tasks = load_tasks()
    priority_colors = {"High": "red", "Medium": "orange", "Low": "green"}
    assert priority_colors.get(tasks[0]["priority"]) == color


@then(parsers.parse('the task should be in the "{status}" section'))
def verify_task_status(context, status):
    tasks = load_tasks()
    today = datetime.now().date()
    task_date = datetime.strptime(tasks[0]["due_date"], "%Y-%m-%d").date()

    if status == "overdue":
        assert task_date < today
    elif status == "today":
        assert task_date == today
    elif status == "upcoming":
        assert task_date > today


@then(parsers.parse('the category list should contain "{category}"'))
def verify_category_exists(context, category):
    categories = load_categories()
    assert category in categories
