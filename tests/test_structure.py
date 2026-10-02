"""Structural checks on the shipped commands, specs, context and templates."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = sorted((ROOT / "commands").glob("*.md"))
# Files a command may Read at runtime, from inside some other project repo.
POINTER_FILES = COMMANDS + sorted(
    p for d in ("specs", "context", "templates") for p in (ROOT / d).glob("*.md")
)

PREFIX = "~/.claude/claude-dev-loop/"
POINTER = re.compile(re.escape(PREFIX) + r"([\w./-]+?\.(?:md|sh))")
HOME_PATH = re.compile(r"~/(?!\.claude/)\S+")


def rel(path):
    return path.relative_to(ROOT)


def test_four_loop_commands_shipped():
    assert [p.stem for p in COMMANDS] == [
        "begin-dev",
        "close-dev",
        "init-dev",
        "review-dev",
    ]


@pytest.mark.parametrize("path", COMMANDS, ids=lambda p: p.name)
def test_command_frontmatter_has_description(path):
    text = path.read_text()
    assert text.startswith("---\n"), "no YAML frontmatter"
    frontmatter = text.split("---\n", 2)[1]
    assert re.search(r"^description: \S", frontmatter, re.M)


@pytest.mark.parametrize("path", POINTER_FILES, ids=lambda p: str(rel(p)))
def test_toolkit_pointers_resolve(path):
    """Every ~/.claude/claude-dev-loop/<path> must exist at <path> in this repo.

    install.sh links the clone to ~/.claude/claude-dev-loop, so this is the path
    the model actually Reads at runtime.
    """
    missing = [m for m in POINTER.findall(path.read_text()) if not (ROOT / m).is_file()]
    assert not missing


@pytest.mark.parametrize("path", POINTER_FILES, ids=lambda p: str(rel(p)))
def test_no_home_paths_outside_claude_dir(path):
    assert not HOME_PATH.findall(path.read_text())


FLAG = re.compile(r"--[a-z][a-z-]*")


def _frontmatter_field(text, field):
    match = re.search(rf"^{field}:(.*)$", text.split("\n---", 1)[0], re.M)
    return match.group(1) if match else ""


def _arguments_table(text):
    section = re.search(r"^## Arguments\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    rows = [line for line in section.group(1).splitlines() if line.startswith("|")]
    return " ".join(row.split("|")[1] for row in rows)


@pytest.mark.parametrize("path", COMMANDS, ids=lambda p: p.name)
def test_argument_hint_matches_arguments_table(path):
    text = path.read_text()
    hint = set(FLAG.findall(_frontmatter_field(text, "argument-hint")))
    table = set(FLAG.findall(_arguments_table(text)))
    assert hint == table, f"hint only: {hint - table}; table only: {table - hint}"


def test_plan_template_has_decisions_table():
    text = (ROOT / "templates/development-plan.md").read_text()
    assert "## Decisions" in text
    assert "| Decision | Chosen | Rejected | Why |" in text


def _broken_tables(text):
    """Rows that continue a table after a non-table line instead of starting a new one."""
    lines, broken, fenced, prev = text.splitlines(), [], False, ""
    for n, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
        if fenced or not line.strip():
            continue
        is_row = line.startswith("|")
        next_line = lines[n + 1] if n + 1 < len(lines) else ""
        starts_table = re.match(r"^\|[\s:|-]+\|$", next_line.strip())
        if is_row and not prev.startswith("|") and not starts_table:
            broken.append(n + 1)
        prev = line
    return broken


@pytest.mark.parametrize("path", POINTER_FILES, ids=lambda p: p.name)
def test_no_table_interrupted_by_prose(path):
    assert _broken_tables(path.read_text()) == []
