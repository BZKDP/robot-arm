$d = Get-PnpDevice -Class Display -PresentOnly -ErrorAction SilentlyContinue |
     Where-Object { $_.FriendlyName -like '*AMD Radeon*' -and $_.Status -ne 'OK' }
foreach ($x in $d) {
    Write-Output ('>>> pnputil enable-device: ' + $x.InstanceId)
    pnputil /enable-device "$($x.InstanceId)"
}
Start-Sleep -Seconds 6
Write-Output '--- posle ---'
Get-PnpDevice -Class Display -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.FriendlyName -like '*AMD*' } |
  Select-Object Status, Problem, FriendlyName | Format-List
