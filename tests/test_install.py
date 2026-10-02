"""install.sh links exactly what it says it links, and --uninstall undoes it."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = sorted(p.name for p in (ROOT / "commands").glob("*.md"))

pytestmark = pytest.mark.integration


def install(home, *args, path=None):
    env = {**os.environ, "HOME": str(home)}
    env["PATH"] = path or f"{home}/.local/bin{os.pathsep}{os.environ['PATH']}"
    return subprocess.run(
        ["bash", str(ROOT / "install.sh"), *args],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def home(tmp_path):
    """A HOME with unrelated files already in the dirs install.sh touches."""
    (tmp_path / ".claude/commands").mkdir(parents=True)
    (tmp_path / ".claude/commands/mine.md").write_text("keep\n")
    (tmp_path / ".local/bin").mkdir(parents=True)
    (tmp_path / ".local/bin/other-tool").write_text("keep\n")
    return tmp_path


def expected_links(home):
    links = {
        home / ".claude/commands" / name: ROOT / "commands" / name for name in COMMANDS
    }
    links[home / ".local/bin/setup-docs"] = ROOT / "scripts/setup-docs.sh"
    links[home / ".claude/claude-dev-loop"] = ROOT
    return links


def test_install_creates_the_links(home):
    install(home)
    for link, target in expected_links(home).items():
        assert link.is_symlink(), link
        assert Path(os.readlink(link)) == target


def test_toolkit_link_resolves_context_files(home):
    install(home)
    assert (home / ".claude/claude-dev-loop/context/context-docs.md").is_file()


def test_install_is_idempotent(home):
    install(home)
    install(home)
    assert (home / ".claude/claude-dev-loop").resolve() == ROOT
    assert not (ROOT / ROOT.name).exists(), "ln -s into the linked dir"


def test_install_never_replaces_a_regular_file(home):
    clash = home / ".claude/commands" / COMMANDS[0]
    clash.write_text("user's own\n")
    result = install(home)
    assert clash.read_text() == "user's own\n"
    assert "skip" in result.stderr


def test_uninstall_removes_exactly_the_links(home):
    install(home)
    install(home, "--uninstall")
    for link in expected_links(home):
        assert not link.exists() and not link.is_symlink(), link
    assert (home / ".claude/commands/mine.md").read_text() == "keep\n"
    assert (home / ".local/bin/other-tool").read_text() == "keep\n"


def test_uninstall_leaves_links_pointing_elsewhere(home, tmp_path):
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text("x\n")
    link = home / ".claude/commands" / COMMANDS[0]
    link.symlink_to(elsewhere)
    install(home, "--uninstall")
    assert link.is_symlink()


def test_install_skips_a_link_pointing_elsewhere(home, tmp_path):
    elsewhere = tmp_path / "other-clone.md"
    elsewhere.write_text("x\n")
    link = home / ".claude/commands" / COMMANDS[0]
    link.symlink_to(elsewhere)
    result = install(home)
    assert Path(os.readlink(link)) == elsewhere
    assert "skip" in result.stderr and str(link) in result.stderr


def test_install_warns_when_bin_dir_not_on_path(home):
    result = install(home, path="/usr/bin:/bin")
    assert "not on PATH" in result.stderr


def test_install_quiet_about_path_when_bin_dir_is_on_path(home):
    assert "not on PATH" not in install(home).stderr
