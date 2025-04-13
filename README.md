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
