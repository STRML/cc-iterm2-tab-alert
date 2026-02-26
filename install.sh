#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$HOME/.claude/hooks"
ITERM2_SCRIPTS="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
SETTINGS="$HOME/.claude/settings.json"

echo "Installing Claude Code iTerm2 tab alert..."

# 1. Copy hook scripts
mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/hooks/iterm2-permission-alert.sh" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/hooks/iterm2-tab-reset.sh" "$HOOKS_DIR/"
echo "  Copied hooks to $HOOKS_DIR/"

# 2. Copy iTerm2 Python script
mkdir -p "$ITERM2_SCRIPTS"
cp "$SCRIPT_DIR/scripts/claude_tab_reset.py" "$ITERM2_SCRIPTS/"
echo "  Copied focus-reset script to $ITERM2_SCRIPTS/"

# 3. Merge hooks into settings.json
if ! command -v jq &>/dev/null; then
    echo ""
    echo "  jq is not installed. Install it (brew install jq) or manually add"
    echo "  the hooks config from hooks.json to your ~/.claude/settings.json."
    echo ""
    echo "  See README.md for the required hooks configuration."
    exit 0
fi

if [ ! -f "$SETTINGS" ]; then
    echo '{}' > "$SETTINGS"
fi

# Build the hooks config and merge
HOOKS_CONFIG=$(cat <<'JSON'
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-permission-alert.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-tab-reset.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-tab-reset.sh"
          }
        ]
      }
    ]
  }
}
JSON
)

# Deep-merge hooks into existing settings (preserves existing hooks)
MERGED=$(jq -s '
  def merge_hooks:
    .[0].hooks as $existing |
    .[1].hooks as $new |
    reduce ($new | keys[]) as $key (
      $existing;
      if .[$key] then
        .[$key] = .[$key] + $new[$key]
      else
        .[$key] = $new[$key]
      end
    );
  .[0] * { hooks: ([ .[0], .[1] ] | merge_hooks) }
' "$SETTINGS" <(echo "$HOOKS_CONFIG"))

echo "$MERGED" > "$SETTINGS"
echo "  Merged hooks into $SETTINGS"

echo ""
echo "Done! Next steps:"
echo "  1. In iTerm2: Scripts > Manage > Install Python Runtime (if not already done)"
echo "  2. In iTerm2: Scripts > claude_tab_reset (to start without restarting iTerm2)"
echo "  3. Run /hooks in Claude Code to reload hooks"
