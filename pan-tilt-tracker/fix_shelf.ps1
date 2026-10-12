$p = 'C:\pantilt\twin\config.json'
$c = Get-Content $p -Raw
# 1) kamera teper na stellazhe (ne pod potolkom) -> vernut polnyy diapazon naklona + poisk po centru
$c = $c.Replace('"min": 2200', '"min": 1519')
$c = $c.Replace('"search_tilt": 2600', '"search_tilt": 2048')
# 2) stabilnost: ne dergaetsya kogda sidish rovno
$c = $c.Replace('"deadzone": 0.05', '"deadzone": 0.09')   # bolshe myortvaya zona -> blizko k centru ne korrektiruet
$c = $c.Replace('"lead": 0.12', '"lead": 0.03')           # menshe uprezhdenie -> ne ohotitsya za shumom (glavnaya prichina kolebaniy)
$c = $c.Replace('"smooth": 0.3', '"smooth": 0.55')        # silnee sglazhivanie tochki golovy
$c = $c.Replace('"kp_yaw": 260', '"kp_yaw": 210')         # myagche korrekciya povorota
$c = $c.Replace('"kp_tilt": 240', '"kp_tilt": 190')       # myagche naklon
[System.IO.File]::WriteAllText($p, $c)
Stop-ScheduledTask -TaskName PanTiltTracker -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName PanTiltTracker
Write-Output 'config: naklon 1519-3138, search_tilt 2048, deadzone 0.09, lead 0.03, smooth 0.55, kp 210/190 + restart'
