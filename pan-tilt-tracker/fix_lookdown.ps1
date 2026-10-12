$p = 'C:\pantilt\twin\config.json'
$c = Get-Content $p -Raw
# naklon id2 (klyuch "pan"): zapret smotret vverh -> min 1519 -> 2200
$c = $c.Replace('"min": 1519', '"min": 2200')
# poisk parkuetsya vniz (na uroven lyudey)
$c = $c.Replace('"lock_dist": 0.35', '"lock_dist": 0.35,' + "`n    " + '"search_tilt": 2600')
[System.IO.File]::WriteAllText($p, $c)
Stop-ScheduledTask -TaskName PanTiltTracker -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName PanTiltTracker
Write-Output 'cfg: tilt min->2200 (no up), search_tilt->2600 (down) + restart'
