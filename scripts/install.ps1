#Requires -Version 5.1

<#
.SYNOPSIS
    Installs the prerequisites for a manual Consortium install on Windows using winget.

.DESCRIPTION
    Checks for Python 3.14 or newer, Git, uv and Docker Desktop, and whether the Docker
    engine is currently running. Reports what was found and what is missing, asks for
    permission before changing anything, then installs the missing tools with winget.
    Once the prerequisites are in place it offers to run 'uv sync --all-packages' in the
    repository root to install the framework and bundled component dependencies.

.PARAMETER Yes
    Answer yes to every prompt. Intended for unattended runs.

.PARAMETER CheckOnly
    Only report what is found and what is missing, then exit without installing anything.

.PARAMETER SkipSync
    Do not offer to run 'uv sync --all-packages' after the prerequisites are installed.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Yes
#>

[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$CheckOnly,
    [switch]$SkipSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# winget writes progress and warnings to stderr, which powershell 7.4+ turns into
# terminating errors when native command errors honour $ErrorActionPreference. Exit codes
# are checked explicitly instead, so opt out of that behaviour where it exists
$PSNativeCommandUseErrorActionPreference = $false

# minimum python the framework supports, kept in step with
# docs/getting-started/installation.md
$script:MinPythonMajor = 3
$script:MinPythonMinor = 14

$script:RepoRoot = Split-Path -Parent $PSScriptRoot

# set on first use by Test-StorePythonInstalled
$script:StorePythonInstalled = $null

# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

function Write-Heading {
    param([string]$Text)

    Write-Host ''
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ('-' * $Text.Length) -ForegroundColor DarkGray
}

function Write-Ok {
    param([string]$Text)
    Write-Host "  [ ok ] $Text" -ForegroundColor Green
}

function Write-Miss {
    param([string]$Text)
    Write-Host "  [miss] $Text" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Text)
    Write-Host "  [fail] $Text" -ForegroundColor Red
}

function Write-Note {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor DarkGray
}

function Confirm-Action {
    param([string]$Question)

    if ($Yes) {
        Write-Host "$Question [Y/n] y (assumed)"
        return $true
    }
    if (-not [Environment]::UserInteractive) {
        Write-Host "$Question [Y/n] n (not interactive, re-run with -Yes to proceed)"
        return $false
    }
    while ($true) {
        $answer = Read-Host "$Question [Y/n]"
        if ([string]::IsNullOrWhiteSpace($answer)) { return $true }
        switch ($answer.Trim().ToLowerInvariant()) {
            'y' { return $true }
            'yes' { return $true }
            'n' { return $false }
            'no' { return $false }
            default { Write-Host "Please answer 'y' or 'n'." }
        }
    }
}

function Invoke-Native {
    param(
        [string]$File,
        [string[]]$Arguments = @()
    )

    Write-Host "  > $File $($Arguments -join ' ')" -ForegroundColor DarkGray
    & $File @Arguments
    return $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# detection helpers
# ---------------------------------------------------------------------------

function Test-StorePythonInstalled {
    # cached because the appx lookup is slow and is consulted for every python candidate
    if ($null -ne $script:StorePythonInstalled) { return $script:StorePythonInstalled }

    $script:StorePythonInstalled = $false
    try {
        $package = Get-AppxPackage -Name 'PythonSoftwareFoundation.Python*' -ErrorAction Stop -WarningAction SilentlyContinue
        $script:StorePythonInstalled = [bool]$package
    } catch {
        # without a usable appx lookup the alias cannot be told apart from a stub, so
        # leave it as not installed and let the py launcher or a winget install answer for
        # python instead
        $script:StorePythonInstalled = $false
    }
    return $script:StorePythonInstalled
}

function Get-UsableCommand {
    param([string]$Name)

    $command = Get-Command $Name -CommandType Application, ExternalScript -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $command) { return $null }

    # python.exe and python3.exe under WindowsApps are app execution aliases which, when
    # the store python is not installed, open the microsoft store instead of reporting a
    # version. every other alias there (winget among them) is a real command
    if ($command.Source -like '*\WindowsApps\*' -and $command.Name -match '^python3?(\.exe)?$') {
        if (Test-StorePythonInstalled) { return $command }
        return $null
    }
    return $command
}

