import pytest
import json
import os
from datetime import datetime, timedelta
from src.tasks import (
    load_tasks,
    save_tasks,
    generate_unique_id,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    filter_tasks_by_completion,
    search_tasks,
    get_overdue_tasks,
)


@pytest.fixture
def sample_tasks():
    return [
        {
            "id": 1,
            "title": "Test Task 1",
            "description": "Description 1",
            "priority": "High",
            "category": "Work",
            "completed": False,
            "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "id": 2,
            "title": "Test Task 2",
            "description": "Description 2",
            "priority": "Medium",
            "category": "Personal",
            "completed": True,
            "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "id": 3,
            "title": "Test Task 3",
            "description": "Description 3",
            "priority": "Low",
            "category": "Work",
            "completed": False,
            "due_date": datetime.now().strftime("%Y-%m-%d"),
        },
    ]


@pytest.fixture
def temp_tasks_file(tmp_path, sample_tasks):
    file_path = tmp_path / "test_tasks.json"
    with open(file_path, "w") as f:
        json.dump(sample_tasks, f)
    return file_path


@pytest.fixture
def corrupted_tasks_file(tmp_path):
    file_path = tmp_path / "corrupted_tasks.json"
    with open(file_path, "w") as f:
        f.write("invalid json content")
    return file_path


def test_load_tasks(temp_tasks_file, sample_tasks, corrupted_tasks_file):
    # Test loading existing tasks
    loaded_tasks = load_tasks(str(temp_tasks_file))
    assert loaded_tasks == sample_tasks

    # Test loading non-existent file
    non_existent_file = "non_existent.json"
    assert load_tasks(non_existent_file) == []

    # Test loading corrupted file
    assert load_tasks(str(corrupted_tasks_file)) == []


def test_save_tasks(temp_tasks_file, sample_tasks):
    # Test saving tasks
    new_task = {
        "id": 4,
        "title": "New Task",
        "description": "New Description",
        "priority": "Low",
        "category": "Work",
        "completed": False,
        "due_date": datetime.now().strftime("%Y-%m-%d"),
    }
    sample_tasks.append(new_task)
    save_tasks(sample_tasks, str(temp_tasks_file))

    with open(temp_tasks_file, "r") as f:
        saved_tasks = json.load(f)
    assert saved_tasks == sample_tasks

    # Test saving to read-only location
    with pytest.raises(IOError):
        save_tasks(sample_tasks, "/readonly/location/tasks.json")


def test_generate_unique_id(sample_tasks):
    # Test with existing tasks
    assert generate_unique_id(sample_tasks) == 4

    # Test with empty list
    assert generate_unique_id([]) == 1

    # Test with single task
    assert generate_unique_id([{"id": 1}]) == 2


def test_filter_tasks_by_priority(sample_tasks):
    # Test filtering high priority tasks
    high_priority = filter_tasks_by_priority(sample_tasks, "High")
    assert len(high_priority) == 1
    assert high_priority[0]["id"] == 1

    # Test filtering medium priority tasks
    medium_priority = filter_tasks_by_priority(sample_tasks, "Medium")
    assert len(medium_priority) == 1
    assert medium_priority[0]["id"] == 2

    # Test filtering low priority tasks
    low_priority = filter_tasks_by_priority(sample_tasks, "Low")
    assert len(low_priority) == 1
    assert low_priority[0]["id"] == 3

    # Test filtering non-existent priority
    assert filter_tasks_by_priority(sample_tasks, "NonExistent") == []


def test_filter_tasks_by_category(sample_tasks):
    # Test filtering work category tasks
    work_tasks = filter_tasks_by_category(sample_tasks, "Work")
    assert len(work_tasks) == 2
    assert all(task["category"] == "Work" for task in work_tasks)

    # Test filtering personal category tasks
    personal_tasks = filter_tasks_by_category(sample_tasks, "Personal")
    assert len(personal_tasks) == 1
    assert personal_tasks[0]["id"] == 2

    # Test filtering non-existent category
    assert filter_tasks_by_category(sample_tasks, "NonExistent") == []


def test_filter_tasks_by_completion(sample_tasks):
    # Test filtering completed tasks
    completed_tasks = filter_tasks_by_completion(sample_tasks, True)
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["id"] == 2

    # Test filtering incomplete tasks
    incomplete_tasks = filter_tasks_by_completion(sample_tasks, False)
    assert len(incomplete_tasks) == 2
    assert all(not task["completed"] for task in incomplete_tasks)

    # Test filtering with no completion status
    tasks_without_completion = [{"id": 1}, {"id": 2, "completed": True}]
    assert len(filter_tasks_by_completion(tasks_without_completion, True)) == 1
    assert len(filter_tasks_by_completion(tasks_without_completion, False)) == 0


def test_search_tasks(sample_tasks):
    # Test searching by title
    title_results = search_tasks(sample_tasks, "Task 1")
    assert len(title_results) == 1
    assert title_results[0]["id"] == 1

    # Test searching by description
    desc_results = search_tasks(sample_tasks, "Description 2")
    assert len(desc_results) == 1
    assert desc_results[0]["id"] == 2

    # Test searching with empty query
    assert search_tasks(sample_tasks, "") == []

    # Test searching with None query
    assert search_tasks(sample_tasks, None) == []

    # Test searching with non-matching query
    assert search_tasks(sample_tasks, "NonExistent") == []

    # Test searching with partial match
    partial_results = search_tasks(sample_tasks, "Test")
    assert len(partial_results) == 3

    # Test searching with case sensitivity
    case_results = search_tasks(sample_tasks, "TEST TASK 1")
    assert len(case_results) == 1
    assert case_results[0]["id"] == 1


def test_get_overdue_tasks(sample_tasks):
    # Test getting overdue tasks
    overdue_tasks = get_overdue_tasks(sample_tasks)
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["id"] == 1

    # Test with tasks due today
    today_tasks = [
        {
            "id": 1,
            "title": "Today's Task",
            "completed": False,
            "due_date": datetime.now().strftime("%Y-%m-%d"),
        }
    ]
    assert len(get_overdue_tasks(today_tasks)) == 0

    # Test with tasks without due date
    no_due_date_tasks = [
        {
            "id": 1,
            "title": "No Due Date",
            "completed": False,
        }
    ]
    with pytest.raises(ValueError):
        get_overdue_tasks(no_due_date_tasks)

    # Test with invalid date format
    invalid_date_tasks = [
        {
            "id": 1,
            "title": "Invalid Date",
            "completed": False,
            "due_date": "invalid-date",
        }
    ]
    with pytest.raises(ValueError):
        get_overdue_tasks(invalid_date_tasks)
