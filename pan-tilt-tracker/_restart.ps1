schtasks /end /tn PanTiltTracker 2>$null | Out-Null
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like 'C:\pantilt\*'} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Set-Content C:\pantilt\server.log -Value '' -NoNewline
schtasks /run /tn PanTiltTracker | Out-Null
Start-Sleep 8
(netstat -ano -p tcp | Select-String ':8200'); Get-Content C:\pantilt\server.log -Tail 4
