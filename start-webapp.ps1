# Starts the InkSight web app (Next.js) on http://127.0.0.1:3000
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "webapp")
npm run dev
