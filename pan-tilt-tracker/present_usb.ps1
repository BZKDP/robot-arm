Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.InstanceId -like 'USB\VID*' } |
  Select-Object Status, Class, FriendlyName, @{n='ID'; e={ ($_.InstanceId -split '\\')[1] }} |
  Sort-Object Class | Format-Table -Auto -Wrap
