# {FEATURE_NAME}: Commands

Quick reference for validation, testing, and common operations.

---

## Validation

Every task's `Verify:` line from SPEC.md, plus the end-to-end check. **Machine-owned:**
`/init-dev --refresh` replaces this block wholesale and `/begin-dev --next` appends to it.
Hand-written commands belong in the sections below the markers, where nothing rewrites them.

<!-- MERGE_START(VERIFY) -->
```bash
# Task 1: {task_name}
{verify command for task 1}

# Task 2: {task_name}
{verify command for task 2}

# End-to-end check
{e2e command}
```
<!-- MERGE_END(VERIFY) -->

---

## Testing

```bash
# Run tests for this feature
pytest tests/path/to/feature_tests.py -v

# Run with coverage
pytest tests/path/to/feature_tests.py --cov=src/path

# Specific test
pytest tests/path/to/test_file.py::test_name -v
```

---

## Quick Reference

```bash
# Local setup (if needed)
{setup commands}

# Debug/inspect
{useful debug commands}

# Cleanup/rollback (if needed)
{recovery commands}
```

---

<!--
Usage:
- Fill in commands as you discover them during development
- Keep commands copy-paste ready (no placeholders in final version)
- Remove sections you don't need
-->
