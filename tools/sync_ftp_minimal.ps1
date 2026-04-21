[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FtpHost,

    [Parameter(Mandatory = $true)]
    [string]$User,

    [Parameter(Mandatory = $true)]
    [string]$Password,

    [int]$Port = 21,

    [string]$RemoteRoot = '/',

    [string]$LocalRoot = 'ftp_dump_minimal',

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:DownloadedFiles = New-Object System.Collections.Generic.List[string]
$script:SkippedByPath = New-Object System.Collections.Generic.List[string]
$script:SkippedByExt = New-Object System.Collections.Generic.List[string]
$script:EffectiveRemoteRoot = '/'

$ExcludedPathFragments = @(
    '/wp-content/uploads',
    '/wp-content/themes/land76wp/img',
    '/cache',
    '/backup',
    '/backups',
    '/tmp',
    '/temp',
    '/logs'
)

$ExcludedExtensions = @(
    '.zip', '.tar', '.gz', '.sql', '.bak', '.log'
)

function Normalize-RemotePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return '/' }
    $normalized = $Path -replace '\\', '/'
    if (-not $normalized.StartsWith('/')) { $normalized = '/' + $normalized }
    $normalized = $normalized -replace '/{2,}', '/'
    if ($normalized.Length -gt 1 -and $normalized.EndsWith('/')) {
        $normalized = $normalized.TrimEnd('/')
    }
    return $normalized
}

function Join-RemotePath {
    param(
        [string]$Base,
        [string]$Child
    )
    $baseNorm = Normalize-RemotePath -Path $Base
    $childNorm = ($Child -replace '\\', '/').Trim('/')
    if ([string]::IsNullOrEmpty($childNorm)) { return $baseNorm }
    if ($baseNorm -eq '/') { return "/$childNorm" }
    return "$baseNorm/$childNorm"
}

function Get-FtpLeafName {
    param([string]$Entry)

    $value = [string]$Entry
    $value = $value.Trim()
    if ([string]::IsNullOrWhiteSpace($value)) { return '' }
    $value = $value -replace '\\', '/'
    $value = $value.TrimEnd('/')
    if ([string]::IsNullOrWhiteSpace($value)) { return '' }

    if ($value.Contains('/')) {
        return $value.Substring($value.LastIndexOf('/') + 1)
    }

    return $value
}

function New-FtpRequest {
    param(
        [string]$Method,
        [string]$RemotePath
    )

    $safePath = Normalize-RemotePath -Path $RemotePath
    $uri = [Uri]::new(("ftp://{0}:{1}{2}" -f $FtpHost, $Port, $safePath))
    $request = [System.Net.FtpWebRequest]::Create($uri)
    $request.Method = $Method
    $request.Credentials = [System.Net.NetworkCredential]::new($User, $Password)
    $request.UseBinary = $true
    $request.UsePassive = $true
    $request.KeepAlive = $false
    $request.ReadWriteTimeout = 60000
    $request.Timeout = 60000
    return $request
}

function Invoke-FtpListDirectory {
    param([string]$RemotePath)

    $request = New-FtpRequest -Method ([System.Net.WebRequestMethods+Ftp]::ListDirectory) -RemotePath $RemotePath
    try {
        $response = [System.Net.FtpWebResponse]$request.GetResponse()
        $stream = $response.GetResponseStream()
        $reader = [System.IO.StreamReader]::new($stream)
        $content = $reader.ReadToEnd()
        $reader.Dispose()
        $stream.Dispose()
        $response.Dispose()

        if ([string]::IsNullOrWhiteSpace($content)) {
            return @()
        }

        return $content -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }
    catch {
        throw "FTP list failed for '$RemotePath': $($_.Exception.Message)"
    }
}

function Invoke-FtpListDirectoryDetails {
    param([string]$RemotePath)

    $request = New-FtpRequest -Method ([System.Net.WebRequestMethods+Ftp]::ListDirectoryDetails) -RemotePath $RemotePath
    try {
        $response = [System.Net.FtpWebResponse]$request.GetResponse()
        $stream = $response.GetResponseStream()
        $reader = [System.IO.StreamReader]::new($stream)
        $content = $reader.ReadToEnd()
        $reader.Dispose()
        $stream.Dispose()
        $response.Dispose()

        if ([string]::IsNullOrWhiteSpace($content)) {
            return @()
        }

        return $content -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }
    catch {
        throw "FTP list details failed for '$RemotePath': $($_.Exception.Message)"
    }
}

