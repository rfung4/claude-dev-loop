#!/bin/bash
# setup-docs.sh
# Creates standardized documentation structure with INDEX.md navigation files
#
# Usage:
#   setup-docs.sh [project-dir] [project-name] [--fresh]
#
# Options:
#   --fresh    Archive existing docs/ to docs/.archive/<timestamp>-XXXX, then
#              start clean. Aborts, deleting nothing, if any move fails.
#   -h, --help Show this help
#
# Safe to re-run: the default run only creates files that are missing.
# Existing files - INDEX.md hubs included - are never overwritten or archived.

set -e

usage() {
    sed -n '5,14p' "$0" | sed 's/^# \{0,1\}//'
}

# Parse arguments
FRESH=false
POSITIONAL=()

for arg in "$@"; do
    case $arg in
        --fresh)
            FRESH=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "setup-docs: unknown option: $arg" >&2
            usage >&2
            exit 2
            ;;
        *)
            POSITIONAL+=("$arg")
            ;;
    esac
done

if [ "${#POSITIONAL[@]}" -gt 2 ]; then
    echo "setup-docs: too many arguments: ${POSITIONAL[*]}" >&2
    usage >&2
    exit 2
fi

# First positional: project dir (default: .)
PROJECT_DIR="${POSITIONAL[0]:-.}"
# Second positional: project name (default: dirname)
PROJECT_NAME="${POSITIONAL[1]:-}"

# Default project name from directory
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="$(basename "$(cd "$PROJECT_DIR" && pwd)")"
fi

