# GPU engine utilization (vse dvizhki) - vo vremya raboty trekera
$s = (Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples
$top = $s | Where-Object {$_.CookedValue -gt 1} | Sort-Object CookedValue -Descending | Select-Object -First 4
"=== GPU dvizhki (>1%) ==="
$top | ForEach-Object { "{0,5:N0}%  {1}" -f $_.CookedValue, ($_.InstanceName -replace '.*engtype_','') }
"GPU SUM: {0:N0}%" -f (($s | Measure-Object CookedValue -Sum).Sum)
"=== CPU/RAM ==="
"CPU total: {0:N0}%" -f (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
$os = Get-CimInstance Win32_OperatingSystem
"RAM: {0:N1} / {1:N1} GB ispolzuetsya" -f ((($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/1MB)),(($os.TotalVisibleMemorySize/1MB))
"=== python (treker) ==="
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like 'C:\pantilt\*'} | ForEach-Object { "PID {0}  RAM {1} MB" -f $_.Id, [int]($_.WorkingSet64/1MB) }
