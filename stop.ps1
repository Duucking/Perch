Write-Host "=== 栖所 Perch 停止 ===" -ForegroundColor Cyan

$ports = @(5000, 3000)
$stopped = 0

foreach ($port in $ports) {
    $procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue
        $stopped++
    }
}

if ($stopped -gt 0) {
    Write-Host "已停止 $stopped 个进程" -ForegroundColor Green
} else {
    Write-Host "没有运行中的服务" -ForegroundColor Yellow
}