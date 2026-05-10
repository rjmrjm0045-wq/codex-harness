param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("pre_tool_use_policy.py", "stop_validation.py", "tdd_guard.py")]
    [string]$ScriptName
)

$ErrorActionPreference = "Stop"

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Could not resolve git repository root."
}

$scriptPath = Join-Path $repoRoot ".codex/hooks/$ScriptName"
$stdinPayload = [Console]::In.ReadToEnd()

if ($stdinPayload.Length -gt 0) {
    $stdinPayload | & python $scriptPath
} else {
    & python $scriptPath
}

exit $LASTEXITCODE
