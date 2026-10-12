Write-Output '=== PRISUTSTVUYUSCHIE USB (VID) ==='
Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.InstanceId -like 'USB\VID*' } |
  Select-Object Status, Class, FriendlyName, @{n='ID'; e={ ($_.InstanceId -split '\\')[1] }} |
  Sort-Object Class | Format-Table -Auto -Wrap
Write-Output '=== PROBLEMNYE prisutstvuyuschie (nuzhen drayver?) ==='
Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.Status -ne 'OK' } |
  Select-Object Status, Problem, Class, FriendlyName | Format-Table -Auto -Wrap
