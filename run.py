#!/usr/bin/env python3
"""
Script Runner - A web-based script management and execution tool.
Run with: python script_runner.py
Then open http://localhost:5000 in your browser.
"""

import subprocess
import threading
import time
import os
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Store running processes
processes = {}
scripts = {}
script_id_counter = [0]
logs = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Script Runner</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0c10;
    --surface: #111418;
    --surface2: #181c22;
    --border: #232830;
    --accent: #00e5a0;
    --accent2: #0090ff;
    --danger: #ff4560;
    --warn: #ffb400;
    --text: #e8edf5;
    --muted: #5a6475;
    --running: #00e5a0;
    --stopped: #ff4560;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 20% 20%, rgba(0,229,160,0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(0,144,255,0.04) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  header {
    position: relative;
    z-index: 1;
    padding: 28px 40px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(10,12,16,0.8);
    backdrop-filter: blur(12px);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }

  h1 {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--text);
  }

  .header-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  main {
    position: relative;
    z-index: 1;
    padding: 40px;
    max-width: 1100px;
    margin: 0 auto;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
  }

  .section-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
  }

  .btn-add {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--accent);
    color: #000;
    border: none;
    padding: 10px 18px;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }

  .btn-add:hover {
    background: #00ffb3;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,229,160,0.3);
  }

  .btn-add .plus { font-size: 18px; line-height: 1; }

  .scripts-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .script-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    align-items: center;
    gap: 20px;
    transition: border-color 0.2s, box-shadow 0.2s;
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .script-card:hover {
    border-color: #2d3440;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  }

  .script-card.running {
    border-color: rgba(0,229,160,0.25);
    box-shadow: 0 0 0 1px rgba(0,229,160,0.1), 0 4px 24px rgba(0,229,160,0.05);
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--stopped);
    flex-shrink: 0;
    transition: background 0.3s;
    position: relative;
  }

  .status-dot.running {
    background: var(--running);
    box-shadow: 0 0 8px var(--running);
  }

  .status-dot.running::after {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    background: var(--running);
    opacity: 0.3;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.3; }
    50% { transform: scale(1.8); opacity: 0; }
  }

  .script-info { min-width: 0; }

  .script-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .script-path {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 20px;
    flex-shrink: 0;
  }

  .status-badge.running {
    background: rgba(0,229,160,0.12);
    color: var(--accent);
    border: 1px solid rgba(0,229,160,0.25);
  }

  .status-badge.stopped {
    background: rgba(255,69,96,0.1);
    color: var(--stopped);
    border: 1px solid rgba(255,69,96,0.2);
  }

  .controls {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }

  .btn {
    border: none;
    border-radius: 7px;
    padding: 8px 14px;
    font-family: 'Syne', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
    transform: none !important;
  }

  .btn-start { background: rgba(0,229,160,0.15); color: var(--accent); border: 1px solid rgba(0,229,160,0.3); }
  .btn-start:not(:disabled):hover { background: rgba(0,229,160,0.25); transform: translateY(-1px); }

  .btn-stop { background: rgba(255,180,0,0.12); color: var(--warn); border: 1px solid rgba(255,180,0,0.25); }
  .btn-stop:not(:disabled):hover { background: rgba(255,180,0,0.22); transform: translateY(-1px); }

  .btn-restart { background: rgba(0,144,255,0.12); color: var(--accent2); border: 1px solid rgba(0,144,255,0.25); }
  .btn-restart:not(:disabled):hover { background: rgba(0,144,255,0.22); transform: translateY(-1px); }

  .btn-kill { background: rgba(255,69,96,0.12); color: var(--danger); border: 1px solid rgba(255,69,96,0.25); }
  .btn-kill:not(:disabled):hover { background: rgba(255,69,96,0.22); transform: translateY(-1px); }

  .btn-remove { background: transparent; color: var(--muted); border: 1px solid transparent; padding: 8px 10px; }
  .btn-remove:hover { color: var(--danger); border-color: rgba(255,69,96,0.2); }

  .btn-logs { background: transparent; color: var(--muted); border: 1px solid transparent; padding: 8px 12px; font-size: 11px; }
  .btn-logs:hover { color: var(--text); }

  .log-panel {
    margin-top: 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    display: none;
    grid-column: 1 / -1;
  }

  .log-panel.open { display: block; }

  .log-header {
    padding: 8px 16px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .log-content {
    padding: 12px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #7a8899;
    max-height: 160px;
    overflow-y: auto;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .log-content::-webkit-scrollbar { width: 4px; }
  .log-content::-webkit-scrollbar-track { background: transparent; }
  .log-content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(6px);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
  }

  .modal-overlay.open { opacity: 1; pointer-events: all; }

  .modal {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    width: 460px;
    max-width: 90vw;
    transform: translateY(10px);
    transition: transform 0.2s;
    box-shadow: 0 24px 80px rgba(0,0,0,0.6);
  }

  .modal-overlay.open .modal { transform: translateY(0); }

  .modal h2 { font-size: 18px; font-weight: 800; margin-bottom: 24px; letter-spacing: -0.3px; }

  .field { margin-bottom: 18px; }

  .field label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
  }

  .field input {
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
  }

  .field input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(0,229,160,0.08);
  }

  .modal-actions { display: flex; gap: 10px; margin-top: 28px; }

  .btn-confirm {
    flex: 1;
    background: var(--accent);
    color: #000;
    border: none;
    padding: 13px;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-confirm:hover {
    background: #00ffb3;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,229,160,0.3);
  }

  .btn-cancel {
    flex: 1;
    background: var(--surface2);
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 13px;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cancel:hover { color: var(--text); border-color: #3a4050; }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
  }

  .empty-state .icon { font-size: 48px; margin-bottom: 16px; opacity: 0.4; }
  .empty-state p { font-size: 14px; line-height: 1.6; }

  .toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 20px;
    font-size: 13px;
    font-weight: 600;
    z-index: 200;
    transform: translateY(20px);
    opacity: 0;
    transition: all 0.3s;
    max-width: 300px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }

  .toast.show { transform: translateY(0); opacity: 1; }
  .toast.success { border-color: rgba(0,229,160,0.3); color: var(--accent); }
  .toast.error { border-color: rgba(255,69,96,0.3); color: var(--danger); }
  .toast.info { border-color: rgba(0,144,255,0.3); color: var(--accent2); }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">⚡</div>
    <h1>Script Runner</h1>
  </div>
  <div class="header-meta">Process Manager v1.0</div>
</header>

<main>
  <div class="section-header">
    <span class="section-title">Scripts</span>
    <button class="btn-add" onclick="openModal()">
      <span class="plus">+</span> Add Script
    </button>
  </div>

  <div class="scripts-grid" id="scriptsGrid">
    <div class="empty-state" id="emptyState">
      <div class="icon">📂</div>
      <p>No scripts added yet.<br>Click <strong>+ Add Script</strong> to get started.</p>
    </div>
  </div>
</main>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <h2>Add New Script</h2>
    <div class="field">
      <label>Script Name</label>
      <input type="text" id="scriptName" placeholder="e.g. Data Processor" />
    </div>
    <div class="field">
      <label>Script Path</label>
      <input type="text" id="scriptPath" placeholder="e.g. /home/user/scripts/run.py" />
    </div>
    <div class="field">
      <label>Arguments (optional)</label>
      <input type="text" id="scriptArgs" placeholder="e.g. --port 8080 --debug" />
    </div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal()">Cancel</button>
      <button class="btn-confirm" onclick="addScript()">Add Script</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
  let logVisible = {};

  function openModal() {
    document.getElementById('modalOverlay').classList.add('open');
    document.getElementById('scriptName').focus();
  }

  function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
    document.getElementById('scriptName').value = '';
    document.getElementById('scriptPath').value = '';
    document.getElementById('scriptArgs').value = '';
  }

  document.getElementById('modalOverlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
    if (e.key === 'Enter' && document.getElementById('modalOverlay').classList.contains('open')) addScript();
  });

  function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
  }

  async function addScript() {
    const name = document.getElementById('scriptName').value.trim();
    const path = document.getElementById('scriptPath').value.trim();
    const args = document.getElementById('scriptArgs').value.trim();
    if (!name || !path) { showToast('Name and path are required.', 'error'); return; }
    const res = await fetch('/api/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name, path, args })
    });
    const data = await res.json();
    if (data.success) { closeModal(); showToast(`"${name}" added.`, 'success'); renderCard(data.script); }
    else showToast(data.error || 'Failed to add script.', 'error');
  }

  function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function renderCard(script) {
    document.getElementById('emptyState')?.remove();
    document.getElementById(`card-${script.id}`)?.remove();
    const grid = document.getElementById('scriptsGrid');
    const running = script.status === 'running';
    const card = document.createElement('div');
    card.className = `script-card ${running ? 'running' : ''}`;
    card.id = `card-${script.id}`;
    card.innerHTML = `
      <div class="status-dot ${running ? 'running' : ''}"></div>
      <div class="script-info">
        <div class="script-name">${escHtml(script.name)}</div>
        <div class="script-path">${escHtml(script.path)}${script.args ? ' ' + escHtml(script.args) : ''}</div>
      </div>
      <span class="status-badge ${running ? 'running' : 'stopped'}">${running ? '● Running' : '○ Stopped'}</span>
      <div class="controls">
        <button class="btn btn-start" id="btn-start-${script.id}" onclick="startScript('${script.id}')" ${running ? 'disabled' : ''}>▶ Start</button>
        <button class="btn btn-stop" id="btn-stop-${script.id}" onclick="stopScript('${script.id}')" ${!running ? 'disabled' : ''}>■ Stop</button>
        <button class="btn btn-restart" id="btn-restart-${script.id}" onclick="restartScript('${script.id}')" ${!running ? 'disabled' : ''}>↻ Restart</button>
        <button class="btn btn-kill" id="btn-kill-${script.id}" onclick="killScript('${script.id}')" ${!running ? 'disabled' : ''}>✕ Kill</button>
        <button class="btn btn-logs" onclick="toggleLogs('${script.id}')">≡ Logs</button>
        <button class="btn btn-remove" title="Remove script" onclick="removeScript('${script.id}')">🗑</button>
      </div>
      <div class="log-panel" id="log-${script.id}">
        <div class="log-header">Output Log</div>
        <div class="log-content" id="logcontent-${script.id}">No output yet.</div>
      </div>
    `;
    grid.appendChild(card);
  }

  function updateCard(script) {
    const card = document.getElementById(`card-${script.id}`);
    if (!card) return;
    const running = script.status === 'running';
    card.className = `script-card ${running ? 'running' : ''}`;
    card.querySelector('.status-dot').className = `status-dot ${running ? 'running' : ''}`;
    card.querySelector('.status-badge').className = `status-badge ${running ? 'running' : 'stopped'}`;
    card.querySelector('.status-badge').textContent = running ? '● Running' : '○ Stopped';
    card.querySelector(`#btn-start-${script.id}`).disabled = running;
    card.querySelector(`#btn-stop-${script.id}`).disabled = !running;
    card.querySelector(`#btn-restart-${script.id}`).disabled = !running;
    card.querySelector(`#btn-kill-${script.id}`).disabled = !running;
  }

  function toggleLogs(id) {
    logVisible[id] = !logVisible[id];
    const panel = document.getElementById(`log-${id}`);
    if (logVisible[id]) { panel.classList.add('open'); fetchLogs(id); }
    else panel.classList.remove('open');
  }

  async function fetchLogs(id) {
    const res = await fetch(`/api/logs/${id}`);
    const data = await res.json();
    const el = document.getElementById(`logcontent-${id}`);
    if (el) { el.textContent = data.logs || 'No output yet.'; el.scrollTop = el.scrollHeight; }
  }

  async function startScript(id) {
    const res = await fetch(`/api/start/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) { updateCard(data.script); showToast('Script started.', 'success'); }
    else showToast(data.error || 'Failed to start.', 'error');
  }

  async function stopScript(id) {
    const res = await fetch(`/api/stop/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) { updateCard(data.script); showToast('Script stopped.', 'info'); }
    else showToast(data.error || 'Failed to stop.', 'error');
  }

  async function restartScript(id) {
    const res = await fetch(`/api/restart/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) { updateCard(data.script); showToast('Script restarted.', 'info'); }
    else showToast(data.error || 'Failed to restart.', 'error');
  }

  async function killScript(id) {
    const res = await fetch(`/api/kill/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) { updateCard(data.script); showToast('Script killed.', 'error'); }
    else showToast(data.error || 'Failed to kill.', 'error');
  }

  async function removeScript(id) {
    const res = await fetch(`/api/remove/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      document.getElementById(`card-${id}`)?.remove();
      showToast('Script removed.', 'info');
      if (!document.querySelector('.script-card')) {
        const grid = document.getElementById('scriptsGrid');
        const empty = document.createElement('div');
        empty.className = 'empty-state';
        empty.id = 'emptyState';
        empty.innerHTML = '<div class="icon">📂</div><p>No scripts added yet.<br>Click <strong>+ Add Script</strong> to get started.</p>';
        grid.appendChild(empty);
      }
    }
  }

  async function pollStatus() {
    const res = await fetch('/api/status');
    const data = await res.json();
    for (const script of data.scripts) {
      updateCard(script);
      if (logVisible[script.id]) fetchLogs(script.id);
    }
  }

  setInterval(pollStatus, 2000);
</script>
</body>
</html>
"""

def get_script_info(sid):
    s = scripts.get(sid, {})
    proc = processes.get(sid)
    running = proc is not None and proc.poll() is None
    return {
        "id": sid,
        "name": s.get("name", ""),
        "path": s.get("path", ""),
        "args": s.get("args", ""),
        "status": "running" if running else "stopped"
    }

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/add", methods=["POST"])
def add_script():
    data = request.json
    name = data.get("name", "").strip()
    path = data.get("path", "").strip()
    args = data.get("args", "").strip()
    if not name or not path:
        return jsonify({"success": False, "error": "Name and path required."})
    script_id_counter[0] += 1
    sid = str(script_id_counter[0])
    scripts[sid] = {"name": name, "path": path, "args": args}
    logs[sid] = ""
    return jsonify({"success": True, "script": get_script_info(sid)})

@app.route("/api/start/<sid>", methods=["POST"])
def start_script(sid):
    if sid not in scripts:
        return jsonify({"success": False, "error": "Script not found."})
    proc = processes.get(sid)
    if proc and proc.poll() is None:
        return jsonify({"success": False, "error": "Already running."})
    s = scripts[sid]
    cmd = ["python3", s["path"]] + (s["args"].split() if s["args"] else [])
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes[sid] = proc
        logs[sid] = ""
        def reader():
            for line in proc.stdout:
                logs[sid] += line
                if len(logs[sid]) > 50000:
                    logs[sid] = logs[sid][-50000:]
        threading.Thread(target=reader, daemon=True).start()
        return jsonify({"success": True, "script": get_script_info(sid)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/stop/<sid>", methods=["POST"])
def stop_script(sid):
    proc = processes.get(sid)
    if not proc or proc.poll() is not None:
        return jsonify({"success": False, "error": "Not running."})
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    return jsonify({"success": True, "script": get_script_info(sid)})

@app.route("/api/restart/<sid>", methods=["POST"])
def restart_script(sid):
    proc = processes.get(sid)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return start_script(sid)

@app.route("/api/kill/<sid>", methods=["POST"])
def kill_script(sid):
    proc = processes.get(sid)
    if not proc or proc.poll() is not None:
        return jsonify({"success": False, "error": "Not running."})
    proc.kill()
    return jsonify({"success": True, "script": get_script_info(sid)})

@app.route("/api/remove/<sid>", methods=["POST"])
def remove_script(sid):
    proc = processes.get(sid)
    if proc and proc.poll() is None:
        proc.kill()
    processes.pop(sid, None)
    scripts.pop(sid, None)
    logs.pop(sid, None)
    return jsonify({"success": True})

@app.route("/api/logs/<sid>")
def get_logs(sid):
    return jsonify({"logs": logs.get(sid, "")})

@app.route("/api/status")
def status():
    return jsonify({"scripts": [get_script_info(sid) for sid in scripts]})

if __name__ == "__main__":
    print("Script Runner starting at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
