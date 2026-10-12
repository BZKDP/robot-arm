$j = Get-Content C:\pantilt\twin\config.json -Raw | ConvertFrom-Json
$j | Add-Member -NotePropertyName cam_port -NotePropertyValue 'COM3' -Force
$j | Add-Member -NotePropertyName cam_baud -NotePropertyValue 921600 -Force
$track = [ordered]@{ kp_yaw=170; kp_tilt=150; deadzone=0.05; yaw_sign=1; tilt_sign=1; max_step=45; fps=20 }
$j | Add-Member -NotePropertyName track -NotePropertyValue $track -Force
($j | ConvertTo-Json -Depth 6) | Set-Content C:\pantilt\twin\config.json -NoNewline
'OK cfg'
