$slugs = @('peacock-app-ui-concept','monkshub-the-ultimate-online-learning-framer-template','neuraflow-ai-automated-business-website-figma-design','3d-cryptocurrency-icon-set','ai-mental-health-app-ui-kit','cryptocurrency-app-ui-design','hello-fresh-meal-delivery-app-ui-design')
foreach ($s in $slugs) {
    $f = "c:\Users\mpro\Desktop\mprnew\mpr-main\products\$s\index.html"
    $c = [IO.File]::ReadAllText($f)
    $m = [regex]::Match($c, 'content="([^"]+)"\s+name="description"')
    $d = $m.Groups[1].Value
    Write-Host "$s ($($d.Length)): $d"
}