function Get-ToolVersion {
    param(
        [string]$Name,
        [string[]]$Arguments = @('--version')
    )

    $command = Get-UsableCommand -Name $Name
    if (-not $command) { return $null }

    try {
        $output = (& $command.Source @Arguments 2>&1 | Out-String)
    } catch {
        return $null
    }
    if ($LASTEXITCODE -ne 0) { return $null }

    $line = ($output -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1)
    if (-not $line) { return $null }
    return $line.Trim()
}

function Find-Python {
    # the py launcher is preferred because it can select an interpreter by version
    # regardless of which python happens to be first on PATH
    $candidates = @(
        @{ File = 'py'; Arguments = @('-3.14', '--version') },
        @{ File = 'py'; Arguments = @('-3', '--version') },
        @{ File = 'python'; Arguments = @('--version') },
        @{ File = 'python3'; Arguments = @('--version') }
    )

    $older = $null
    foreach ($candidate in $candidates) {
        $version = Get-ToolVersion -Name $candidate.File -Arguments $candidate.Arguments
        if (-not $version) { continue }
        if ($version -notmatch 'Python\s+(\d+)\.(\d+)') { continue }

        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        $invocation = ($candidate.File + ' ' + ($candidate.Arguments -join ' ')).Replace(' --version', '')

        if ($major -gt $script:MinPythonMajor -or
            ($major -eq $script:MinPythonMajor -and $minor -ge $script:MinPythonMinor)) {
            return [pscustomobject]@{ Found = $true; Detail = "$version ($invocation)" }
        }
        if (-not $older) { $older = "$version ($invocation)" }
    }

    # uv can manage interpreters itself, and uv run/uv sync pick a managed one up
    # automatically, so a uv managed 3.14 satisfies the requirement just as well
    if (Get-UsableCommand -Name 'uv') {
        try {
            $managed = (& uv python find '>=3.14' 2>$null | Out-String).Trim()
        } catch {
            $managed = ''
        }
        if ($LASTEXITCODE -eq 0 -and $managed) {
            return [pscustomobject]@{ Found = $true; Detail = "uv managed ($managed)" }
        }
    }

    if ($older) {
        return [pscustomobject]@{ Found = $false; Detail = "found $older, older than 3.14" }
    }
    return [pscustomobject]@{ Found = $false; Detail = 'not found' }
}

function Get-DockerDesktopPath {
    $candidates = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Docker\Docker\Docker Desktop.exe')
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path -LiteralPath $path)) { return $path }
    }
    return $null
}

function New-Requirements {
    return @(
        [pscustomobject]@{
            Key      = 'python'
            Name     = 'Python 3.14+'
            WingetId = 'Python.Python.3.14'
            Service  = $false
            Found    = $false
            Detail   = ''
        },
        [pscustomobject]@{
            Key      = 'git'
            Name     = 'Git'
            WingetId = 'Git.Git'
            Service  = $false
            Found    = $false
            Detail   = ''
        },
        [pscustomobject]@{
            Key      = 'uv'
            Name     = 'uv'
            WingetId = 'astral-sh.uv'
            Service  = $false
            Found    = $false
            Detail   = ''
        },
        [pscustomobject]@{
            Key      = 'docker'
            Name     = 'Docker Desktop'
            WingetId = 'Docker.DockerDesktop'
            Service  = $false
            Found    = $false
            Detail   = ''
        },
        [pscustomobject]@{
            Key      = 'docker-engine'
            Name     = 'Docker engine'
            WingetId = $null
            Service  = $true
            Found    = $false
            Detail   = ''
        }
    )
}

