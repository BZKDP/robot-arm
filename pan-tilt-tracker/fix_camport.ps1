$p = 'C:\pantilt\twin\config.json'
$c = Get-Content $p -Raw
$c = $c.Replace('"cam_port": "COM3"', '"cam_port": "COM5"')
[System.IO.File]::WriteAllText($p, $c)
Stop-ScheduledTask -TaskName PanTiltTracker -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName PanTiltTracker
Write-Output 'config updated COM3->COM5 + task restarted'
