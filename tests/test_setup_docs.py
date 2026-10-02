"""setup-docs.sh produces the docs/ layout the loop commands expect."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/setup-docs.sh"
GITIGNORE_LINES = [
    "docs/research/",
    "docs/development/",
    "docs/report/",
    "docs/.archive/",
]

pytestmark = pytest.mark.integration

# Keep the caller's git config (a global core.hooksPath, signing) out of the
# temp repos: the script installs its hook wherever git says hooks live.
GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def run(*args, cwd=None):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=GIT_ENV,
        cwd=cwd,
    )


def setup_docs(project, *flags):
    result = run(str(project), "Name", *flags)
    assert result.returncode == 0, result.stderr
    return result


def git(project, *args):
    return subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )


@pytest.fixture
def project(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


def test_creates_docs_layout(project):
    setup_docs(project)
    for path in [
        "docs/INDEX.md",
        "docs/schema/INDEX.md",
        "docs/api/INDEX.md",
        "docs/ops/INDEX.md",
    ]:
        assert (project / path).is_file(), path
    for path in ["docs/development", "docs/research", "docs/report"]:
        assert (project / path).is_dir(), path


def test_gitignores_the_four_local_dirs(project):
    setup_docs(project)
    lines = (project / ".gitignore").read_text().splitlines()
    for entry in GITIGNORE_LINES:
        assert entry in lines


def test_rerun_does_not_duplicate_gitignore_lines(project):
    setup_docs(project)
    setup_docs(project)
    lines = (project / ".gitignore").read_text().splitlines()
    for entry in GITIGNORE_LINES:
        assert lines.count(entry) == 1, entry


def test_appends_to_existing_gitignore(project):
    (project / ".gitignore").write_text("node_modules/\n")
    setup_docs(project)
    lines = (project / ".gitignore").read_text().splitlines()
    assert lines[0] == "node_modules/"
    for entry in GITIGNORE_LINES:
        assert entry in lines


def test_installs_local_docs_guard_hook(project):
    setup_docs(project)
    hook = project / ".git/hooks/pre-commit"
    assert hook.is_file()
    assert "local-only docs" in hook.read_text()


def test_rerun_keeps_edited_files_byte_identical(project):
    setup_docs(project)
    index = project / "docs/INDEX.md"
    content = project / "docs/schema/users.md"
    index.write_text("# Mine\n\n- [users](schema/users.md)\n")
    content.write_text("users table\n")
    before = {p: p.read_bytes() for p in (index, content)}
    setup_docs(project)
    assert {p: p.read_bytes() for p in (index, content)} == before
    assert list((project / "docs/.archive").iterdir()) == [
        project / "docs/.archive/.keep"
    ]


def test_fresh_archives_old_files(project):
    setup_docs(project)
    (project / "docs/INDEX.md").write_text("old index\n")
    (project / "docs/notes/gotcha.md").write_text("gotcha\n")
    setup_docs(project, "--fresh")
    archives = [p for p in (project / "docs/.archive").iterdir() if p.is_dir()]
    assert len(archives) == 1
    assert (archives[0] / "INDEX.md").read_text() == "old index\n"
    assert (archives[0] / "notes/gotcha.md").read_text() == "gotcha\n"
    assert not (project / "docs/notes/gotcha.md").exists()
    assert "old index" not in (project / "docs/INDEX.md").read_text()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_fresh_aborts_with_files_intact_when_a_move_fails(project):
    docs = project / "docs"
    (docs / ".archive").mkdir(parents=True)
    (docs / "INDEX.md").write_text("keep me\n")
    docs.chmod(0o555)  # entries cannot be moved out of docs/
    try:
        result = run(str(project), "Name", "--fresh")
    finally:
        docs.chmod(0o755)
    assert result.returncode != 0
    assert (docs / "INDEX.md").read_text() == "keep me\n"


def test_hook_blocks_force_added_local_doc(project):
    setup_docs(project)
    (project / "docs/development/x.md").write_text("wip\n")
    git(project, "add", "-f", "docs/development/x.md")
    result = git(project, "commit", "-q", "-m", "wip")
    assert result.returncode != 0
    assert "docs/development/x.md" in result.stdout + result.stderr
    assert git(project, "rev-parse", "HEAD").returncode != 0  # nothing committed


def test_existing_pre_commit_hook_is_untouched(project):
    hook = project / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 0\n")
    setup_docs(project)
    assert hook.read_text() == "#!/bin/sh\nexit 0\n"


def test_claude_md_section_added_once_without_at_includes(project):
    (project / "CLAUDE.md").write_text("# Project\n")
    setup_docs(project)
    setup_docs(project)
    text = (project / "CLAUDE.md").read_text()
    assert text.count("## Documentation") == 1
    assert "@docs/" not in text


def test_help_exits_zero():
    result = run("--help")
    assert result.returncode == 0
    assert "--fresh" in result.stdout


def test_unknown_flag_exits_2_and_writes_nothing(tmp_path):
    result = run(str(tmp_path), "--frsh")
    assert result.returncode == 2
    assert not (tmp_path / "docs").exists()


def test_third_positional_exits_2(tmp_path):
    assert run(str(tmp_path), "Name", "extra").returncode == 2


def test_runs_through_a_symlink_like_install_creates(project, tmp_path):
    """install.sh links setup-docs onto PATH; the script must still find
    templates/docs/ next to its real location."""
    link = tmp_path / "bin/setup-docs"
    link.parent.mkdir()
    link.symlink_to(SCRIPT)
    result = subprocess.run(
        ["bash", str(link), str(project), "Name"],
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    assert result.returncode == 0, result.stderr
    assert (project / "docs/context/overview.md").is_file()
    assert (project / "docs/INDEX.md").read_text().startswith("# Name Documentation\n")
