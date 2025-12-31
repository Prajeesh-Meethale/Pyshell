# PyShell Automation Script
param([string]$pythonCode)
$repoPath = "C:\Users\Prajeesh\Shell Py"
Set-Content -Path "$repoPath\app\main.py" -Value $pythonCode -Encoding UTF8
cd $repoPath
git add app/main.py
git commit -m "automated update"
git push origin master
Write-Host "✓ Code pushed successfully"
Write-Host "✓ Update complete"