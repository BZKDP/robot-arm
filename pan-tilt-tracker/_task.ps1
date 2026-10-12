schtasks /end /tn PanTiltTracker 2>$null | Out-Null
schtasks /delete /tn PanTiltTracker /f 2>$null | Out-Null
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like 'C:\pantilt\*'} | Stop-Process -Force -ErrorAction SilentlyContinue
schtasks /create /tn PanTiltTracker /tr "C:\pantilt\run_server.bat" /sc onstart /ru SYSTEM /rl HIGHEST /f
schtasks /run /tn PanTiltTracker
Start-Sleep 8
'--- PORT ---'; (netstat -ano -p tcp | Select-String ':8200')
'--- LOG ---'; Get-Content C:\pantilt\server.log -Tail 6
