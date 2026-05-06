param(
    [string]$UsersCsv = "data/users.csv",
    [string]$CoursesCsv = "data/courses.csv",
    [string]$MembersCsv = "data/members.csv"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$command = @(
    "docker-compose",
    "run",
    "--rm",
    "web",
    "python",
    "manage.py",
    "clear_imported_data",
    "--users-csv",
    $UsersCsv,
    "--courses-csv",
    $CoursesCsv,
    "--members-csv",
    $MembersCsv
)

Write-Host "Menjalankan command Docker:" -ForegroundColor Cyan
Write-Host ($command -join ' ')

$dockerComposeExe = "docker-compose"
if (-not (Get-Command $dockerComposeExe -ErrorAction SilentlyContinue)) {
    $dockerComposeExe = "docker"
    $dockerComposeArgs = @("compose") + $command[1..($command.Length - 1)]
} else {
    $dockerComposeArgs = $command[1..($command.Length - 1)]
}

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = $dockerComposeExe
$processInfo.Arguments = [string]::Join(' ', $dockerComposeArgs)
$processInfo.RedirectStandardOutput = $false
$processInfo.RedirectStandardError = $false
$processInfo.UseShellExecute = $true

$process = [System.Diagnostics.Process]::Start($processInfo)
$process.WaitForExit()

if ($process.ExitCode -ne 0) {
    throw "Docker command gagal dengan exit code $($process.ExitCode)."
}
