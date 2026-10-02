"""README stays truthful about the repo it describes."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
BASH_BLOCK = re.compile(r"```bash\n(.*?)```", re.S)


def test_relative_links_resolve():
    links = [t for t in LINK.findall(README) if not re.match(r"[a-z]+://", t)]
    assert links
    missing = [t for t in links if not (ROOT / t).exists()]
    assert not missing


def test_every_command_is_named():
    for cmd in (ROOT / "commands").glob("*.md"):
        assert f"/{cmd.stem}" in README, cmd.stem
        assert f"commands/{cmd.name}" in README, cmd.name


def test_shell_blocks_are_one_command_per_line():
    blocks = BASH_BLOCK.findall(README)
    assert blocks
    for block in blocks:
        for line in block.splitlines():
            assert not line.rstrip().endswith("\\"), line


def _before(first, second):
    assert first in README and second in README, (first, second)
    return README.index(first) < README.index(second)


def test_comparison_table_comes_before_install():
    assert _before("Spec Kit", "## Install")
    assert _before("plan mode", "## Install")


def test_design_rules_come_before_transcripts():
    assert _before("## Design rules", "## What it looks like")


def test_index_count_is_not_four_hubs():
    assert "four INDEX hubs" not in README


def test_author_line_without_contact():
    line = re.search(r"^\*\*Author:\*\* (.+)$", README, re.M)
    assert line
    assert not re.search(r"@|https?://", line.group(1))


def test_no_at_include_in_shell_blocks():
    for block in BASH_BLOCK.findall(README):
        assert "@" not in block, block
