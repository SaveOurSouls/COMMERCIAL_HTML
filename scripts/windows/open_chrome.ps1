param(
    [string]$Url = "http://127.0.0.1:8000"
)

$chromeCandidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)

$chromePath = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chromePath) {
    Start-Process -FilePath $chromePath -ArgumentList $Url
}
else {
    # Fallback to default browser if Chrome is not installed.
    Start-Process $Url
}
