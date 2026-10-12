$py = 'C:\pantilt\venv\Scripts\python.exe'
Get-Process | Where-Object { $_.Path -eq $py -and $_.CommandLine -match 'server.py' } 2>$null | Stop-Process -Force -ErrorAction SilentlyContinue
$code = "import subprocess; subprocess.Popen([r'$py','-u', r'C:\pantilt\twin\server.py'], creationflags=0x00000008|0x00000200, stdout=open(r'C:\pantilt\server.log','w'), stderr=subprocess.STDOUT, cwd=r'C:\pantilt\twin')"
& $py -c $code
Start-Sleep 7
'--- LOG ---'
Get-Content C:\pantilt\server.log -Raw
'--- PORT ---'
(netstat -ano -p tcp | Select-String ':8200')
