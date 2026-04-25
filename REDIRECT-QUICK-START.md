# DESIGN-MONKS → PROZESY: QUICK START GUIDE
## Complete External Redirect & Link Management

---

## 📋 WHAT YOU NEED TO DO

### IMMEDIATE (Today)
1. ✅ Upload `.htaccess` file to your web root
2. ✅ Test the 4 redirect URLs

### THIS WEEK  
3. Create 4 new pages (or add redirects manually if using Netlify/Vercel)
4. Test 301 redirects in browser

### THIS MONTH
5. Monitor Google Search Console
6. Update sitemap.xml
7. Monitor traffic for old URLs

---

## 🔗 THE 4 EXTERNAL REDIRECTS YOU NEED

| OLD URL | NEW URL | WHERE LINKED |
|---------|---------|--------------|
| / | /prozesy-vs-agencies | Footer of all 96 pages |
| / | /prozesy-vs-freelancers | Footer of all 96 pages |
| / | /prozesy-vs-inhouse | Footer of all 96 pages |
| /blog-category/life-at-design-monks | /blog-category/life-at-prozesy | blogs/index.html |

---

## 🛠️ IMPLEMENTATION OPTIONS

### Option 1: Using .htaccess (Apache Hosting)
✅ **Best for: Shared hosting, cPanel, traditional servers**

1. Copy the `.htaccess` file from this project folder
2. Upload to your domain's root directory
3. Test: Visit https://yourdomain.com/ (should redirect)
4. Done!

**Test redirect:**
```bash
curl -I https://yourdomain.com/
# Should show: HTTP/1.1 301 Moved Permanently
# Location: /prozesy-vs-agencies
```

---

### Option 2: Using Nginx Configuration
✅ **Best for: VPS, Nginx servers, modern hosting**

Add to your nginx server block (`/etc/nginx/sites-available/yourdomain.com`):

```nginx
# Redirect design-monks URLs to prozesy
rewrite ^//?$ /prozesy-vs-agencies/ permanent;
rewrite ^//?$ /prozesy-vs-freelancers/ permanent;
rewrite ^//?$ /prozesy-vs-inhouse/ permanent;
rewrite ^/blog-category/life-at-design-monks/?$ /blog-category/life-at-prozesy/ permanent;
```

Then reload Nginx:
```bash
sudo systemctl reload nginx
```

---

### Option 3: Using Netlify Redirects
✅ **Best for: Netlify hosting**

Create a `_redirects` file in your site root:

```
/ /prozesy-vs-agencies 301
/ /prozesy-vs-freelancers 301
/ /prozesy-vs-inhouse 301
/blog-category/life-at-design-monks /blog-category/life-at-prozesy 301
```

Or use `netlify.toml`:

```toml
[[redirects]]
  from = "/"
  to = "/prozesy-vs-agencies"
  status = 301

[[redirects]]
  from = "/"
  to = "/prozesy-vs-freelancers"
  status = 301

[[redirects]]
  from = "/"
  to = "/prozesy-vs-inhouse"
  status = 301

[[redirects]]
  from = "/blog-category/life-at-design-monks"
  to = "/blog-category/life-at-prozesy"
  status = 301
```

---

### Option 4: Using Vercel Redirects
✅ **Best for: Vercel hosting**

In `vercel.json`:

```json
{
  "redirects": [
    {
      "source": "/",
      "destination": "/prozesy-vs-agencies",
      "permanent": true
    },
    {
      "source": "/",
      "destination": "/prozesy-vs-freelancers",
      "permanent": true
    },
    {
      "source": "/",
      "destination": "/prozesy-vs-inhouse",
      "permanent": true
    },
    {
      "source": "/blog-category/life-at-design-monks",
      "destination": "/blog-category/life-at-prozesy",
      "permanent": true
    }
  ]
}
```

---

### Option 5: Using CloudFlare (All Hosting)
✅ **Best for: Any hosting with CloudFlare DNS**

1. Go to CloudFlare Dashboard > Your Domain > Rules > Page Rules
2. Create 4 forwarding rules:

```
 → forward to prozesy-vs-agencies (301)
 → forward to prozesy-vs-freelancers (301)
 → forward to prozesy-vs-inhouse (301)
blog-category/life-at-design-monks → forward to blog-category/life-at-prozesy (301)
```

