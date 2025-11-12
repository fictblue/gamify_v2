# Create directories
$webClient = New-Object System.Net.WebClient

# Download Font Awesome CSS
$fontAwesomeVersion = "6.0.0"
$baseUrl = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/$fontAwesomeVersion/"

# Create webfonts directory
$webfontsDir = "static/vendor/font-awesome/webfonts"
New-Item -ItemType Directory -Force -Path $webfontsDir | Out-Null

# Download CSS
Write-Host "Downloading Font Awesome CSS..."
$cssUrl = "${baseUrl}css/all.min.css"
$cssPath = "static/vendor/font-awesome/css/all.min.css"
$webClient.DownloadFile($cssUrl, $cssPath)

# List of webfont files to download
$webfonts = @(
    "webfonts/fa-solid-900.woff2",
    "webfonts/fa-solid-900.ttf",
    "webfonts/fa-regular-400.woff2",
    "webfonts/fa-regular-400.ttf",
    "webfonts/fa-brands-400.woff2",
    "webfonts/fa-brands-400.ttf"
)

# Download each webfont file
foreach ($font in $webfonts) {
    $fontUrl = "${baseUrl}${font}"
    $fontPath = "static/vendor/font-awesome/${font}"
    $fontDir = [System.IO.Path]::GetDirectoryName($fontPath)
    
    # Create directory if it doesn't exist
    if (-not (Test-Path $fontDir)) {
        New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
    }
    
    Write-Host "Downloading $font..."
    try {
        $webClient.DownloadFile($fontUrl, $fontPath)
    } catch {
        Write-Warning "Failed to download $font : $_"
    }
}

Write-Host "Font Awesome download complete!"
