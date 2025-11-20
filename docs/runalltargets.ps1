$targets = @(
    'dirhtml',
    'singlehtml', 
    'pickle',
    'json',
    'htmlhelp',
    'qthelp',
    'devhelp',
    'epub',
    'latex',
    'text',
    'man',
    'texinfo',
    'gettext',
    'changes',
    'xml',
    'pseudoxml',
    'linkcheck',
    'doctest',
    'coverage'
)

foreach ($target in $targets) {
    Write-Host "Executing: ./make.bat $target" -ForegroundColor Cyan
    & ./make.bat $target
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error executing make.bat with target: $target (Exit code: $LASTEXITCODE)" -ForegroundColor Red
    }
}

Write-Host "`nAll targets completed." -ForegroundColor Green