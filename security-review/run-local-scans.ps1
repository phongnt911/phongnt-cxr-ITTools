param([string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
$outputFolder = Join-Path $ProjectRoot 'security-review'
$scanner = 'C:\Program Files\Fortinet\FortiClient\av_task.exe'
$results = @()
foreach ($item in @(
    @{ Name = 'assets'; Path = (Join-Path $ProjectRoot 'ITTools\assets') },
    @{ Name = 'release'; Path = (Join-Path $ProjectRoot 'dist\IT_Tool_SAGS_CXR_2026.exe') }
)) {
    try {
        $process = Start-Process -FilePath $scanner -ArgumentList @('-s', 'a_0', '-t', '0', '-d', ('"' + $item.Path + '"')) -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $outputFolder ('forticlient-' + $item.Name + '.stdout.log')) -RedirectStandardError (Join-Path $outputFolder ('forticlient-' + $item.Name + '.stderr.log'))
        $results += [PSCustomObject]@{ Target = $item.Path; ExitCode = $process.ExitCode; Time = (Get-Date -Format o); Note = 'Process exit is not a malware verdict; verify FortiClient scan logs and file counters.' }
    } catch {
        $results += [PSCustomObject]@{ Target = $item.Path; Error = $_.Exception.Message; Time = (Get-Date -Format o) }
    }
}
$results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outputFolder 'local-scan-attempts.json') -Encoding UTF8
