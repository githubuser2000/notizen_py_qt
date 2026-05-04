param(
    [string]$Python = 'python',
    [string]$Launcher = '',
    [switch]$UseLauncher,
    [switch]$WhatIfOnly
)
$ErrorActionPreference = 'Stop'
$AppDir = Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '..')
if ($UseLauncher -and -not $Launcher) {
    $Launcher = Join-Path $AppDir 'Notizen starten.cmd'
}
if ($UseLauncher) {
    $OpenCommand = '"' + $Launcher + '" --show --no-tray --reset-window "%1"'
    $IconPath = $Launcher
} else {
    $ResolvedPython = (Get-Command $Python).Source
    $OpenCommand = '"' + $ResolvedPython + '" -m notizen_py_qt --show --no-tray --reset-window "%1"'
    $IconPath = $ResolvedPython
}
$Base = 'HKCU:\Software\Classes'
$Operations = @(
    @{ Path = "$Base\.alx"; Name = ''; Value = 'Notizenfile'; IfMissing = $true },
    @{ Path = "$Base\.alx\OpenWithList"; Name = ''; Value = ''; IfMissing = $true },
    @{ Path = "$Base\.alx\OpenWithList\Notizen.exe"; Name = ''; Value = ''; IfMissing = $true },
    @{ Path = "$Base\.alx\OpenWithProgIds"; Name = ''; Value = ''; IfMissing = $true },
    @{ Path = "$Base\.alx\OpenWithProgIds"; Name = 'notizenfile'; Value = ''; IfMissing = $true },
    @{ Path = "$Base\notizenfile"; Name = ''; Value = ''; IfMissing = $true },
    @{ Path = "$Base\notizenfile\Shell"; Name = ''; Value = 'Open'; IfMissing = $true },
    @{ Path = "$Base\notizenfile\Shell\Open"; Name = ''; Value = ''; IfMissing = $true },
    @{ Path = "$Base\notizenfile\Shell\Open\Command"; Name = ''; Value = $OpenCommand; IfMissing = $false },
    @{ Path = "$Base\notizenfile\DefaultIcon"; Name = ''; Value = $IconPath; IfMissing = $false }
)
foreach ($op in $Operations) {
    if ($WhatIfOnly) {
        Write-Host "$($op.Path) [$($op.Name)] = $($op.Value)"
        continue
    }
    if (-not (Test-Path $op.Path)) { New-Item -Path $op.Path -Force | Out-Null }
    if ($op.IfMissing) {
        $existing = $null
        try {
            if ($op.Name) { $existing = (Get-ItemProperty -Path $op.Path -Name $op.Name -ErrorAction Stop).($op.Name) }
            else { $existing = (Get-Item -Path $op.Path).GetValue('') }
        } catch { $existing = $null }
        if ($null -ne $existing) { continue }
    }
    if ($op.Name) { New-ItemProperty -Path $op.Path -Name $op.Name -Value $op.Value -PropertyType String -Force | Out-Null }
    else { Set-ItemProperty -Path $op.Path -Name '(default)' -Value $op.Value }
}
if (-not $WhatIfOnly) {
    Write-Host 'Notizen PyQt .alx-Dateizuordnung wurde unter HKCU\Software\Classes eingerichtet.'
    Write-Host "Open command: $OpenCommand"
}
