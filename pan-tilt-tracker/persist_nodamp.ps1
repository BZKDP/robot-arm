$p = 'C:\pantilt\twin\config.json'
$c = Get-Content $p -Raw
if ($c -notmatch 'nod_amp') {
    $c = $c.Replace('"search_tilt": 2600', '"search_tilt": 2600,' + "`n    " + '"nod_amp": 182')
    [System.IO.File]::WriteAllText($p, $c)
}
if ((Get-Content $p -Raw) -match 'nod_amp"\s*:\s*182') { 'OK nod_amp=182 persisted' } else { 'FAIL' }
