param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsFromUser
)
$ErrorActionPreference = 'Stop'
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $AppDir 'src' + [IO.Path]::PathSeparator + $env:PYTHONPATH
if (-not $env:NOTIZEN_FORCE_VISIBLE) { $env:NOTIZEN_FORCE_VISIBLE = '1' }
if (-not $env:NOTIZEN_RESET_WINDOW) { $env:NOTIZEN_RESET_WINDOW = '1' }
python -m notizen_py_qt --show --reset-window --no-tray @ArgsFromUser
