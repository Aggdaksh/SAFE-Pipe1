param([string]$RepositoryRoot=(Get-Location).Path)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$artifactDir=Join-Path $RepositoryRoot 'docs/minor_report_v1/academic_report'
$actual=Join-Path $RepositoryRoot 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx'
$preview=Join-Path $RepositoryRoot 'reports/_scratch/minor_actual_report_v1/word_render/SAFE_Pipe_DTU_Minor_Project_Report.pdf'
$archive=[IO.Compression.ZipFile]::Open($actual,[IO.Compression.ZipArchiveMode]::Update)
try{
    $entry=$archive.GetEntry('word/document.xml')
    $reader=[IO.StreamReader]::new($entry.Open());try{[xml]$xml=$reader.ReadToEnd()}finally{$reader.Dispose()}
    $ns=[Xml.XmlNamespaceManager]::new($xml.NameTable)
    $ns.AddNamespace('m','http://schemas.openxmlformats.org/officeDocument/2006/math')
    $ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    $first=$xml.SelectSingleNode('//m:oMath',$ns)
    if(-not $first.InnerText.Contains('MdAPE')){throw 'Expected MdAPE as the first equation.'}
    [xml]$correct=Get-Content (Join-Path $artifactDir 'mdape.omml.xml') -Raw -Encoding UTF8
    [void]$first.ParentNode.ReplaceChild($xml.ImportNode($correct.DocumentElement,$true),$first)
    foreach($node in $xml.SelectNodes('//w:t',$ns)){
        $node.InnerText=$node.InnerText.Replace('The previously discussed approximately 6.78 GiB','In the earlier development screen, approximately 6.78 GiB')
        $node.InnerText=$node.InnerText.Replace('Do not silently change fitted feature values to make the unit labels look more convenient; refer to docs/DATA_DICTIONARY.md.','The historical feature contract is retained to maintain compatibility with the saved model, as documented in the data dictionary.')
    }
    $body=$xml.SelectSingleNode('//w:body',$ns)
    $storage=@($body.SelectNodes('w:p',$ns) | Where-Object { $_.InnerText.StartsWith('In the earlier development screen, approximately 6.78 GiB') })
    foreach($p in $storage){[void]$body.InsertBefore($p,$body.SelectSingleNode('w:sectPr',$ns))}
    $entry.Delete();$entry=$archive.CreateEntry('word/document.xml')
    $writer=[IO.StreamWriter]::new($entry.Open(),[Text.UTF8Encoding]::new($false))
    try{$writer.Write($xml.OuterXml)}finally{$writer.Dispose()}
}finally{$archive.Dispose()}
$word=$null;$doc=$null
try{
    $word=New-Object -ComObject Word.Application
    if($word.Documents.Count -ne 0){throw 'Existing documents in automation instance; stopped to preserve them.'}
    $word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3
    $doc=$word.Documents.Open([string]$actual)
    $doc.Styles.Item('Source Note').ParagraphFormat.Alignment=0
    foreach($t in $doc.Tables){
        $t.Rows.Item(1).Range.ParagraphFormat.Alignment=0
        for($i=1;$i -lt $t.Rows.Count;$i++){$t.Rows.Item($i).Range.ParagraphFormat.KeepWithNext=-1}
        $t.Rows.Item($t.Rows.Count).Range.ParagraphFormat.KeepWithNext=0
    }
    foreach($p in $doc.Paragraphs){
        if($p.Range.Text -match '^\[\d+\]'){$p.Range.ParagraphFormat.Alignment=0}
    }
    $doc.Fields.Update() | Out-Null;$doc.Repaginate()
    foreach($toc in $doc.TablesOfContents){$toc.Update()}
    foreach($tof in $doc.TablesOfFigures){$tof.Update()}
    $doc.Repaginate();$doc.Save()
    $doc.SaveAs2([string]$preview,17)
    $summary=[ordered]@{word_version=$word.Version;pages=$doc.ComputeStatistics(2);words=$doc.ComputeStatistics(0);sections=$doc.Sections.Count;embedded_images=$doc.InlineShapes.Count;tables=$doc.Tables.Count;equations=$doc.OMaths.Count;contents_tables=$doc.TablesOfContents.Count;figure_lists=$doc.TablesOfFigures.Count;docx=$actual;preview_pdf=$preview}
    $summary | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $artifactDir 'word_build_result.json')
    $summary | ConvertTo-Json
}finally{
    $discard=0
    if($doc){$doc.Close([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
    if($word){$word.Quit([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
