Set-Content C:\pantilt\server.log -Value '' -NoNewline
schtasks /run /tn PanTiltTracker | Out-Null
Start-Sleep 9
'--- PORT ---'; (netstat -ano -p tcp | Select-String ':8200')
'--- LOG ---'; Get-Content C:\pantilt\server.log -Tail 6
