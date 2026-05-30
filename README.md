# ⬡ Script Runner

A lightweight web-based process manager that lets you run, monitor, stop, restart, and kill scripts from your browser — no terminal babysitting required.

---

## Features

- **Run any command** — shell scripts, Python files, binaries, one-liners
- **Live output** — stdout and stderr streamed to the browser in real time
- **Process controls** — Stop (graceful), Restart, and Kill (force)
- **Status indicator** — live badge shows Running / Stopped / Killed with a pulsing dot
- **Uptime counter** — tracks how long the current process has been running
- **Reconnect on refresh** — if you reload the page mid-run, the UI reattaches to the live process
- **Color-coded terminal** — stdout, stderr, system messages, and exit codes each have distinct colors

---

## Requirements

- Python 3.7+
- Flask

---

## Installation

```bash
pip install flask
```

---

## Usage

### Start the server

```bash
python3 script_runner.py
```

Then open **http://localhost:5000** in your browser.

To use a different port:

```bash
PORT=8080 python3 script_runner.py
```

### Run a script

1. Type any command into the input field at the top
2. Click **▶ Run**

**Examples:**

```
python3 my_script.py
bash ./deploy.sh
ping google.com
ls -la /var/log
```

### Controls

| Button | Action |
|--------|--------|
| **▶ Run** | Launches the entered command as a subprocess |
| **■ Stop** | Sends `SIGTERM` to the process group (graceful shutdown) |
| **↺ Restart** | Stops the current process and relaunches the same command |
| **✕ Kill** | Sends `SIGKILL` to the process group (immediate termination) |
| **⌫ Clear** | Clears the terminal output display |

---

## How it works

- The script is launched via `subprocess.Popen` with `shell=True`, so it runs inside a process group
- stdout and stderr are read on background threads and pushed to a queue
- The browser connects to `/stream` using **Server-Sent Events (SSE)** for live output
- Stop/Kill target the entire process group (`os.killpg`), so child processes are also terminated
- State (status, script path, start time) is held in memory — it resets when the server restarts

---

## Project Structure

```
script_runner.py   # Single-file app — server + UI in one
```

Everything is self-contained in one file. The HTML/CSS/JS frontend is embedded as a Python string and served via Flask's `render_template_string`.

---

## Notes

- **No authentication** — this tool is intended for local or trusted-network use only. Do not expose it to the public internet.
- **One process at a time** — only one script can run at a time. Start a new one after the current process stops.
- **Shell expansion** — because `shell=True` is used, commands like `ls *.py` and `$HOME` work as expected.
- Output history is kept in memory (last 200 lines) and is lost when the server restarts.

---

## License

MIT — do whatever you want with it.
