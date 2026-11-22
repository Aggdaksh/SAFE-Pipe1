$ErrorActionPreference='Stop'
$root=(Get-Location).Path
$base=Join-Path $root 'docs/report_integrity_review_v1'
$target=Join-Path $root 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx'
$qa=Join-Path $root 'reports/_scratch/report_revision_v1'
$backup=Join-Path $qa 'before_editorial_corrections.docx'
if(Test-Path -LiteralPath $backup){throw 'Backup already exists; inspect before repeating.'}
Copy-Item -LiteralPath $target -Destination $backup
Copy-Item -LiteralPath (Join-Path $qa 'reviewed.pdf') -Destination (Join-Path $qa 'before_editorial_corrections.pdf')
$plan=Get-Content -LiteralPath (Join-Path $base 'editorial_corrections.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$word=$null;$doc=$null;$discard=0
try{
 $word=New-Object -ComObject Word.Application
 if($word.Documents.Count -ne 0){throw 'Existing documents in automation instance'}
 $word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3
 $doc=$word.Documents.Open([string]$target)
 $operations=@();$guideCount=0
 foreach($p in $doc.Paragraphs){
  $txt=$p.Range.Text.TrimEnd([char]13,[char]7)
  foreach($edit in $plan.edits){if($txt -ceq $edit.before){$operations+=@{range=$p.Range.Duplicate;after=[string]$edit.after;before=$txt}}}
  if($txt -ceq 'Prof. Dinesh Kumar Vishwakarma'){
   $guideCount++
   if($guideCount -eq 2){$operations+=@{range=$p.Range.Duplicate;after="Prof. Dinesh Kumar Vishwakarma`rProject Supervisor";before=$txt}}
  }
 }
 if($operations.Count -ne ($plan.edits.Count+1)){throw 'Unexpected edit matches'}
 foreach($op in ($operations | Sort-Object {$_.range.Start} -Descending)){
  $r=$op.range
  if($op.after -eq ''){[void]$r.Delete()}else{$r.End=$r.End-1;$r.Text=$op.after}
 }
 $doc.Fields.Update() | Out-Null
 foreach($toc in $doc.TablesOfContents){$toc.Update()}
 foreach($tof in $doc.TablesOfFigures){$tof.Update()}
 $doc.Repaginate();$doc.Save()
 $doc.SaveAs2([string](Join-Path $qa 'reviewed.pdf'),17)
}finally{
 if($doc){$doc.Close([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
 if($word -and $word.Documents.Count -eq 0){$word.Quit([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
