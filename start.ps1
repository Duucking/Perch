$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== 栖所 Perch 启动 ===" -ForegroundColor Cyan

# Kill existing processes on target ports
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Start-Sleep -Seconds 1

# Start backend
$backend = Start-Process -WindowStyle Normal -FilePath "python" -ArgumentList "app.py" -WorkingDirectory "$root\backend" -PassThru
Write-Host "[Backend] 启动中... PID: $($backend.Id)" -ForegroundColor Green

# Start frontend
$env:Path = "C:\Program Files\nodejs;$env:Path"
$frontend = Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$root\frontend" -PassThru
Write-Host "[Frontend] 启动中... PID: $($frontend.Id)" -ForegroundColor Green

Start-Sleep -Seconds 3

# Verify
$bp = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
$fp = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }

if ($bp) {
    Write-Host "[Backend]  http://localhost:5000  ✓" -ForegroundColor Green
} else {
    Write-Host "[Backend]  启动失败" -ForegroundColor Red
}

if ($fp) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -First 1).IPAddress
    Write-Host "[Frontend] http://localhost:3000  ✓" -ForegroundColor Green
    if ($ip) {
        Write-Host "[Network]  http://${ip}:3000  (其他设备)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[Frontend] 启动失败" -ForegroundColor Red
}