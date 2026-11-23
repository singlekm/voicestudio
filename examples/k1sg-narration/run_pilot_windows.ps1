# Render one K1SG milestone on Windows using the REAL local VoiceStudio CLI.
# Prerequisites: VoiceStudio backend running, narrator/model configured,
# Python 3.11+ with VoiceStudio CLI installed, and FFmpeg for MP3 output.
# Keeps source and output in Git-ignored directories; uploads nothing.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Kit,
    [ValidatePattern('^M-(?:00[1-9]|0[1-9][0-9]|100)$')]
    [string]$Milestone = 'M-001',
    [string]$Voice = 'K1SG Documentary',
    [ValidateSet('wav', 'mp3')]
    [string]$Format = 'mp3',
    [string]$Python = 'python',
    [string]$Engine = '',
    [switch]$Overwrite
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$kitPath = (Resolve-Path -LiteralPath $Kit -ErrorAction Stop).Path
$privateInput = Join-Path $scriptRoot 'private_scripts'
$privateOutput = Join-Path $scriptRoot 'private_output'
$inputScript = Join-Path $privateInput ($Milestone + '.txt')
$importer = Join-Path $scriptRoot 'import_private_kit.py'
$preflight = Join-Path $scriptRoot 'preflight.py'
$renderer = Join-Path $scriptRoot 'render.py'
$number = [int]$Milestone.Substring(2, 3)

# Stage only the selected milestone. Don't overwrite a previously edited script.
if ((-not (Test-Path -LiteralPath $inputScript)) -or $Overwrite) {
    $importArgs = @($importer, '--kit', $kitPath,
                    '--dest', $privateInput, '--first', "$number",
                    '--last', "$number")
    if ($Overwrite) { $importArgs += '--overwrite' }
    & $Python @importArgs
    if ($LASTEXITCODE -ne 0) { throw 'Could not stage the private script.' }
}

$checkArgs = @($preflight, '--milestone', $Milestone,
               '--voice', $Voice, '--input-dir', $privateInput,
               '--format', $Format)
& $Python @checkArgs
if ($LASTEXITCODE -ne 0) {
    throw 'VoiceStudio is not ready. Install a compatible, legally permitted model and configure the saved voice profile, then retry.'
}

$renderArgs = @($renderer, '--milestone', $Milestone,
                '--input-dir', $privateInput,
                '--output-dir', $privateOutput,
                '--voice', $Voice, '--format', $Format)
if ($Engine.Trim()) { $renderArgs += @('--engine', $Engine) }
if ($Overwrite) { $renderArgs += '--overwrite' }
& $Python @renderArgs
if ($LASTEXITCODE -ne 0) { throw 'VoiceStudio failed to render the narration.' }
Write-Host ('Finished ' + $Milestone + ' using the local VoiceStudio engine.')
Write-Host ('Output directory: ' + $privateOutput)
