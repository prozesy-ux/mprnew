$base = "c:\Users\mpro\Desktop\mprnew\mpr-main"
$files = Get-ChildItem -Path $base -Recurse -Filter index.html
$updated = 0

function Get-CanonicalUrl([string]$content) {
    if ($content -match 'rel="canonical"\s+href="([^"]+)"') { return $matches[1] }
    if ($content -match 'href="([^"]+)"\s+rel="canonical"') { return $matches[1] }
    return ""
}

function Get-TagContent([string]$content, [string]$pattern) {
    if ($content -match $pattern) { return $matches[1] }
    return ""
}

function Add-Or-Replace-MetaDescription([string]$content, [string]$desc) {
    $escaped = $desc -replace '&', '&amp;'
    if ($content -match 'name="description"') {
        $content = [regex]::Replace($content, '<meta\s+name="description"\s+content="[^"]*"\s*/>', ('<meta content="' + $escaped + '" name="description"/>'))
        $content = [regex]::Replace($content, '<meta\s+content="[^"]*"\s+name="description"\s*/>', ('<meta content="' + $escaped + '" name="description"/>'))
    } else {
        $content = $content -replace '(<meta charset="utf-8"/>)', ('`$1`n        <meta content="' + $escaped + '" name="description"/>')
    }
    if ($content -match 'property="og:description"') {
        $content = [regex]::Replace($content, '<meta\s+content="[^"]*"\s+property="og:description"\s*/>', ('<meta content="' + $escaped + '" property="og:description"/>'))
    } else {
        $content = $content -replace '(<meta\s+content="[^"]*"\s+property="og:title"\s*/>)', ('`$1`n        <meta content="' + $escaped + '" property="og:description"/>')
    }
    if ($content -match 'property="twitter:description"') {
        $content = [regex]::Replace($content, '<meta\s+content="[^"]*"\s+property="twitter:description"\s*/>', ('<meta content="' + $escaped + '" property="twitter:description"/>'))
    } else {
        $content = $content -replace '(<meta\s+content="[^"]*"\s+property="twitter:title"\s*/>)', ('`$1`n        <meta content="' + $escaped + '" property="twitter:description"/>')
    }
    return $content
}

function Ensure-JsonLdBlock([string]$content, [string]$typeMarker, [string]$json) {
    if ($content -match [regex]::Escape($typeMarker)) { return $content }
    $block = "        <script type=""application/ld+json"">`n$json`n        </script>`n"
    return $content -replace '(</head>)', "$block`$1"
}

function Build-BreadcrumbJson([string]$url, [string]$title) {
    $u = $url.TrimEnd('/')
    if (-not $u.StartsWith('http')) { return "" }
    $path = ($u -replace '^https?://[^/]+','').Trim('/')
    $parts = @()
    if ($path -ne "") { $parts = $path.Split('/') }

    $items = @()
    $items += '            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.prozesy.com/"}'
    $acc = ""
    $pos = 2
    foreach ($p in $parts) {
        $acc += "/$p"
        $name = ($p -replace '-', ' ')
        $name = (Get-Culture).TextInfo.ToTitleCase($name)
        $items += "            {""@type"":""ListItem"",""position"":$pos,""name"":""$name"",""item"":""https://www.prozesy.com$acc/""}"
        $pos++
    }

    return @"
        {
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          "itemListElement": [
$($items -join ",`n")
          ]
        }
"@
}

$industryMap = @{
    "ai-machine-learning" = "AI and Machine Learning"
    "automotive" = "Automotive"
    "beauty-cosmetics" = "Beauty and Cosmetics"
    "business-consulting" = "Business Consulting"
    "construction" = "Construction"
    "cybersecurity" = "Cybersecurity"
    "ecrm-portals" = "eCRM Portals"
    "edtech" = "EdTech"
    "electronics" = "Electronics"
    "entertainment" = "Entertainment"
    "event-management" = "Event Management"
    "fashion-apparel" = "Fashion and Apparel"
    "fintech" = "Fintech"
    "fitness-gym" = "Fitness and Gym"
    "food-beverages" = "Food and Beverages"
    "gaming" = "Gaming"
    "healthtech-startups" = "HealthTech Startups"
    "hotel-management" = "Hotel Management"
    "insurance" = "Insurance"
    "it-solutions" = "IT Solutions"
    "legal-services" = "Legal Services"
    "mental-health-services" = "Mental Health Services"
    "on-demand-services" = "On-Demand Services"
    "portfolio" = "Portfolio"
    "real-estate" = "Real Estate"
    "renewable-energy" = "Renewable Energy"
    "saas" = "SaaS"
    "social-media-platforms" = "Social Media Platforms"
    "tourism" = "Tourism"
    "transportation-logistics" = "Transportation and Logistics"
}

