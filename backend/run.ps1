$ErrorActionPreference = 'Stop'
$backend = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $backend
$uvicornArgs = @('app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
if (Test-Path -LiteralPath '.env') {
    $uvicornArgs += @('--env-file', '.env')
}
python -m uvicorn @uvicornArgs
