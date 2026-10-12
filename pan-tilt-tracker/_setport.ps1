$c = Get-Content C:\pantilt\twin\config.json -Raw
$c = $c -replace 'COM9','COM4'
Set-Content C:\pantilt\twin\config.json -Value $c -NoNewline
($c -split "`n" | Select-String 'port')
