# rt — Remote Terminal

Access your Mac's terminal from your phone. Run `rt`, scan the QR code, and you're in — with a mobile-friendly web UI featuring virtual keyboard buttons, clipboard sync, and real-time session mirroring.

## How it works

`rt` spins up a local terminal session using **tmux**, exposes it through **ttyd** (web-based terminal), routes traffic through **Caddy** (reverse proxy with auth token), and tunnels it to the internet via **ngrok** or **cloudflared**. A companion clipboard bridge server handles copy/paste between your phone and the terminal.

```
┌──────────┐     ┌──────────────┐     ┌───────┐     ┌────────────────┐
│  Phone   │────▶│ ngrok/       │────▶│ Caddy  │────▶│ ttyd (terminal)│
│ (browser)│     │ cloudflared  │     │ :port  │    ▶│ clipboard srv  │
└──────────┘     └──────────────┘     └───────┘     └────────────────┘
                                                           │
                                                     ┌─────┴─────┐
                                                     │   tmux    │
                                                     │  session  │
                                                     └───────────┘
```

Every session is protected by a random 128-bit token in the URL — no one can access your terminal without the full link.

## Install

There are two ways to install Remote Terminal. Choose whichever you prefer:

**Option 1 — Homebrew** (recommended, manages dependencies and updates automatically):

```bash
brew install rafgirao/remote-terminal/cli
```

**Option 2 — Script** (if you don't use Homebrew):

```bash
curl -fsSL https://raw.githubusercontent.com/rafgirao/remote-terminal/main/install.sh | bash
```

> On first run, `rt` will ask which tunnel provider you want to use (ngrok, cloudflared, or both) and install it automatically.

### Dependencies

| Dependency | Purpose |
|---|---|
| `tmux` | Terminal multiplexer — hosts the shared session |
| `ttyd` | Exposes tmux as a WebSocket-based terminal |
| `caddy` | Reverse proxy with token-based routing |
| `qrencode` | Generates QR code in the terminal |
| `python@3` | Runs the clipboard bridge server |

Installed automatically by both methods.

## Usage

### Start a session

```bash
rt
```

This will:
1. Create a tmux session named `remote`
2. Launch ttyd, Caddy, clipboard server, and a tunnel
3. Print the URL and QR code
4. Open a new terminal tab attached to the session

Scan the QR code with your phone and you're connected.

#### Named sessions

```bash
rt work
rt server
rt debug
```

Each name creates an independent session with its own tunnel, URL, and tmux session. You can run multiple sessions simultaneously.

### List sessions

```bash
rt list
# or
rt ls
```

Shows all active sessions and their status:

```
  remote (running)
  work (running)
  debug (stopped)
```

### Show QR code again

```bash
rt qr
rt qr work
```

Reprints the URL and QR code for an existing session. Useful if you cleared your terminal or need to scan again on a different device.

### Reconnect a session

```bash
rt reconnect
rt reconnect work
# or
rt rc
rt rc work
```

Relaunches all services (ttyd, Caddy, tunnel) for an existing tmux session without losing your terminal history. Use this when:
- The tunnel URL expired
- ngrok/cloudflared crashed
- You need a fresh URL

The tmux session stays alive — only the networking layer restarts.

### Stop a session

```bash
rt stop
rt stop work
```

Kills all processes (ttyd, Caddy, tunnel, clipboard server) and cleans up the session.

#### Stop all sessions

```bash
rt stop --all
```

### Setup (manual)

```bash
rt setup
```

Re-run the tunnel provider setup at any time (e.g. to add cloudflared after initially choosing ngrok). Also configures `~/.tmux.conf`.

### Version

```bash
rt version
```

### Help

```bash
rt help
```

## Auto-update

When you run `rt`, it checks for new versions once per day. If an update is available, you'll see:

```
  ╭─────────────────────────────────────────────╮
  │  Update available: v0.1.0 → v0.2.0          │
  ╰─────────────────────────────────────────────╯

  Update now? [Y/n]
```

Press **Enter** or **Y** to update automatically via `brew upgrade`. Press **N** to skip.

## Mobile Web UI

The phone interface includes:

### Virtual keyboard

Two rows of buttons for keys that are hard to type on a phone:

| Button | Action |
|---|---|
| `Esc` | Send Escape |
| `Tab` | Send Tab |
| `↑` `↓` `←` `→` | Arrow keys |
| `Ctrl` | Toggle Ctrl modifier (combines with next key) |
| `^C` | Send Ctrl+C (interrupt) |
| `^D` | Send Ctrl+D (EOF) |
| `^Z` | Send Ctrl+Z (suspend) |
| `^L` | Send Ctrl+L (clear screen) |
| `^A` | Send Ctrl+A (beginning of line) |
| `^E` | Send Ctrl+E (end of line) |
| `^R` | Send Ctrl+R (reverse search) |
| `^W` | Send Ctrl+W (delete word) |
| `\|` `/` `~` | Pipe, slash, tilde |

### Clipboard

- **Paste here + Enter**: Tap the input field, paste text from your phone's clipboard, hit Enter to send it to the terminal
- **Copy**: Captures the last 50 lines from the terminal pane and opens an overlay where you can copy to your phone's clipboard

## Session mirroring

When you start a session, `rt` automatically opens a new terminal tab on your Mac attached to the same tmux session. Everything you do on your phone appears on the Mac in real-time, and vice-versa.

For the best experience with multiple clients, add to your `~/.tmux.conf`:

```bash
set -g window-size largest
```

This prevents the terminal from shrinking to the smallest client's size.

## Configuration

### Ports

Ports are automatically assigned based on the session name hash to avoid collisions:

- Base port: `7680 + (hash % 500) * 3`
- `+0` → Clipboard server
- `+1` → ttyd
- `+2` → Caddy

### Tunnel priority

`rt` tries **ngrok** first (up to 15 seconds). If ngrok fails or isn't installed, it falls back to **cloudflared** (up to 30 seconds).

### Security

- Each session gets a unique 128-bit random token
- The URL format is `https://<tunnel-domain>/<token>/`
- Caddy rejects any request without a valid token (returns 403)
- Tokens are regenerated on every `rt start` and `rt reconnect`

## Troubleshooting

### "Failed to get tunnel URL"

- Make sure `ngrok` or `cloudflared` is installed
- If using ngrok, make sure you've authenticated: `ngrok config add-authtoken <token>`
- Check the tunnel log: `cat /tmp/remote-terminal-<name>/tunnel.log`

### Session won't start

- Check if ports are in use: `lsof -i :<port>`
- Kill stale sessions: `rt stop --all`
- Check for leftover tmux sessions: `tmux list-sessions`

### Dots/artifacts on the Mac terminal tab

Add to `~/.tmux.conf`:

```bash
set -g window-size largest
```

Then restart tmux: `tmux kill-server` (this will close all tmux sessions).

## Uninstall

### Homebrew

```bash
rt stop --all
brew uninstall cli && brew untap rafgirao/remote-terminal
```

### Script

```bash
rt stop --all
curl -fsSL https://raw.githubusercontent.com/rafgirao/remote-terminal/main/uninstall.sh | bash
```

## License

MIT