function Get-FtpListItems {
    param([string]$RemotePath)

    $items = New-Object System.Collections.Generic.List[object]
    $lines = Invoke-FtpListDirectoryDetails -RemotePath $RemotePath

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }

        # Unix-like format: drwxr-xr-x ... name
        $unix = [regex]::Match($trimmed, '^(?<type>[dl-])[rwx\-]{9}\s+\d+\s+\S+\s+\S+\s+\d+\s+\w+\s+\d+\s+[\d:]+\s+(?<name>.+)$')
        if ($unix.Success) {
            $entryName = Get-FtpLeafName -Entry $unix.Groups['name'].Value
            $isDir = $unix.Groups['type'].Value -eq 'd'
            $items.Add([pscustomobject]@{
                Name = $entryName
                IsDirectory = $isDir
                Raw = $trimmed
            })
            continue
        }

        # DOS format: 01-30-26  11:12AM       <DIR> folder
        $dos = [regex]::Match($trimmed, '^\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}(AM|PM)\s+(?<size><DIR>|\d+)\s+(?<name>.+)$')
        if ($dos.Success) {
            $entryName = Get-FtpLeafName -Entry $dos.Groups['name'].Value
            $isDir = $dos.Groups['size'].Value -eq '<DIR>'
            $items.Add([pscustomobject]@{
                Name = $entryName
                IsDirectory = $isDir
                Raw = $trimmed
            })
            continue
        }

        # Fallback as unknown; can be resolved by one explicit check if needed.
        $fallbackName = Get-FtpLeafName -Entry $trimmed
        $items.Add([pscustomobject]@{
            Name = $fallbackName
            IsDirectory = $null
            Raw = $trimmed
        })
    }

    return $items
}

function Test-FtpDirectory {
    param([string]$RemotePath)

    try {
        $null = Invoke-FtpListDirectory -RemotePath $RemotePath
        return $true
    }
    catch {
        return $false
    }
}

function Ensure-LocalDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Convert-RemoteToLocalPath {
    param([string]$RemotePath)

    $remoteNorm = Normalize-RemotePath -Path $RemotePath
    $rootNorm = Normalize-RemotePath -Path $script:EffectiveRemoteRoot

    if ($remoteNorm -eq $rootNorm) {
        $relative = ''
    }
    elseif ($remoteNorm.StartsWith("$rootNorm/")) {
        $relative = $remoteNorm.Substring($rootNorm.Length).TrimStart('/')
    }
    else {
        $relative = $remoteNorm.TrimStart('/')
    }

    if ([string]::IsNullOrWhiteSpace($relative)) { return $LocalRoot }
    $parts = $relative -split '/'
    return Join-Path -Path $LocalRoot -ChildPath ([System.IO.Path]::Combine($parts))
}

function Should-ExcludeByPath {
    param([string]$RemotePath)

    $normalized = (Normalize-RemotePath -Path $RemotePath).ToLowerInvariant()
    foreach ($fragment in $ExcludedPathFragments) {
        if ($normalized.Contains($fragment.ToLowerInvariant())) {
            $script:SkippedByPath.Add($normalized)
            return $true
        }
    }
    return $false
}

function Should-ExcludeByExtension {
    param([string]$RemotePath)

    $ext = [System.IO.Path]::GetExtension($RemotePath).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($ext)) { return $false }
    if ($ExcludedExtensions -contains $ext) {
        $script:SkippedByExt.Add((Normalize-RemotePath -Path $RemotePath).ToLowerInvariant())
        return $true
    }
    return $false
}