function Update-Requirements {
    param([object[]]$Requirements)

    foreach ($requirement in $Requirements) {
        switch ($requirement.Key) {
            'python' {
                $python = Find-Python
                $requirement.Found = $python.Found
                $requirement.Detail = $python.Detail
            }
            'git' {
                $version = Get-ToolVersion -Name 'git'
                $requirement.Found = [bool]$version
                $requirement.Detail = if ($version) { $version } else { 'not found' }
            }
            'uv' {
                $version = Get-ToolVersion -Name 'uv'
                $requirement.Found = [bool]$version
                $requirement.Detail = if ($version) { $version } else { 'not found' }
            }
            'docker' {
                $version = Get-ToolVersion -Name 'docker'
                if ($version) {
                    $requirement.Found = $true
                    $requirement.Detail = $version
                } elseif (Get-DockerDesktopPath) {
                    $requirement.Found = $true
                    $requirement.Detail = 'installed, docker client not on PATH yet'
                } else {
                    $requirement.Found = $false
                    $requirement.Detail = 'not found'
                }
            }
            'docker-engine' {
                if (-not (Get-UsableCommand -Name 'docker')) {
                    $requirement.Found = $false
                    $requirement.Detail = 'not running (Docker Desktop is not installed)'
                } else {
                    # docker info only succeeds when the client can reach a running engine
                    & docker info --format '{{.ServerVersion}}' > $null 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        $requirement.Found = $true
                        $requirement.Detail = 'running'
                    } else {
                        $requirement.Found = $false
                        $requirement.Detail = 'not running'
                    }
                }
            }
        }
    }
}

function Write-RequirementReport {
    param([object[]]$Requirements)

    $found = @($Requirements | Where-Object { $_.Found })
    $missing = @($Requirements | Where-Object { -not $_.Found })

    Write-Heading 'Found'
    if ($found.Count -eq 0) {
        Write-Note 'nothing'
    } else {
        foreach ($requirement in $found) {
            Write-Ok ('{0,-16} {1}' -f $requirement.Name, $requirement.Detail)
        }
    }

    Write-Heading 'Missing'
    if ($missing.Count -eq 0) {
        Write-Note 'nothing'
    } else {
        foreach ($requirement in $missing) {
            Write-Miss ('{0,-16} {1}' -f $requirement.Name, $requirement.Detail)
        }
    }

    return $missing
}

function Update-SessionPath {
    # installers write to the machine and user PATH, which this already running process
    # does not pick up, so rebuild the session PATH from the registry after installing
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @($machine, $user) | Where-Object { $_ }
    if ($parts) { $env:Path = ($parts -join ';') }
}

# ---------------------------------------------------------------------------
# install actions
# ---------------------------------------------------------------------------

function Install-WithWinget {
    param([object]$Requirement)

    $arguments = @(
        'install',
        '--id', $Requirement.WingetId,
        '--exact',
        '--source', 'winget',
        '--accept-package-agreements',
        '--accept-source-agreements'
    )
    if ($Yes) { $arguments += '--disable-interactivity' }

    $exitCode = Invoke-Native -File 'winget' -Arguments $arguments
    switch ($exitCode) {
        0 {
            Write-Ok "$($Requirement.Name) installed"
            return $true
        }
        # APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE, reported when the package is
        # already present at the requested version
        -1978335189 {
            Write-Ok "$($Requirement.Name) already installed"
            return $true
        }
        default {
            Write-Fail "$($Requirement.Name) install failed (winget exit code $exitCode)"
            return $false
        }
    }
}

