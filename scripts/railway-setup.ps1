# BotFin Railway setup script
# Run: powershell -ExecutionPolicy Bypass -File scripts/railway-setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

function New-Secret([int]$bytes = 32) {
    $b = New-Object byte[] $bytes
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    return [Convert]::ToBase64String($b).TrimEnd('=').Replace('+', 'x').Replace('/', 'y')
}

$jwt = New-Secret
$nextauth = New-Secret
$deepseek = ""

$envFile = Join-Path $root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*DEEPSEEK_API_KEY=(.+)$') { $deepseek = $matches[1].Trim() }
    }
}

Write-Host ""
Write-Host "=== BotFin Railway setup ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repo: https://github.com/nkiparenko1/BotFin"
Write-Host "New project: https://railway.com/new"
Write-Host "Pgvector DB: https://railway.com/deploy/postgres-with-pgvector-engine"
Write-Host ""
Write-Host "Service names (required for variable references):"
Write-Host "  Postgres, BotFin, Frontend"
Write-Host "Root directories: backend, frontend"
Write-Host "Deploy order: Postgres -> Backend -> Frontend"
Write-Host ""

$ref = '${{'
$backendLines = @(
    "DATABASE_URL=$ref" + "Postgres.DATABASE_URL}}"
    "ENV=production"
    "JWT_SECRET=$jwt"
    "JWT_ACCESS_EXPIRE_MINUTES=15"
    "JWT_REFRESH_EXPIRE_DAYS=30"
    "CORS_ORIGINS=https://$ref" + "Frontend.RAILWAY_PUBLIC_DOMAIN}}"
    "DEEPSEEK_API_KEY=$deepseek"
    "DEEPSEEK_BASE_URL=https://api.deepseek.com"
    "DEEPSEEK_CHAT_MODEL=deepseek-chat"
    "DEEPSEEK_EMBEDDING_MODEL=deepseek-embedding"
)

$frontendLines = @(
    "NEXTAUTH_URL=https://$ref" + "Frontend.RAILWAY_PUBLIC_DOMAIN}}"
    "NEXTAUTH_SECRET=$nextauth"
    "NEXT_PUBLIC_API_URL=https://$ref" + "BotFin.RAILWAY_PUBLIC_DOMAIN}}"
    "INTERNAL_API_URL=http://$ref" + "BotFin.RAILWAY_PRIVATE_DOMAIN}}:$ref" + "BotFin.PORT}}"
)

Write-Host "=== BACKEND (Raw Editor) ===" -ForegroundColor Green
$backendLines | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host "=== FRONTEND (Raw Editor) ===" -ForegroundColor Green
$frontendLines | ForEach-Object { Write-Host $_ }
Write-Host ""

if (-not $deepseek) {
    Write-Host "WARN: DEEPSEEK_API_KEY missing in .env" -ForegroundColor Red
}

$outDir = Join-Path $root "scripts\railway"
$outBackend = Join-Path $outDir "backend.generated.env"
$outFrontend = Join-Path $outDir "frontend.generated.env"
$backendLines | Out-File -FilePath $outBackend -Encoding utf8
$frontendLines | Out-File -FilePath $outFrontend -Encoding utf8
Write-Host "Saved to (do not commit):"
Write-Host "  $outBackend"
Write-Host "  $outFrontend"

try {
    Start-Process "https://railway.com/new"
} catch {
    Write-Host "Open https://railway.com/new manually"
}
