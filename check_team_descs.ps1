$pages = @('bitas-pramanik','mehdi-hasan-soikot','mostafizur-rahman','nahid-islam','olivia-jade','rahmatullah-onu','rahul-roy','tasfeen-nayem','yash-vardhan')
foreach ($p in $pages) {
    $f = "c:\Users\mpro\Desktop\mprnew\mpr-main\$p\index.html"
    $c = [IO.File]::ReadAllText($f)
    $m = [regex]::Match($c, 'content="([^"]+)"\s+name="description"')
    if (-not $m.Success) { $m = [regex]::Match($c, 'name="description"\s+content="([^"]+)"') }
    Write-Host "${p}: $($m.Groups[1].Value)"
}