# Doc skeletons live in templates/docs/ beside this script's directory. Follow
# symlinks (setup-docs on PATH is one) by hand - macOS has no readlink -f.
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
    dir="$(cd -P "$(dirname "$src")" && pwd)"
    src="$(readlink "$src")"
    case $src in /*) ;; *) src="$dir/$src" ;; esac
done
SKELETON="$(cd -P "$(dirname "$src")/../templates/docs" && pwd)"

cd "$PROJECT_DIR"

# Write stdin to $1 only if $1 does not exist yet. Existing files are kept
# byte-identical - they hold the user's own content and links.
write_new() {
    if [ -e "$1" ]; then
        cat > /dev/null
        echo "ℹ️  $1 exists - kept"
    else
        cat > "$1"
        echo "✅ $1"
    fi
}

# --fresh: move everything in docs/ (except .archive) into a unique archive dir.
# Nothing is deleted - a move that fails aborts the run with the rest in place.
if [ "$FRESH" = true ] && [ -d docs ]; then
    mkdir -p docs/.archive
    ARCHIVE_DIR=$(mktemp -d "docs/.archive/$(date +%Y%m%d_%H%M%S)-XXXX")
    echo "📦 Archiving existing docs to $ARCHIVE_DIR..."
    moved=0
    while IFS= read -r -d '' item; do
        if ! mv "$item" "$ARCHIVE_DIR/"; then
            echo "✗ Could not archive $item - aborting. Nothing was deleted;" >&2
            echo "  items already moved are in $ARCHIVE_DIR" >&2
            exit 1
        fi
        moved=$((moved + 1))
    done < <(find docs -mindepth 1 -maxdepth 1 ! -name .archive -print0)
    echo "✅ Archived $moved items"
fi

echo "📚 Setting up documentation for: $PROJECT_NAME"

# Create directory structure (SIMPLIFIED CONVENTION)
mkdir -p docs/{context,schema,api,architecture,ops,notes,research,development,report,.archive}

# notes/ is tracked: .keep lets git hold the empty dir. The other four are
# gitignored, so their .keep files only mark the dirs locally and never reach git.
touch docs/notes/.keep
touch docs/research/.keep
touch docs/development/.keep
touch docs/report/.keep
touch docs/.archive/.keep

# ============================================================================
# DOC SKELETONS - copied from templates/docs/, missing files only
# ============================================================================
TODAY=$(date +%Y-%m-%d)
while IFS= read -r -d '' tpl; do
    rel="${tpl#"$SKELETON"/}"
    if [ "$rel" = INDEX.md ] && [ ! -e docs/INDEX.md ]; then
        # the one templated file: project name and creation date
        { printf '# %s Documentation\n' "$PROJECT_NAME"
          tail -n +2 "$tpl" | sed "s/{{DATE}}/$TODAY/"; } > docs/INDEX.md
        echo "✅ docs/INDEX.md"
    else
        write_new "docs/$rel" < "$tpl"
    fi
done < <(find "$SKELETON" -type f -name '*.md' -print0)

# Add gitignore entries
add_ignore() {
    if ! grep -qF "$1" .gitignore; then
        printf '\n# %s\n%s\n' "$2" "$1" >> .gitignore
        echo "ℹ️  Added $1 to .gitignore"
    fi
}

if [ -f .gitignore ]; then
    add_ignore docs/research/ "Messy exploration (not tracked)"
    add_ignore docs/development/ "Local feature tracking (not tracked)"
    add_ignore docs/report/ "Completion reports (not tracked)"
    add_ignore docs/.archive/ "Auto-archived docs (not tracked)"
else
    cat > .gitignore << 'GITIGNORE'
# Messy exploration (not tracked)
docs/research/

# Local feature tracking (not tracked)
docs/development/

# Completion reports (not tracked)
docs/report/

# Auto-archived docs (not tracked)
docs/.archive/
GITIGNORE
    echo "ℹ️  Created .gitignore with docs/ entries"
fi

# ============================================================================
# Install pre-commit guard for local-only docs
# ============================================================================
# .gitignore only suppresses UNTRACKED files. Once a local-only doc is tracked
# (committed before the ignore rule, or added with -f), the rule is inert
# forever. This hook stops the set from growing.
#
# Deliberately installed to .git/hooks/ (local, never committed): the docs
# convention is yours, and should not gate other contributors on shared repos.
# Self-contained by design - no reference to the toolkit clone, so moving the clone
# cannot silently break it.
if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
    HOOKS_DIR=$(git config core.hooksPath 2>/dev/null || true)
    [ -z "$HOOKS_DIR" ] && HOOKS_DIR=$(git rev-parse --git-path hooks 2>/dev/null || echo ".git/hooks")

    if [ -e "$HOOKS_DIR/pre-commit" ]; then
        echo "ℹ️  $HOOKS_DIR/pre-commit exists - not overwritten"
        echo "    (add the local-docs guard manually)"
    else
        mkdir -p "$HOOKS_DIR"
        cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/usr/bin/env bash
# Block NEWLY ADDED local-only docs from entering git.
#
# docs/{research,development,report,.archive}/ are local exploration and archive
# per the docs convention - they are gitignored, but .gitignore does nothing for
# files that are already tracked. This guards additions only (--diff-filter=A),
# so editing docs already in history keeps working.
#
# Installed by setup-docs.sh. Bypass: git commit --no-verify

added=$(git diff --cached --name-only --diff-filter=A \
        | grep -E '^docs/(research|development|report|\.archive)/' \
        | grep -v '/\.keep$') || exit 0
[ -z "$added" ] && exit 0

echo "✗ Local-only docs staged for addition:"
printf '%s\n' "$added" | sed 's/^/    /'
echo ""
echo "  These directories are local-only by convention (see docs/INDEX.md)."
echo "  Unstage:   git reset HEAD <file>"
echo "  Override:  git commit --no-verify"
exit 1
HOOK
        chmod +x "$HOOKS_DIR/pre-commit"
        echo "✅ Installed local-docs guard → $HOOKS_DIR/pre-commit"
    fi
fi

# ============================================================================
# Update CLAUDE.md if exists
# ============================================================================
if [ -f CLAUDE.md ]; then
    if ! grep -q "## Documentation" CLAUDE.md; then
        cat >> CLAUDE.md << 'EOF'

## Documentation

**Start here:** docs/INDEX.md (plain paths - read what the task needs; nothing here loads up front)

**Quick context:**
- docs/context/overview.md - What this project does
- docs/context/domain.md - Key terminology
- docs/context/stack.md - Tech stack

**When working on:**
- Database/models → docs/schema/
- API endpoints → docs/api/
- Architecture → docs/architecture/
- Processes/runbooks → docs/ops/
- Utility scripts → docs/ops/SCRIPTS.md
- Current features → docs/development/ (local)
- Research/exploration → docs/research/ (local)
- Tribal knowledge → docs/notes/
EOF
        echo "✅ Updated CLAUDE.md"
    else
        echo "ℹ️  CLAUDE.md already has Documentation section"
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Documentation structure created!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Structure:"
echo "  docs/"
echo "  ├── INDEX.md              ← Start here"
echo "  ├── context/              ← AI context loading"
echo "  ├── schema/               ← Database documentation"
echo "  ├── api/                  ← API conventions"
echo "  ├── architecture/         ← System design"
echo "  ├── ops/                  ← Processes + Runbooks + Scripts"
echo "  │   └── SCRIPTS.md        ← Utility scripts reference"
echo "  ├── notes/                ← Tribal knowledge (gotchas)"
echo "  ├── research/             ← Exploration (gitignored)"
echo "  │   └── INDEX.md          ← Tracks all research"
echo "  ├── development/          ← Active work (gitignored)"
echo "  │   └── INDEX.md          ← Tracks all features"
echo "  ├── report/               ← Completed work summaries (gitignored)"
echo "  └── .archive/             ← Auto-archived docs (gitignored)"
echo ""
echo "INDEX.md hubs: docs/, schema/, api/, ops/, research/, development/"
echo ""
echo "Next steps:"
echo "  1. Edit docs/INDEX.md - Add project description"
echo "  2. Edit docs/context/overview.md - Describe the project"
echo "  3. Edit docs/context/domain.md - Add terminology"
echo "  4. Edit docs/schema/INDEX.md - Add ER diagram"
echo "  5. Commit: git add docs/ && git commit -m 'Add documentation structure'"
echo ""