Or use CloudFlare Dashboard > Rules > Redirect Rules (new method)

---

## 📁 FILES PROVIDED FOR REDIRECT MANAGEMENT

```
c:\Users\mpro\Desktop\mprnew\
├── .htaccess                              [Apache redirect config]
├── DESIGN-MONKS-REDIRECT-MAPPING.md       [Complete reference guide]
├── redirect-reference.csv                 [CSV format - all URLs]
├── redirect-config.json                   [JSON format - config file]
└── replace_monk_text.ps1                  [Script used for text replacements]
```

---

## 📊 WHAT'S ALREADY DONE

✅ **92 HTML files updated** - Text replacements completed
- "Home is where the monk lives" → "Home is where the Prozesy lives"
- "An overview of the Monk family" → "An overview of the Prozesy family"
- "Be a Monk!" → "Be a Prozesy!"

✅ **All social links preserved** - No changes to:
- Dribbble: dribbble.com/design_monks
- LinkedIn: linkedin.com/company/designmonks
- Twitter: twitter.com/design_monks
- Telegram: t.me/designmonks
- TidyCal: tidycal.com/designmonks

✅ **All Webflow assets preserved** - No changes to:
- CSS files (design-monks.*.min.css)
- JS files (design-monks.*.js)
- Image assets
- GitHub resources

---

## ⚠️ WHAT STILL NEEDS DOING

❌ **4 redirects needed** - Choose ONE implementation method above:
1. / → /prozesy-vs-agencies
2. / → /prozesy-vs-freelancers
3. / → /prozesy-vs-inhouse
4. /blog-category/life-at-design-monks → /blog-category/life-at-prozesy

❌ **Create 4 new pages** with Prozesy names (with similar content)

❌ **Update sitemap.xml** to include new page URLs

❌ **Submit to Google Search Console** after redirects are live

---

## 🧪 TESTING YOUR REDIRECTS

After implementation, test each redirect:

```bash
# Test 1: 
curl -I https://yourdomain.com/
# Expected: 301 Moved Permanently → /prozesy-vs-agencies

# Test 2: 
curl -I https://yourdomain.com/
# Expected: 301 Moved Permanently → /prozesy-vs-freelancers

# Test 3: 
curl -I https://yourdomain.com/
# Expected: 301 Moved Permanently → /prozesy-vs-inhouse

# Test 4: blog category
curl -I https://yourdomain.com/blog-category/life-at-design-monks
# Expected: 301 Moved Permanently → /blog-category/life-at-prozesy
```

Or simply visit the old URLs in your browser - they should automatically redirect.

---

## 📈 MONITORING AFTER LAUNCH

1. **Google Search Console**
   - Monitor Coverage report
   - Check for crawl errors
   - Verify new URLs are indexed within 2 weeks

2. **Analytics**
   - Check traffic to old URLs (should drop to 0)
   - Check traffic to new URLs (should increase)
   - Monitor bounce rate

3. **Backlinks**
   - Google your domain + "design-monks"
   - Any external backlinks to old URLs will still work (redirects preserve value)

4. **Search Results**
   - Google: site:yourdomain.com design-monks
   - Should show redirects, not 404s
   - Within 30 days, old URLs should drop from search results

---

## 🎯 SUMMARY

| Task | Status | Effort | Priority |
|------|--------|--------|----------|
| Text replacement (92 files) | ✅ DONE | LOW | N/A |
| .htaccess file | ✅ READY | LOW | HIGH |
| Redirect setup | ⚠️ PENDING | 30 min | HIGH |
| New pages creation | ⚠️ PENDING | 2-4 hours | MEDIUM |
| Sitemap update | ⚠️ PENDING | 15 min | MEDIUM |
| GSC monitoring | ⚠️ PENDING | ONGOING | LOW |

**Estimated Total Time: 3-5 hours**

---

## 📞 SUPPORT

Reference Files Available:
- `.htaccess` - Apache redirect configuration
- `DESIGN-MONKS-REDIRECT-MAPPING.md` - Complete reference guide
- `redirect-reference.csv` - All URLs in spreadsheet format
- `redirect-config.json` - Machine-readable config
- `redirect-config.json` - Implementation checklist

All files are in: `c:\Users\mpro\Desktop\mprnew\`
