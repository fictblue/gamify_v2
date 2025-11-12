# Create a WebClient object
$webClient = New-Object System.Net.WebClient

# Download Chart.js
Write-Host "Downloading Chart.js..."
$chartJsUrl = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"
$chartJsPath = "static/vendor/chartjs/chart.umd.min.js"
$webClient.DownloadFile($chartJsUrl, $chartJsPath)

# Download Chart.js Matrix plugin
Write-Host "Downloading Chart.js Matrix plugin..."
$matrixPluginUrl = "https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.1.1/dist/chartjs-chart-matrix.min.js"
$matrixPluginPath = "static/vendor/chartjs-chart-matrix/chartjs-chart-matrix.min.js"
$webClient.DownloadFile($matrixPluginUrl, $matrixPluginPath)

# Download Chart.js Annotation plugin
Write-Host "Downloading Chart.js Annotation plugin..."
$annotationPluginUrl = "https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@2.2.1/dist/chartjs-plugin-annotation.min.js"
$annotationPluginPath = "static/vendor/chartjs-plugin-annotation/chartjs-plugin-annotation.min.js"
$webClient.DownloadFile($annotationPluginUrl, $annotationPluginPath)

# Download Font Awesome CSS
Write-Host "Downloading Font Awesome..."
$fontAwesomeCssUrl = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
$fontAwesomeCssPath = "static/vendor/font-awesome/css/all.min.css"
$webClient.DownloadFile($fontAwesomeCssUrl, $fontAwesomeCssPath)

Write-Host "All resources downloaded successfully!"
