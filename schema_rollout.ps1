$base = 'c:\Users\mpro\Desktop\mprnew\mpr-main'
$files = Get-ChildItem -Path $base -Recurse -Filter index.html
$changed = 0

function Get-Canonical($content) {
    if ($content -match 'rel="canonical"\s+href="([^"]+)"') { return $matches[1] }
    if ($content -match 'href="([^"]+)"\s+rel="canonical"') { return $matches[1] }
    return ''
}

function Get-Title($content) {
    if ($content -match '<title>(.*?)</title>') { return $matches[1] }
    return ''
}

function Get-Desc($content) {
    if ($content -match 'name="description"\s+content="([^"]*)"') { return $matches[1] }
    if ($content -match 'content="([^"]*)"\s+name="description"') { return $matches[1] }
    return ''
}

function Ensure-Schema($content, $marker, $json) {
    if ($content -match [regex]::Escape($marker)) { return $content }
    $block = "        <script type=`"application/ld+json`">`n$json`n        </script>`n"
    return [regex]::Replace($content, '</head>', ($block + '    </head>'), 1)
}

foreach ($f in $files) {
    $path = $f.FullName
    $rel = $path.Substring($base.Length + 1)
    $content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    $orig = $content

    $canonical = Get-Canonical $content
    if ($canonical -eq '') { continue }

    $title = (Get-Title $content).Replace('"', '\\"')
    $desc = (Get-Desc $content).Replace('"', '\\"')

    if ($rel -match '^blog\\.+\\index\.html$' -and $rel -ne 'blog\index.html') {
        $article = @"
        {
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": "$title",
          "description": "$desc",
          "mainEntityOfPage": "$canonical",
          "author": {"@type":"Organization","name":"Prozesy Media"},
          "publisher": {"@type":"Organization","name":"Prozesy Media"}
        }
"@
        $content = Ensure-Schema $content '"@type": "Article"' $article
    }

    if (($rel -match '^services\\.+\\index\.html$') -or ($rel -match '^(meta-ads|google-ads|seo-optimization|ui-ux|web-app-development|branding-design|tiktok-ads)\\index\.html$')) {
        $service = @"
        {
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "$title",
          "description": "$desc",
          "url": "$canonical",
          "provider": {"@type":"Organization","name":"Prozesy Media"}
        }
"@
        $content = Ensure-Schema $content '"@type": "Service"' $service
    }

    if ($rel -match '^products\\.+\\index\.html$' -and $rel -ne 'products\index.html') {
        $product = @"
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "$title",
          "description": "$desc",
          "url": "$canonical"
        }
"@
        $content = Ensure-Schema $content '"@type": "Product"' $product
    }

    if ($rel -match '^(biplop-sharkar|bitas-pramanik|mehdi-hasan-soikot|mostafizur-rahman|nahid-islam|olivia-jade|rahmatullah-onu|rahul-roy|tasfeen-nayem|yash-vardhan)\\index\.html$') {
        $personName = ($title.Split('|')[0]).Trim()
        $person = @"
        {
          "@context": "https://schema.org",
          "@type": "Person",
          "name": "$personName",
          "url": "$canonical",
          "worksFor": {"@type":"Organization","name":"Prozesy Media"}
        }
"@
        $content = Ensure-Schema $content '"@type": "Person"' $person
    }

    if ($rel -match '^projects\\.+\\index\.html$' -and $rel -ne 'projects\index.html') {
        $creative = @"
        {
          "@context": "https://schema.org",
          "@type": "CreativeWork",
          "name": "$title",
          "description": "$desc",
          "url": "$canonical"
        }
"@
        $content = Ensure-Schema $content '"@type": "CreativeWork"' $creative
    }

    if ($content -ne $orig) {
        [System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
        $changed++
    }
}

Write-Host "Schema updated files: $changed"
