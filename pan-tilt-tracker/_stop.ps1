schtasks /end /tn PanTiltTracker 2>$null | Out-Null
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like 'C:\pantilt\*'} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2; 'server stopped'
