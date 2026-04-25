$root = "c:\Users\mpro\Desktop\mprnew\mpr-main"
$files = Get-ChildItem -Path $root -Recurse -Filter "index.html" | Where-Object { $_.FullName -notlike "*\local\*" }

$replacements = @(
    @{ old = "Home is where the monk lives"; new = "Home is where the Prozesy lives" }
    @{ old = "An overview of the Monk family"; new = "An overview of the Prozesy family" }
    @{ old = "Be a <span class=`"brand-bh2`">Monk!</span>"; new = "Be a <span class=`"brand-bh2`">Prozesy!</span>" }
)

$count = 0
foreach ($file in $files) {
    $content = [IO.File]::ReadAllText($file.FullName)
    $changed = $false
    
    foreach ($rep in $replacements) {
        if ($content.Contains($rep.old)) {
            $content = $content.Replace($rep.old, $rep.new)
            $changed = $true
        }
    }
    
    if ($changed) {
        [IO.File]::WriteAllText($file.FullName, $content, [System.Text.Encoding]::UTF8)
        Write-Host "Updated: $($file.FullName.Replace($root, ''))"
        $count++
    }
}

Write-Host "`nTotal files updated: $count" -ForegroundColor Green
