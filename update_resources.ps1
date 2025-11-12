# Create necessary directories
$fontAwesomeDir = ".\static\vendor\fontawesome"
$chartJsDir = ".\static\vendor\chartjs"

New-Item -ItemType Directory -Force -Path $fontAwesomeDir
New-Item -ItemType Directory -Force -Path $chartJsDir

# Download Font Awesome CSS
$fontAwesomeUrl = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
$fontAwesomeCss = "$fontAwesomeDir\font-awesome.min.css"
Invoke-WebRequest -Uri $fontAwesomeUrl -OutFile $fontAwesomeCss

# Download Font Awesome Webfonts (example - you might need more font files)
$fontAwesomeWebfontUrl = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2"
$fontAwesomeWebfontDir = "$fontAwesomeDir\webfonts"
New-Item -ItemType Directory -Force -Path $fontAwesomeWebfontDir
Invoke-WebRequest -Uri $fontAwesomeWebfontUrl -OutFile "$fontAwesomeWebfontDir\fa-solid-900.woff2"

# Download Chart.js
$chartJsUrl = "https://cdn.jsdelivr.net/npm/chart.js"
Invoke-WebRequest -Uri "$chartJsUrl/dist/chart.min.js" -OutFile "$chartJsDir\chart.min.js"

# Download Chart.js Matrix plugin
$chartMatrixUrl = "https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.1.1/dist/chartjs-chart-matrix.min.js"
Invoke-WebRequest -Uri $chartMatrixUrl -OutFile "$chartJsDir\chartjs-chart-matrix.min.js"

Write-Host "Resources have been downloaded successfully!"
