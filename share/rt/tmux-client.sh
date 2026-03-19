#!/bin/bash
# Wrapper for ttyd: creates a grouped tmux session and cleans it up on exit
SESSION_NAME="$1"
CLIENT_SESSION="${SESSION_NAME}-ttyd-$$"

tmux new-session -d -t "$SESSION_NAME" -s "$CLIENT_SESSION" 2>/dev/null
tmux attach -t "$CLIENT_SESSION"

# Cleanup: kill the grouped session when the client disconnects
tmux kill-session -t "$CLIENT_SESSION" 2>/dev/null