function Start-DockerDesktop {
    $path = Get-DockerDesktopPath
    if (-not $path) {
        Write-Fail 'Docker Desktop executable not found, start the engine by hand'
        return $false
    }
    Write-Host "  > `"$path`"" -ForegroundColor DarkGray
    try {
        Start-Process -FilePath $path | Out-Null
    } catch {
        Write-Fail "could not start Docker Desktop: $($_.Exception.Message)"
        return $false
    }
    Write-Note 'Docker Desktop was started, the engine takes a moment to come up'
    return $true
}

function Invoke-Sync {
    Write-Heading 'Installing Consortium dependencies'

    if (-not (Get-UsableCommand -Name 'uv')) {
        Write-Fail 'uv is not available on PATH, skipping dependency install'
        return $false
    }

    Push-Location -LiteralPath $script:RepoRoot
    try {
        $exitCode = Invoke-Native -File 'uv' -Arguments @('sync', '--all-packages')
    } finally {
        Pop-Location
    }

    if ($exitCode -eq 0) {
        Write-Ok 'dependencies installed'
        return $true
    }
    Write-Fail "uv sync failed (exit code $exitCode)"
    return $false
}

# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host 'Consortium install (Windows)' -ForegroundColor White
Write-Note "repository root: $script:RepoRoot"

if (-not (Get-UsableCommand -Name 'winget')) {
    Write-Heading 'Package manager'
    Write-Fail 'winget was not found on PATH'
    Write-Note 'winget ships with the "App Installer" package. Install or update it from the'
    Write-Note 'Microsoft Store, or from https://github.com/microsoft/winget-cli/releases,'
    Write-Note 'then run this script again.'
    exit 1
}
Write-Note "package manager: winget ($(Get-ToolVersion -Name 'winget'))"

$requirements = New-Requirements
Update-Requirements -Requirements $requirements
$missing = @(Write-RequirementReport -Requirements $requirements)

if ($CheckOnly) {
    Write-Host ''
    if ($missing.Count -eq 0) {
        Write-Host 'All prerequisites are present.' -ForegroundColor Green
        exit 0
    }
    Write-Host 'Prerequisites are missing, re-run without -CheckOnly to install them.' -ForegroundColor Yellow
    exit 1
}

if ($missing.Count -gt 0) {
    # the engine is started rather than installed, and only once docker itself is present
    $toInstall = @($missing | Where-Object { $_.WingetId })
    $startEngine = [bool]($missing | Where-Object { $_.Key -eq 'docker-engine' })

    Write-Heading 'Planned actions'
    foreach ($requirement in $toInstall) {
        Write-Note "install $($requirement.Name) : winget install --id $($requirement.WingetId) --exact --source winget"
    }
    if ($startEngine) {
        Write-Note 'start Docker Desktop so the engine is available'
    }

    Write-Host ''
    if (-not (Confirm-Action 'Install the missing prerequisites?')) {
        Write-Host ''
        Write-Host 'Nothing was installed.' -ForegroundColor Yellow
        exit 1
    }

    foreach ($requirement in $toInstall) {
        Write-Heading "Installing $($requirement.Name)"
        Install-WithWinget -Requirement $requirement | Out-Null
    }

    Update-SessionPath

    if ($startEngine) {
        Write-Heading 'Starting the Docker engine'
        Start-DockerDesktop | Out-Null
    }

    Update-Requirements -Requirements $requirements
    Write-Heading 'Re-checking'
    foreach ($requirement in $requirements) {
        if ($requirement.Found) {
            Write-Ok ('{0,-16} {1}' -f $requirement.Name, $requirement.Detail)
        } else {
            Write-Miss ('{0,-16} {1}' -f $requirement.Name, $requirement.Detail)
        }
    }
}

$stillMissingTools = @($requirements | Where-Object { -not $_.Found -and -not $_.Service })
$engineDown = [bool]($requirements | Where-Object { $_.Key -eq 'docker-engine' -and -not $_.Found })

if ($stillMissingTools.Count -gt 0) {
    Write-Heading 'Result'
    Write-Fail 'some prerequisites are still missing:'
    foreach ($requirement in $stillMissingTools) {
        Write-Note "- $($requirement.Name): $($requirement.Detail)"
    }
    Write-Note 'A tool installed just now may only appear on PATH in a new terminal. Open a'
    Write-Note 'new terminal and run this script again to confirm before installing by hand.'
    exit 1
}

if (-not $SkipSync) {
    Write-Host ''
    if (Confirm-Action "Run 'uv sync --all-packages' in $script:RepoRoot now?") {
        if (-not (Invoke-Sync)) { exit 1 }
    } else {
        Write-Note "skipped, run 'uv sync --all-packages' before starting the server"
    }
}

Write-Heading 'Result'
Write-Ok 'all prerequisites are present'
if ($engineDown) {
    Write-Miss 'the Docker engine is not running'
    Write-Note 'Start Docker Desktop before using an agent generator that compiles its payload'
    Write-Note 'in a container. Everything else runs without it.'
}
Write-Note 'Start the server with: uv run consortium.py server'
Write-Note 'Connect the client with: uv run consortium.py client'
exit 0
