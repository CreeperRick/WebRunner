# ⚡ Script Runner

A lightweight, web-based process manager for running and monitoring Python scripts — all from your browser.

---

## Features

- **Multi-script management** — add as many scripts as you need, each tracked independently
- **Live status indicators** — pulsing green dot when running, red when stopped
- **Full process controls** — Start, Stop, Restart, and Kill per script
- **Live log output** — toggle an output panel to watch stdout/stderr in real time
- **Add via UI** — click `+` to register a new script by name, path, and optional arguments
- **Auto-refresh** — status polling every 2 seconds, no manual refresh needed

---

## Requirements

- Python 3.7+
- Flask

Install Flask if you don't have it:

```bash
pip install flask
```

---

## Usage

```bash
python3.11 script_runner.py
```

Then open your browser and go to:

```
http://localhost:5000
```

---

## Adding a Script

1. Click the **+ Add Script** button in the top right
2. Fill in the fields:
   - **Name** — a label for the script (e.g. `Data Processor`)
   - **Path** — absolute or relative path to your `.py` file (e.g. `/home/user/scripts/run.py`)
   - **Arguments** *(optional)* — any CLI arguments (e.g. `--port 8080 --debug`)
3. Click **Add Script** or press `Enter`

---

## Controls

| Button | Action |
|--------|--------|
| ▶ **Start** | Launches the script with `python3.11` |
| ■ **Stop** | Sends `SIGTERM` for a graceful shutdown (waits up to 5s, then force-kills) |
| ↻ **Restart** | Stops the running process and immediately starts it again |
| ✕ **Kill** | Sends `SIGKILL` — instant, forceful termination |
| ≡ **Logs** | Toggles the live output panel (stdout + stderr) |
| 🗑 **Remove** | Kills the process (if running) and removes it from the list |

---

## Notes

- All scripts are run with `python3.11`. Shell scripts or other runtimes are not currently supported out of the box.
- Log output is capped at 50,000 characters (oldest lines are dropped to keep memory usage low).
- Scripts and their state are stored in memory — restarting the server clears all entries.
- The server binds to `0.0.0.0:5000` by default, making it accessible on your local network. For local-only access, change `host="0.0.0.0"` to `host="127.0.0.1"` in the last line of `script_runner.py`.

---

## Project Structure

```
script_runner.py   # Single-file app — Flask backend + HTML/CSS/JS frontend
README.md
```

---

## License

MIT — do whatever you want with it.
