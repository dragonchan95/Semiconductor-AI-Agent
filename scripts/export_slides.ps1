$ErrorActionPreference = 'Stop'
$semiRoot = Split-Path -Parent $PSScriptRoot
$semiPptx = Join-Path $semiRoot 'docs\G045_Semiconductor_Agent.pptx'
$semiPdf = Join-Path $semiRoot 'docs\G045_Semiconductor_Agent.pdf'
$semiPowerPoint = New-Object -ComObject PowerPoint.Application
$semiPresentation = $null
try {
    $semiPresentation = $semiPowerPoint.Presentations.Open($semiPptx, -1, 0, 0)
    $semiPresentation.SaveAs($semiPdf, 32)
    Write-Output "Exported PDF: $semiPdf"
} finally {
    if ($null -ne $semiPresentation) { $semiPresentation.Close() }
    if ($semiPowerPoint.Presentations.Count -eq 0) { $semiPowerPoint.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($semiPowerPoint)
}
