## Prepare environment

### Install the package

```bash
    poetry install
```

### Install the dev dependencies

```bash
    poetry install --dev
```

### Run the tests

```bash
    poetry run pytest tests/
```

### Install pre-commits

```bash
    poetry run pre-commit install
```

## Commit Message Guidelines

To maintain consistency and clarity in the commit history, we have defined a standard structure for commit messages.
Please use the following types:

### 1. `feat:` (Feature)

Used for introducing new features or major changes to the application.

- Example: `feat: Add filter search functionality`

### 2. `fix:` (Fix)

Used for bug fixes or improvements that address undesirable behavior.

- Example: `fix: Fix mobile UI display issue`

### 3. `refactor:` (Refactor)

Used for code improvements that do not add new features or fix bugs, but clean up, enhance readability, or improve
performance.

- Example: `refactor: Optimize error handling in validation module`

---

## Pull Request Guidelines

### 1. Squash Commits

When merging a Pull Request (PR), **please squash all commits** into a single commit. This helps to keep the commit
history clean and manageable.

### 2. Use the PR Title as the Commit Message

The commit message should be the title of the Pull Request. This ensures that the history reflects the purpose of the PR
clearly.

---

## Example Commit Messages

- **feat:** Add contact page
- **fix:** Fix bug with product display in the list
- **refactor:** Refactor user controller code organization
