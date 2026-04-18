# Copilot Instructions: Best Practices & Conventions

Welcome to the Resume Bridge AI codebase! This file provides best practices and conventions for GitHub Copilot and all contributors to follow for consistent, high-quality software development.

## General Coding Best Practices

- Write clear, concise, and self-documenting code.
- Use meaningful variable, function, and class names.
- Keep functions and classes small and focused on a single responsibility.
- Write docstrings for all public functions, classes, and modules.
- Use type hints and static typing where possible (e.g., Python type annotations).
- Avoid code duplication; refactor common logic into reusable functions or modules.
- Handle exceptions gracefully and log errors with context.
- Use version control (git) for all changes; commit early and often with clear messages.
- Write unit and integration tests for new features and bug fixes.
- Follow the DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles.
- Prefer composition over inheritance unless inheritance is clearly justified.
- Use code linters and formatters (e.g., black, flake8, isort for Python).
- Document any non-obvious design decisions in code comments or documentation files.

## Python-Specific Practices

- Follow PEP 8 for code style and formatting.
- Use virtual environments for dependency management.
- Pin dependencies in `requirements.txt` and update regularly.
- Use environment variables for secrets and configuration (never hardcode secrets).
- Structure code into logical modules and packages (e.g., `src/`).
- Prefer async code for I/O-bound operations.

## API & Web Development

- Validate all user input and sanitize data before processing.
- Use status codes and clear error messages in API responses.
- Separate business logic from API endpoint definitions.
- Use dependency injection for database and service access.
- Write OpenAPI/Swagger documentation for all endpoints (FastAPI does this automatically).

## Database Practices

- Use ORM models for database access (e.g., SQLAlchemy).
- Write migrations for schema changes if using a migration tool.
- Avoid raw SQL unless necessary; always sanitize inputs.
- Index database columns that are frequently queried.

## Testing & CI

- Place tests in a dedicated `tests/` directory.
- Use pytest or unittest for Python testing.
- Mock external services in tests.
- Run tests and linters in CI before merging code.
- Aim for high test coverage, but prioritize meaningful tests over 100% coverage.

## Documentation

- Keep README and AGENTS.md up to date with setup, usage, and architecture notes.
- Use inline comments for complex logic.
- Link to external docs instead of duplicating content.

## Collaboration

- Use feature branches and pull requests for all changes.
- Request code reviews and address feedback promptly.
- Write descriptive PR titles and summaries.
- Reference related issues in commits and PRs.

## Security

- Never commit secrets or credentials to the repository.
- Regularly update dependencies to patch vulnerabilities.
- Validate and sanitize all external input.

---

For project-specific conventions, see AGENTS.md. For questions, ask in code comments or open an issue.
