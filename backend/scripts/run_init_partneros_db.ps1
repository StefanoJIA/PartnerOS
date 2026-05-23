#Requires -Version 5.0
<#
.SYNOPSIS
  Creates PostgreSQL role + database `partneros` (user/pass partneros) using psql.
  Do NOT paste SQL into PowerShell; use this script or pgAdmin.

.USAGE
  cd backend
  # Set superuser password for local postgres (default superuser is often 'postgres'):
  $env:PGPASSWORD = "your_postgres_password"
  .\scripts\run_init_partneros_db.ps1

  Optional: -PsqlPath "C:\Program Files\PostgreSQL\16\bin\psql.exe"
#>
param(
  [string]$Host = "127.0.0.1",
  [string]$SuperUser = "postgres",
  [string]$SqlFile = "$PSScriptRoot\init_partneros_db.sql",
  [string]$PsqlPath = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SqlFile)) {
  Write-Error "Missing SQL file: $SqlFile"
}

function Find-Psql {
  if ($PsqlPath -and (Test-Path $PsqlPath)) { return $PsqlPath }
  $candidates = @(
    "psql",
    "C:\Program Files\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    "C:\Program Files\PostgreSQL\15\bin\psql.exe"
  )
  foreach ($c in $candidates) {
    if ($c -eq "psql") {
      $cmd = Get-Command psql -ErrorAction SilentlyContinue
      if ($cmd) { return $cmd.Source }
    } elseif (Test-Path $c) { return $c }
  }
  return $null
}

$psql = Find-Psql
if (-not $psql) {
  Write-Error @"
Could not find psql.exe. Install PostgreSQL client tools, or pass -PsqlPath.

You can still open init_partneros_db.sql in pgAdmin (Query Tool) and execute there.
"@
}

if (-not $env:PGPASSWORD) {
  Write-Warning "PGPASSWORD is not set. psql will prompt for password, or set: `$env:PGPASSWORD = '...'"
}

& $psql -h $Host -U $SuperUser -d postgres -v ON_ERROR_STOP=1 -f $SqlFile
if ($LASTEXITCODE -ne 0) {
  Write-Error "psql exited with code $LASTEXITCODE"
}

Write-Host "Done. Test with: psql -h $Host -U partneros -d partneros -c 'SELECT 1'"
