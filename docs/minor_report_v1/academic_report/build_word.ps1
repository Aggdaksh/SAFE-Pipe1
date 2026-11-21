param([string]$RepositoryRoot=(Get-Location).Path)
$ErrorActionPreference='Stop'
$artifactDir=Join-Path $RepositoryRoot 'docs/minor_report_v1/academic_report'
$data=Get-Content (Join-Path $artifactDir 'report_content.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$outDir=Join-Path $RepositoryRoot 'output/docx'
$qaDir=Join-Path $RepositoryRoot 'reports/_scratch/minor_actual_report_v1/word_render'
New-Item -ItemType Directory -Force $outDir,$qaDir | Out-Null
$finalPath=Join-Path $outDir 'SAFE_Pipe_DTU_Minor_Project_Report.docx'
$previewPath=Join-Path $qaDir 'SAFE_Pipe_DTU_Minor_Project_Report.pdf'
$word=$null;$doc=$null
function Add-Paragraph {
    param([string]$Text,[string]$Style='Normal',[int]$Align=-1,[bool]$Keep=$false)
    $start=$doc.Content.End-1
    $r=$doc.Range($start,$start)
    $r.InsertAfter($Text+"`r")
    $r=$doc.Range($start,$start+$Text.Length)
    $r.Style=$doc.Styles.Item($Style)
    if($Align -ge 0){$r.ParagraphFormat.Alignment=$Align}
    $r.ParagraphFormat.KeepWithNext=$(if($Keep){-1}else{0})
    return $r
}
function Add-Break {param([int]$Kind=7);$r=$doc.Range($doc.Content.End-1,$doc.Content.End-1);$r.InsertBreak($Kind)}
function Front-Title {param([string]$Text);$r=Add-Paragraph $Text 'Front Heading' 1 $true;$r.ParagraphFormat.SpaceAfter=24}
function Add-Image {
    param([string]$File,[double]$Width=450,[bool]$Keep=$true)
    $r=Add-Paragraph '' 'Normal' 1 $Keep
    $at=$doc.Range($r.Start,$r.Start)
    $shape=$doc.InlineShapes.AddPicture($File,$false,$true,$at)
    $shape.LockAspectRatio=-1
    $shape.Width=[single]$Width
    $shape.AlternativeText=[IO.Path]::GetFileNameWithoutExtension($File)
    return $shape
}
function Add-Caption {
    param([string]$Label,[string]$Title)
    $prefix=$Label+' '
    $r=Add-Paragraph ($prefix+'0  '+$Title) 'Caption' 1 $true
    $numberRange=$doc.Range($r.Start+$prefix.Length,$r.Start+$prefix.Length+1)
    [void]$doc.Fields.Add($numberRange,-1,('SEQ '+$Label+' \* ARABIC'),$false)
}
function Add-Table {
    param($Block)
    Add-Caption 'Table' $Block.title
    $r=$doc.Range($doc.Content.End-1,$doc.Content.End-1)
    $t=$doc.Tables.Add($r,$Block.rows.Count+1,$Block.headers.Count)
    $t.AllowAutoFit=$false
    $t.PreferredWidthType=3;$t.PreferredWidth=451.2
    $t.Borders.Enable=1
    $t.TopPadding=5;$t.BottomPadding=5;$t.LeftPadding=6;$t.RightPadding=6
    $t.Range.Font.Name='Times New Roman';$t.Range.Font.Size=10.5;$t.Range.Font.Color=0
    $t.Range.ParagraphFormat.LineSpacingRule=0
    $t.Range.ParagraphFormat.SpaceBefore=2;$t.Range.ParagraphFormat.SpaceAfter=2
    $t.Range.ParagraphFormat.KeepWithNext=0
    for($c=1;$c -le $Block.headers.Count;$c++){
        $t.Columns.Item($c).Width=[single](451.2*$Block.widths[$c-1])
        $t.Cell(1,$c).Range.Text=[string]$Block.headers[$c-1]
    }
    $t.Rows.Item(1).HeadingFormat=-1
    $t.Rows.Item(1).Range.Font.Bold=-1
    $t.Rows.Item(1).Shading.BackgroundPatternColor=15132390
    for($i=0;$i -lt $Block.rows.Count;$i++){
        for($j=0;$j -lt $Block.headers.Count;$j++){
            $cell=$t.Cell($i+2,$j+1)
            $cell.Range.Text=[string]$Block.rows[$i][$j]
            $cell.VerticalAlignment=1
            $cell.Range.ParagraphFormat.Alignment=0
        }
    }
    foreach($row in $t.Rows){$row.AllowBreakAcrossPages=0}
    $t.Range.InsertParagraphAfter()
    [void](Add-Paragraph '' 'Normal')
}
function Front-Field {
    param([string]$Code)
    $r=Add-Paragraph '' 'Normal'
    [void]$doc.Fields.Add($doc.Range($r.Start,$r.Start),-1,$Code,$false)
}
try {
    $word=New-Object -ComObject Word.Application
    if($word.Documents.Count -ne 0){throw 'New Word automation instance unexpectedly contains existing documents; stopping to preserve them.'}
    $word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3
    $doc=$word.Documents.Add()
    $word.Options.Pagination=$true
    $doc.PageSetup.PaperSize=7
    $doc.PageSetup.TopMargin=72;$doc.PageSetup.BottomMargin=72
    $doc.PageSetup.LeftMargin=72;$doc.PageSetup.RightMargin=72
    $doc.PageSetup.HeaderDistance=30;$doc.PageSetup.FooterDistance=30
    $normal=$doc.Styles.Item('Normal')
    $normal.Font.Name='Times New Roman';$normal.Font.Size=12;$normal.Font.Color=0
    $normal.ParagraphFormat.Alignment=3;$normal.ParagraphFormat.LineSpacingRule=1
    $normal.ParagraphFormat.SpaceAfter=6;$normal.ParagraphFormat.WidowControl=-1
    foreach($name in @('Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption','TOC 1','TOC 2','Table of Figures')){
        $s=$doc.Styles.Item($name);$s.Font.Name='Times New Roman';$s.Font.Color=0
        $s.ParagraphFormat.Borders.Enable=0
    }
    $doc.Styles.Item('Title').Font.Size=16;$doc.Styles.Item('Title').Font.Bold=-1
    $doc.Styles.Item('Heading 1').Font.Size=14;$doc.Styles.Item('Heading 1').Font.Bold=-1
    $doc.Styles.Item('Heading 1').ParagraphFormat.PageBreakBefore=-1
    $doc.Styles.Item('Heading 1').ParagraphFormat.SpaceAfter=18
    $doc.Styles.Item('Heading 2').Font.Size=12;$doc.Styles.Item('Heading 2').Font.Bold=-1
    $doc.Styles.Item('Heading 2').ParagraphFormat.SpaceBefore=12
    $doc.Styles.Item('Heading 2').ParagraphFormat.SpaceAfter=6
    $doc.Styles.Item('Heading 1').ParagraphFormat.KeepWithNext=-1
    $doc.Styles.Item('Heading 2').ParagraphFormat.KeepWithNext=-1
    $doc.Styles.Item('Caption').Font.Size=10.5
    $doc.Styles.Item('Caption').Font.Italic=0
    $doc.Styles.Item('Caption').ParagraphFormat.LineSpacingRule=0
    foreach($name in @('TOC 1','TOC 2','Table of Figures')){
        $s=$doc.Styles.Item($name);$s.Font.Size=10.5
        $s.ParagraphFormat.LineSpacingRule=0;$s.ParagraphFormat.SpaceAfter=4
    }
    $front=$doc.Styles.Add('Front Heading',1)
    $front.BaseStyle='Normal';$front.Font.Name='Times New Roman';$front.Font.Size=14;$front.Font.Bold=-1;$front.Font.Color=0
    $front.ParagraphFormat.OutlineLevel=10;$front.ParagraphFormat.LineSpacingRule=0
    $sourceStyle=$doc.Styles.Add('Source Note',1)
    $sourceStyle.BaseStyle='Normal';$sourceStyle.Font.Size=9;$sourceStyle.Font.Color=0
    $sourceStyle.ParagraphFormat.LineSpacingRule=0;$sourceStyle.ParagraphFormat.SpaceAfter=12
    $cover=$doc.Styles.Add('Cover Text',1);$cover.BaseStyle='Normal'
    $cover.Font.Name='Times New Roman';$cover.Font.Size=12;$cover.Font.Color=0
    $cover.ParagraphFormat.Alignment=1;$cover.ParagraphFormat.LineSpacingRule=0
    $cover.ParagraphFormat.SpaceAfter=7;$cover.ParagraphFormat.KeepWithNext=0
    [void](Add-Paragraph $data.title 'Title' 1)
    [void](Add-Paragraph 'MINOR BTECH PROJECT REPORT' 'Cover Text' 1)
    [void](Add-Paragraph "SUBMITTED IN PARTIAL FULFILMENT OF THE REQUIREMENTS`rFOR THE AWARD OF THE DEGREE OF" 'Cover Text' 1)
    $r=Add-Paragraph "BACHELOR OF TECHNOLOGY`rIN INFORMATION TECHNOLOGY" 'Cover Text' 1;$r.Font.Bold=-1
    [void](Add-Paragraph 'SUBMITTED BY' 'Cover Text' 1)
    foreach($member in $data.team){$r=Add-Paragraph ($member[0]+'    '+$member[1]) 'Cover Text' 1;$r.Font.Bold=-1}
    [void](Add-Paragraph ($data.semester+' | Academic Session '+$data.session) 'Cover Text' 1)
    [void](Add-Paragraph 'Under the supervision of' 'Cover Text' 1)
    $r=Add-Paragraph $data.guide 'Cover Text' 1;$r.Font.Bold=-1
    [void](Add-Paragraph 'Head of Department' 'Cover Text' 1)
    $shape=Add-Image $data.logo 91 $false
    $shape.Range.ParagraphFormat.SpaceAfter=8
    $r=Add-Paragraph 'DEPARTMENT OF INFORMATION TECHNOLOGY' 'Cover Text' 1;$r.Font.Bold=-1
    $r=Add-Paragraph 'DELHI TECHNOLOGICAL UNIVERSITY' 'Cover Text' 1;$r.Font.Bold=-1
    [void](Add-Paragraph "(Formerly Delhi College of Engineering)`rBawana Road, Delhi 110042" 'Cover Text' 1)
    [void](Add-Paragraph $data.date 'Cover Text' 1)
    Add-Break 2
    Front-Title 'CANDIDATES DECLARATION'
    [void](Add-Paragraph ('We, Daksh Aggarwal (23/IT/047), Ganant Awasthi (23/IT/055) and Chaitanya Singh (23/IT/045), students of B.Tech VII Semester in the Department of Information Technology, Delhi Technological University, hereby declare that the project report titled "'+$data.title+'" presents our project work submitted for the Minor BTech Project in the academic session 2026-2027.'))
    [void](Add-Paragraph 'The work and results of other authors have been acknowledged through references. This report has not been submitted in full for the award of another degree or diploma. The completed experiments, software verification and proposed future work are distinguished in the report.')
    [void](Add-Paragraph "Place: New Delhi`rDate: ____________________")
    foreach($member in $data.team){[void](Add-Paragraph ("`rSignature: ____________________`r"+$member[0]+' ('+$member[1]+')'))}
    Add-Break
    Front-Title 'CERTIFICATE'
    [void](Add-Paragraph ('This is to certify that the project report titled "'+$data.title+'", submitted by Daksh Aggarwal (23/IT/047), Ganant Awasthi (23/IT/055) and Chaitanya Singh (23/IT/045), Department of Information Technology, Delhi Technological University, in partial fulfilment of the requirements of the Minor BTech Project, B.Tech VII Semester, academic session 2026-2027, is a record of the project work carried out under my supervision.'))
    [void](Add-Paragraph 'The report is submitted for academic evaluation. The technical results, limitations and remaining work are described in the relevant chapters.')
    [void](Add-Paragraph "`r`rSignature: ____________________`rDate: ____________________`rPlace: New Delhi")
    [void](Add-Paragraph ("`r"+$data.guide+"`rHead of Department`rDepartment of Information Technology`rDelhi Technological University"))
    Add-Break
    Front-Title 'ACKNOWLEDGEMENT'
    [void](Add-Paragraph 'We express our gratitude to our project guide, Prof. Dinesh Kumar Vishwakarma, Head of Department, Department of Information Technology, Delhi Technological University, for the opportunity to undertake this project and for academic guidance. We thank the Department of Information Technology for the academic environment in which the project was developed.')
    [void](Add-Paragraph 'We acknowledge the open-source contributors to Dask, LightGBM and the scientific Python ecosystem whose software made the implementation and reproducible analysis possible. The research publications used to develop the technical background are cited in the report. We also thank our peers and project team members for discussions and coordination during the work.')
    foreach($member in $data.team){[void](Add-Paragraph ("`r"+$member[0]+' ('+$member[1]+')'))}
    Add-Break
    Front-Title 'ABSTRACT'
    [void](Add-Paragraph $data.abstract)
    [void](Add-Paragraph 'Keywords: Dask, configuration selection, runtime prediction, LightGBM, conformal calibration, memory pressure, execution profiling, abstention.')
    Add-Break
    Front-Title 'TABLE OF CONTENTS'
    Front-Field 'TOC \o "1-2" \h \z \u'
    Add-Break
    Front-Title 'LIST OF FIGURES'
    Front-Field 'TOC \h \z \c "Figure"'
    Add-Break
    Front-Title 'LIST OF TABLES'
    Front-Field 'TOC \h \z \c "Table"'
    Add-Break
    Front-Title 'LIST OF ABBREVIATIONS'
    foreach($entry in @('CLI - Command Line Interface','CPU - Central Processing Unit','DTU - Delhi Technological University','ETL - Extract Transform Load','GB - Gigabyte in decimal units','GiB - Gibibyte in binary units','JSONL - JSON Lines','MdAPE - Median Absolute Percentage Error','ML - Machine Learning','OOD - Out of Distribution','RAM - Random Access Memory','RSS - Resident Set Size','SLA - Service Level Agreement','SHA-256 - Secure Hash Algorithm with 256 bit output')){
        [void](Add-Paragraph $entry)
    }
    Add-Break 2
    $firstChapter=$true
    foreach($block in $data.blocks){
        switch($block.type){
            'heading' {
                $r=Add-Paragraph $block.text ('Heading '+$block.level) -Keep $true
                if($firstChapter){$r.ParagraphFormat.PageBreakBefore=0;$firstChapter=$false}
            }
            'paragraph' {[void](Add-Paragraph $block.text)}
            'equation' {
                $r=Add-Paragraph $block.text 'Normal' 1
                $r.Font.Name='Cambria Math';$r.Font.Size=11
                $math=$doc.OMaths.Add($r);$math.OMaths.Item(1).BuildUp()
            }
            'figure' {
                $width=451
                if($block.id -eq 'saved_advisor_output'){$width=420}
                $shape=Add-Image $block.file $width $true
                if($shape.Height -gt 340){$shape.Height=340}
                Add-Caption 'Figure' $block.title
                [void](Add-Paragraph $block.caption 'Source Note')
                [void](Add-Paragraph ('Source: '+$block.source) 'Source Note')
            }
            'table' {Add-Table $block}
        }
    }
    for($i=2;$i -le $doc.Sections.Count;$i++){
        $section=$doc.Sections.Item($i)
        $footer=$section.Footers.Item(1);$footer.LinkToPrevious=$false
        $footer.Range.Text='';$footer.Range.ParagraphFormat.Alignment=1
        $footer.Range.Font.Name='Times New Roman';$footer.Range.Font.Size=10;$footer.Range.Font.Color=0
        [void]$footer.PageNumbers.Add(1,$true)
        $footer.PageNumbers.RestartNumberingAtSection=$true
        $footer.PageNumbers.StartingNumber=1
        if($i -eq 2){$footer.PageNumbers.NumberStyle=2}else{$footer.PageNumbers.NumberStyle=0}
    }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    foreach($toc in $doc.TablesOfContents){$toc.Update()}
    foreach($tof in $doc.TablesOfFigures){$tof.Update()}
    $doc.Repaginate();$doc.Fields.Update() | Out-Null
    $doc.SaveAs2([string]$finalPath,16)
    $doc.SaveAs2([string]$previewPath,17)
    $summary=[ordered]@{word_version=$word.Version;pages=$doc.ComputeStatistics(2);words=$doc.ComputeStatistics(0);sections=$doc.Sections.Count;embedded_images=$doc.InlineShapes.Count;tables=$doc.Tables.Count;equations=$doc.OMaths.Count;contents_tables=$doc.TablesOfContents.Count;figure_lists=$doc.TablesOfFigures.Count;docx=$finalPath;preview_pdf=$previewPath}
    $summary | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $artifactDir 'word_build_result.json')
    $summary | ConvertTo-Json
} catch {
    Write-Output $_.Exception.ToString()
    Write-Output $_.ScriptStackTrace
    throw
} finally {
    $discard=0
    if($doc){$doc.Close([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
    if($word){$word.Quit([ref]$discard);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
