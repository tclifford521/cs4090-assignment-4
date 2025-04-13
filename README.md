## Project Structure

```
todo_app/
│
├── app.py                  # Streamlit UI
├── tasks.py                # Core logic: add, delete, update, etc.
├── test/
│   ├── test_basic.py       # Basic pytest tests
│   ├── test_advanced.py    # Fixtures and parameterized tests
│   ├── test_tdd.py         # TDD-driven example
│   ├── test_property.py    # Property-based tests using hypothesis
│   └── features/           # BDD folder for behave
│       ├── add_task.feature
│       └── steps/
│           └── test_add_steps.py
├── requirements.txt
└── README.md
```

### Highlights

- **`app.py`** – Streamlit UI to interact with the to-do list.
- **`tasks.py`** – Contains the core logic for managing tasks.
- **`test/`** – Includes various test styles:
  - `test_basic.py`: Unit tests with `pytest`
  - `test_advanced.py`: Tests using fixtures & parameterization
  - `test_tdd.py`: Test-driven development example
  - `test_property.py`: Property-based testing with `hypothesis`
  - `features/`: BDD tests using `behave` or `pytest-bdd`, including feature files and steps
