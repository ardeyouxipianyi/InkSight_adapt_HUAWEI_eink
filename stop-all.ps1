# 停止 InkSight 的前后端进程（按端口 3000 / 8080 定位）。
foreach ($port in 3000, 8080) {
  $pids = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
  if (-not $pids) {
    Write-Host "port $port : not running"
    continue
  }
  foreach ($procId in $pids) {
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -in @("node", "python")) {
      Stop-Process -Id $procId -Force
      Write-Host "port $port : stopped $($proc.ProcessName) (PID $procId)"
    } else {
      Write-Warning "port $port : PID $procId is $($proc.ProcessName), not stopped"
    }
  }
}
