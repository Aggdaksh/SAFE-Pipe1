param(
 [string]$OutputPath='output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Evidence_Reviewed.docx',
 [string]$QaDirectory='reports/_scratch/report_evidence_v2',
 [string]$Python='python'
)
$ErrorActionPreference='Stop'
$root=(Get-Location).Path
$out=[IO.Path]::GetFullPath((Join-Path $root $OutputPath))
$qa=[IO.Path]::GetFullPath((Join-Path $root $QaDirectory))
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $qa)){throw 'Output or QA directory exists; use new paths.'}
& $Python 'docs/report_integrity_review_v1/build_evidence_docx.py' --out $out
if($LASTEXITCODE -ne 0){throw 'Document preparation failed'}
New-Item -ItemType Directory -Path $qa | Out-Null
$word=$null;$doc=$null;$discard=0
try{
 $word=New-Object -ComObject Word.Application
 if($word.Documents.Count -ne 0){throw 'Preserve existing automation documents.'}
 $word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3
 $doc=$word.Documents.Open([string]$out)
 $doc.Fields.Update() | Out-Null
 $doc.Repaginate()
 foreach($toc in $doc.TablesOfContents){$toc.Update()}
 foreach($tof in $doc.TablesOfFigures){$tof.Update()}
 $doc.Repaginate();$doc.Save()
 $summary=[ordered]@{pages=$doc.ComputeStatistics(2);images=$doc.InlineShapes.Count;tables=$doc.Tables.Count;equations=$doc.OMaths.Count;word_version=$word.Version;output=$OutputPath}
 $doc.SaveAs2([string](Join-Path $qa 'report.pdf'),17)
}finally{
 if($doc){$doc.Close([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
 if($word -and $word.Documents.Count -eq 0){$word.Quit([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
$summary.sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qa 'word_result.json') -Encoding UTF8
$summary | ConvertTo-Json
