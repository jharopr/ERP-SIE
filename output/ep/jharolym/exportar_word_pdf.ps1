param([string]$DocxPath, [string]$PdfPath)
$ErrorActionPreference = 'Stop'
$wordForRender = $null
$documentForRender = $null
try {
    $wordForRender = New-Object -ComObject Word.Application
    $wordForRender.Visible = $false
    $wordForRender.DisplayAlerts = 0
    $wordForRender.AutomationSecurity = 3
    $documentForRender = $wordForRender.Documents.Open($DocxPath, $false, $true, $false)
    $documentForRender.ExportAsFixedFormat($PdfPath, 17)
    Write-Output ('Paginas exportadas: ' + $documentForRender.ComputeStatistics(2))
}
finally {
    if ($null -ne $documentForRender) { $documentForRender.Close(0) }
    if ($null -ne $wordForRender) { $wordForRender.Quit() }
}
