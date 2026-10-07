# Starts the InkSight backend (FastAPI) on port 8080.
# Binds 0.0.0.0 so devices on the LAN (phone, ESP32) can reach it; use
# http://127.0.0.1:8080 locally. Set --host 127.0.0.1 to restrict to this PC.
$ErrorActionPreference = "Stop"

# Keep Python's default text encoding UTF-8 so config files that contain
# Chinese text are not read with the GBK default of zh-CN Windows.
$env:PYTHONUTF8 = "1"

Set-Location (Join-Path $PSScriptRoot "backend")
& .\.venv\Scripts\python.exe -m uvicorn api.index:app --host 0.0.0.0 --port 8080