foreach ($f in $files) {
    $path = $f.FullName
    $rel = $path.Replace($base + "\\", "")
    $content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    $original = $content

    $title = Get-TagContent $content '<title>(.*?)</title>'
    $desc = Get-TagContent $content 'name="description"\s+content="([^"]*)"'
    if ($desc -eq "") { $desc = Get-TagContent $content 'content="([^"]*)"\s+name="description"' }
    $canonical = Get-CanonicalUrl $content

    # 1) Fill missing meta description for policy/legal pages
    if ($rel -eq 'privacy-policy\index.html' -and $desc -eq "") {
        $desc = "Read Prozesy Media privacy policy to understand how we collect, use, and protect your personal data."
        $content = Add-Or-Replace-MetaDescription $content $desc
    }
    if ($rel -eq 'terms-and-condition\index.html' -and $desc -eq "") {
        $desc = "Review Prozesy Media terms and conditions for use of our website, services, and legal policies."
        $content = Add-Or-Replace-MetaDescription $content $desc
    }

    # 2) Industry content de-duplication and self-link fix
    if ($rel -like 'industry\*\index.html' -and $rel -ne 'industry\index.html') {
        $slug = (($rel -split '\\')[1])
        if ($industryMap.ContainsKey($slug)) {
            $industryName = $industryMap[$slug]
            $industryLower = $industryName.ToLowerInvariant()

            $content = $content -replace 'data-wf-item-slug="hotel-management"', "data-wf-item-slug=""$slug"""
            $content = $content -replace 'href="/industry/hotel-management"', "href=""/industry/$slug"""

            $content = $content -replace '>Hotel Management<', ">$industryName<"
            $content = $content -replace 'Modern <em>Hotel Interfaces</em>', "Modern <em>$industryName Interfaces</em>"
            $content = $content -replace '<h2>for Smooth Guest Journeys</h2>', "<h2>for Better Digital Journeys</h2>"
            $content = $content -replace '<strong>UI/UX for Hotel Management Industry</strong>', "<strong>UI/UX for $industryName Industry</strong>"
            $content = $content -replace 'Good UI/UX in the Hotel Management industry is a must-have to deliver seamless guest experiences\. From booking to check-out, intuitive interfaces make every interaction smoother\. It also boosts satisfaction and loyalty\. Great design not only simplifies operations but also gives your brand a competitive edge in hospitality\.', "Good UI/UX in the $industryName industry is essential to deliver seamless user experiences. From discovery to conversion, intuitive interfaces make every interaction smoother. It improves trust, engagement, and long-term growth while giving your brand a competitive digital edge."
            $content = $content -replace 'hotel management platforms', "$industryLower platforms"
            $content = $content -replace 'hotel management systems', "$industryLower systems"
            $content = $content -replace 'hotel staff', 'teams'
            $content = $content -replace 'guest experiences', 'user experiences'
            $content = $content -replace 'Guest Insights', 'User Insights'
            $content = $content -replace 'Boost Guest Satisfaction with', 'Boost User Satisfaction with'
            $content = $content -replace 'Custom Hotel App UI/UX Solutions', "Custom $industryName App UI/UX Solutions"
            $content = $content -replace 'your hotel''s personality', 'your brand personality'
        }
    }

    # 3) Advanced schema injection
    if ($canonical -ne "") {
        $safeTitle = ($title -replace '"', '\\"')
        $safeDesc = (($desc -replace '&amp;', '&') -replace '"', '\\"')
        $safeUrl = $canonical

        $breadcrumb = Build-BreadcrumbJson $safeUrl $title
        if ($breadcrumb -ne "") {
            $content = Ensure-JsonLdBlock $content '"@type": "BreadcrumbList"' $breadcrumb
        }

        if ($rel -like 'blog\*\index.html' -and $rel -ne 'blog\index.html') {
            $articleJson = @"
        {
          "@context": "https://schema.org",
          "@type": "Article",
          "mainEntityOfPage": "$safeUrl",
          "headline": "$safeTitle",
          "description": "$safeDesc",
          "author": {
            "@type": "Organization",
            "name": "Prozesy Media"
          },
          "publisher": {
            "@type": "Organization",
            "name": "Prozesy Media"
          },
          "datePublished": "2026-03-06",
          "dateModified": "2026-04-23"
        }
"@
            $content = Ensure-JsonLdBlock $content '"@type": "Article"' $articleJson
        }

        if (($rel -like 'services\*\index.html') -or ($rel -match '^(meta-ads|google-ads|seo-optimization|ui-ux|web-app-development|branding-design|tiktok-ads)\\index\.html$')) {
            $serviceJson = @"
        {
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "$safeTitle",
          "description": "$safeDesc",
          "provider": {
            "@type": "Organization",
            "name": "Prozesy Media",
            "url": "https://www.prozesy.com/"
          },
          "areaServed": "Worldwide",
          "url": "$safeUrl"
        }
"@
            $content = Ensure-JsonLdBlock $content '"@type": "Service"' $serviceJson
        }

        if ($rel -like 'products\*\index.html' -and $rel -ne 'products\index.html') {
            $productJson = @"
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "$safeTitle",
          "description": "$safeDesc",
          "brand": {
            "@type": "Brand",
            "name": "Prozesy Media"
          },
          "url": "$safeUrl"
        }
"@
            $content = Ensure-JsonLdBlock $content '"@type": "Product"' $productJson
        }

        if ($rel -match '^(biplop-sharkar|bitas-pramanik|mehdi-hasan-soikot|mostafizur-rahman|nahid-islam|olivia-jade|rahmatullah-onu|rahul-roy|tasfeen-nayem|yash-vardhan)\\index\.html$') {
            $name = $title.Split('|')[0].Trim()
            $personJson = @"
        {
          "@context": "https://schema.org",
          "@type": "Person",
          "name": "$name",
          "url": "$safeUrl",
          "worksFor": {
            "@type": "Organization",
            "name": "Prozesy Media"
          }
        }
"@
            $content = Ensure-JsonLdBlock $content '"@type": "Person"' $personJson
        }

        if ($rel -like 'projects\*\index.html' -and $rel -ne 'projects\index.html') {
            $creativeJson = @"
        {
          "@context": "https://schema.org",
          "@type": "CreativeWork",
          "name": "$safeTitle",
          "description": "$safeDesc",
          "url": "$safeUrl",
          "creator": {
            "@type": "Organization",
            "name": "Prozesy Media"
          }
        }
"@
            $content = Ensure-JsonLdBlock $content '"@type": "CreativeWork"' $creativeJson
        }
    }

    if ($content -ne $original) {
        [System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
        $updated++
    }
}

Write-Host "Updated files: $updated"