function Download-FtpFile {
    param([string]$RemoteFile)

    if (Should-ExcludeByPath -RemotePath $RemoteFile) {
        Write-Host "[skip:path] $RemoteFile"
        return
    }
    if (Should-ExcludeByExtension -RemotePath $RemoteFile) {
        Write-Host "[skip:ext]  $RemoteFile"
        return
    }

    $localFile = Convert-RemoteToLocalPath -RemotePath $RemoteFile
    $localDir = Split-Path -Path $localFile -Parent
    Ensure-LocalDirectory -Path $localDir

    if ($DryRun) {
        Write-Host "[dry:file]  $RemoteFile -> $localFile"
        return
    }

    $request = New-FtpRequest -Method ([System.Net.WebRequestMethods+Ftp]::DownloadFile) -RemotePath $RemoteFile
    try {
        $response = [System.Net.FtpWebResponse]$request.GetResponse()
        $stream = $response.GetResponseStream()
        $fileStream = [System.IO.File]::Open($localFile, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
        $stream.CopyTo($fileStream)
        $fileStream.Dispose()
        $stream.Dispose()
        $response.Dispose()

        $script:DownloadedFiles.Add((Normalize-RemotePath -Path $RemoteFile))
        Write-Host "[download]  $RemoteFile"
    }
    catch {
        throw "FTP download failed for '$RemoteFile': $($_.Exception.Message)"
    }
}

function Download-FtpDirectoryRecursive {
    param([string]$RemoteDir)

    $dirNorm = Normalize-RemotePath -Path $RemoteDir
    if (Should-ExcludeByPath -RemotePath $dirNorm) {
        Write-Host "[skip:path] $dirNorm"
        return
    }

    Write-Host "[scan]      $dirNorm"
    $items = Get-FtpListItems -RemotePath $dirNorm

    foreach ($item in $items) {
        $itemName = $item.Name
        if ($itemName -in @('.', '..')) { continue }

        $childRemote = Join-RemotePath -Base $dirNorm -Child $itemName
        if (Should-ExcludeByPath -RemotePath $childRemote) {
            Write-Host "[skip:path] $childRemote"
            continue
        }

        if ($item.IsDirectory -eq $true) {
            Download-FtpDirectoryRecursive -RemoteDir $childRemote
        }
        elseif ($item.IsDirectory -eq $false) {
            Download-FtpFile -RemoteFile $childRemote
        }
        elseif (Test-FtpDirectory -RemotePath $childRemote) {
            Download-FtpDirectoryRecursive -RemoteDir $childRemote
        }
        else {
            Download-FtpFile -RemoteFile $childRemote
        }
    }
}

function Resolve-WordPressRoot {
    param([string]$RequestedRoot)

    $root = Normalize-RemotePath -Path $RequestedRoot
    Write-Host "[check]     probing root $root"

    $entries = Get-FtpListItems -RemotePath $root
    $entryNames = @($entries | ForEach-Object { $_.Name })
    if ($entryNames -contains 'wp-config.php') {
        return $root
    }

    $candidates = @('public_html', 'www', 'htdocs', 'httpdocs')
    foreach ($candidate in $candidates) {
        if ($entryNames -contains $candidate) {
            $candidatePath = Join-RemotePath -Base $root -Child $candidate
            try {
                $candidateEntries = Get-FtpListItems -RemotePath $candidatePath
                $candidateNames = @($candidateEntries | ForEach-Object { $_.Name })
                if ($candidateNames -contains 'wp-config.php') {
                    Write-Host "[check]     detected wp root in $candidatePath"
                    return $candidatePath
                }
            }
            catch {
                continue
            }
        }
    }

    return $root
}

function Get-DownloadSummary {
    param([string]$BasePath)

    if (-not (Test-Path -LiteralPath $BasePath)) {
        return [pscustomobject]@{
            FileCount = 0
            TotalBytes = 0
        }
    }

    $files = @(Get-ChildItem -LiteralPath $BasePath -Recurse -File -ErrorAction SilentlyContinue)
    $totalBytes = [int64]0
    foreach ($file in $files) {
        $totalBytes += [int64]$file.Length
    }

    return [pscustomobject]@{
        FileCount = $files.Count
        TotalBytes = [int64]$totalBytes
    }
}

try {
    Ensure-LocalDirectory -Path $LocalRoot

    $resolvedRoot = Resolve-WordPressRoot -RequestedRoot $RemoteRoot
    $script:EffectiveRemoteRoot = $resolvedRoot
    Write-Host "[info]      remote root: $resolvedRoot"

    # 1) Download only top-level files from WP root
    $rootEntries = Get-FtpListItems -RemotePath $resolvedRoot
    foreach ($entry in $rootEntries) {
        $entryName = $entry.Name
        if ($entryName -in @('.', '..')) { continue }

        $remoteEntry = Join-RemotePath -Base $resolvedRoot -Child $entryName
        if ($entry.IsDirectory -eq $true) {
            continue
        }
        if ($entry.IsDirectory -eq $null -and (Test-FtpDirectory -RemotePath $remoteEntry)) {
            continue
        }

        Download-FtpFile -RemoteFile $remoteEntry
    }

    # 2) Download only the target theme recursively
    $themeRemoteDir = Join-RemotePath -Base $resolvedRoot -Child 'wp-content/themes/land76wp'
    if (-not (Test-FtpDirectory -RemotePath $themeRemoteDir)) {
        throw "Theme directory not found: $themeRemoteDir"
    }

    Download-FtpDirectoryRecursive -RemoteDir $themeRemoteDir

    $summary = Get-DownloadSummary -BasePath $LocalRoot
    $hasWpConfig = Test-Path -LiteralPath (Join-Path -Path $LocalRoot -ChildPath 'wp-config.php')
    $hasTheme = Test-Path -LiteralPath (Join-Path -Path $LocalRoot -ChildPath 'wp-content\\themes\\land76wp')

    Write-Host ''
    Write-Host '=== FTP minimal sync report ==='
    Write-Host ("Downloaded files: {0}" -f $summary.FileCount)
    Write-Host ("Total size (bytes): {0}" -f $summary.TotalBytes)
    Write-Host ("wp-config.php present: {0}" -f $hasWpConfig)
    Write-Host ("land76wp present: {0}" -f $hasTheme)
    Write-Host ("Skipped by path: {0}" -f $script:SkippedByPath.Count)
    Write-Host ("Skipped by extension: {0}" -f $script:SkippedByExt.Count)

    $report = [pscustomobject]@{
        host = $FtpHost
        remote_root = $resolvedRoot
        local_root = (Resolve-Path -LiteralPath $LocalRoot).Path
        downloaded_files = $script:DownloadedFiles
        skipped_by_path = $script:SkippedByPath
        skipped_by_extension = $script:SkippedByExt
        summary = $summary
        checks = [pscustomobject]@{
            wp_config_present = $hasWpConfig
            theme_present = $hasTheme
        }
        generated_at = (Get-Date).ToString('s')
    }

    $reportPath = Join-Path -Path $LocalRoot -ChildPath 'sync_report.json'
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Host ("Report: {0}" -f $reportPath)
}
catch {
    Write-Error $_
    exit 1
}


