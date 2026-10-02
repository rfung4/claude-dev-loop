#!/usr/bin/env bash
# Link the dev loop into Claude Code.
#
#   ./install.sh               link commands, setup-docs and the toolkit root
#   ./install.sh --uninstall   remove exactly those links
#
# Three kinds of link, all symlinks back into this clone:
#   ~/.claude/commands/<cmd>.md  -> commands/<cmd>.md
#   ~/.local/bin/setup-docs      -> scripts/setup-docs.sh
#   ~/.claude/claude-dev-loop        -> this clone (every Read pointer in the
#                                   commands uses this prefix, so they resolve
#                                   from inside any project repo)
#
# Existing regular files and links that point elsewhere are never replaced or
# removed - install skips them with a warning.
set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
BIN_DIR="$HOME/.local/bin"
TOOLKIT_LINK="$HOME/.claude/claude-dev-loop"

# target -> link pairs
links=()
for cmd in "$ROOT"/commands/*.md; do
    links+=("$cmd" "$COMMANDS_DIR/$(basename "$cmd")")
done
links+=("$ROOT/scripts/setup-docs.sh" "$BIN_DIR/setup-docs")
links+=("$ROOT" "$TOOLKIT_LINK")

install() {
    mkdir -p "$COMMANDS_DIR" "$BIN_DIR"
    local i target link
    for ((i = 0; i < ${#links[@]}; i += 2)); do
        target="${links[i]}"
        link="${links[i + 1]}"
        if [[ -L "$link" && "$(readlink "$link")" != "$target" ]]; then
            echo "skip: $link already links to $(readlink "$link")" >&2
            continue
        fi
        if [[ -e "$link" && ! -L "$link" ]]; then
            echo "skip: $link exists and is not a symlink" >&2
            continue
        fi
        ln -sfn "$target" "$link"
        echo "linked: $link -> $target"
    done
    case ":$PATH:" in
        *":$BIN_DIR:"*) ;;
        *) echo "warning: $BIN_DIR is not on PATH - add it to run setup-docs" >&2 ;;
    esac
}

uninstall() {
    local i target link
    for ((i = 0; i < ${#links[@]}; i += 2)); do
        target="${links[i]}"
        link="${links[i + 1]}"
        if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
            rm "$link"
            echo "removed: $link"
        fi
    done
}

case "${1:-}" in
    "") install ;;
    --uninstall) uninstall ;;
    *)
        echo "usage: $0 [--uninstall]" >&2
        exit 2
        ;;
esac
