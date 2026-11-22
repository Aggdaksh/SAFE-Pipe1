param([string]$RepositoryRoot=(Get-Location).Path)
$ErrorActionPreference='Stop'
$dir=Join-Path $RepositoryRoot 'docs/report_integrity_review_v1'
$source=Join-Path $RepositoryRoot 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx'
$target=Join-Path $RepositoryRoot 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx'
$qa=Join-Path $RepositoryRoot 'reports/_scratch/report_revision_v1'
if(Test-Path -LiteralPath $target){throw 'Reviewed output exists; preserve it and choose a new version.'}
New-Item -ItemType Directory -Force -Path $qa | Out-Null
$before=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$plan=Get-Content -LiteralPath (Join-Path $dir 'revision_plan.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$word=$null;$doc=$null
try{
 $word=New-Object -ComObject Word.Application
 if($word.Documents.Count -ne 0){throw 'Automation instance has existing documents; preserve them.'}
 $word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3
 $doc=$word.Documents.Open([string]$source,$false,$true)
 $doc.SaveAs2([string]$target,16)
 $applied=@()
 foreach($edit in $plan.edits){
  $matches=@()
  foreach($p in $doc.Paragraphs){if($p.Range.Text.TrimEnd([char]13,[char]7) -ceq $edit.before){$matches+= $p.Range.Duplicate}}
  if($matches.Count -ne 1){throw "Expected one paragraph for $($edit.id), found $($matches.Count)"}
  $r=$matches[0];$r.End=$r.End-1;$r.Text=[string]$edit.after
  $applied+= $edit.id
 }
 $end=$doc.Content.Duplicate;$end.Collapse(0)
 $end.InsertBefore("`r" + [string]$plan.disclosure + "`r")
 $doc.Fields.Update() | Out-Null
 foreach($toc in $doc.TablesOfContents){$toc.Update()}
 foreach($tof in $doc.TablesOfFigures){$tof.Update()}
 $doc.Repaginate();$doc.Save()
 $pages=$doc.ComputeStatistics(2)
 $doc.SaveAs2([string](Join-Path $qa 'reviewed.pdf'),17)
 $summary=[ordered]@{source_sha256=$before;pages=$pages;applied_edits=$applied;disclosure_added=$true;word_version=$word.Version;images=$doc.InlineShapes.Count;tables=$doc.Tables.Count;equations=$doc.OMaths.Count}
}finally{
 $discard=0
 if($doc){$doc.Close([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
 if($word -and $word.Documents.Count -eq 0){$word.Quit([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
$summary.reviewed_sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
$summary.source_preserved=((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -eq $before)
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $dir 'revision_receipt.json') -Encoding UTF8
