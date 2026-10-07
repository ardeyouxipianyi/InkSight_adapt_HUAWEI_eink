# 启动 InkSight 后端 + 前端，作为独立后台进程运行（关闭终端后不会退出）。
# 日志写到仓库上一级目录：backend.out.log / backend.err.log / webapp.out.log / webapp.err.log
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$logDir = Split-Path -Parent $root

# 中文 Windows 上必须设置，否则读 UTF-8 配置会报编码错误
$env:PYTHONUTF8 = "1"

$backend = Join-Path $root "backend"
$webapp = Join-Path $root "webapp"

$backendArgs = @{
  FilePath               = (Join-Path $backend ".venv\Scripts\python.exe")
  ArgumentList           = @("-m", "uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080")
  WorkingDirectory       = $backend
  WindowStyle            = "Hidden"
  RedirectStandardOutput = (Join-Path $logDir "backend.out.log")
  RedirectStandardError  = (Join-Path $logDir "backend.err.log")
}
Start-Process @backendArgs

$webappArgs = @{
  FilePath               = "npm.cmd"
  ArgumentList           = @("run", "dev")
  WorkingDirectory       = $webapp
  WindowStyle            = "Hidden"
  RedirectStandardOutput = (Join-Path $logDir "webapp.out.log")
  RedirectStandardError  = (Join-Path $logDir "webapp.err.log")
}
Start-Process @webappArgs

Start-Sleep -Seconds 8

foreach ($port in 3000, 8080) {
  $listen = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
  if ($listen) {
    $addr = ($listen | Select-Object -First 1).LocalAddress
    Write-Host "port $port listening on $addr"
  } else {
    Write-Warning "port $port is NOT listening - check the logs in $logDir"
  }
}

Write-Host ""
Write-Host "WebApp  : http://127.0.0.1:3000"
Write-Host "Backend : http://127.0.0.1:8080"
