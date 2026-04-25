import boto3
from botocore.exceptions import ClientError

ACCOUNT_ID  = "20fe549097cc4110c9f9d5c4f4ed3760"
ACCESS_KEY  = "b3b2985b2c3b441091df72f4aa376e6b"
SECRET_KEY  = "85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365"
BUCKET_NAME = "videos"
ENDPOINT    = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

MIME_TYPES = {
    ".svg":   "image/svg+xml",
    ".avif":  "image/avif",
    ".webp":  "image/webp",
    ".png":   "image/png",
    ".jpg":   "image/jpeg",
    ".jpeg":  "image/jpeg",
    ".gif":   "image/gif",
    ".ico":   "image/x-icon",
    ".css":   "text/css; charset=utf-8",
    ".js":    "application/javascript; charset=utf-8",
    ".html":  "text/html; charset=utf-8",
    ".json":  "application/json; charset=utf-8",
    ".woff":  "font/woff",
    ".woff2": "font/woff2",
    ".ttf":   "font/ttf",
    ".otf":   "font/otf",
    ".mp4":   "video/mp4",
    ".webm":  "video/webm",
    ".mov":   "video/quicktime",
    ".mp3":   "audio/mpeg",
    ".pdf":   "application/pdf",
}

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

import os

updated = 0
skipped = 0
failed = 0

paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=BUCKET_NAME)

for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        ext = os.path.splitext(key)[1].lower()
        content_type = MIME_TYPES.get(ext)
        if not content_type:
            skipped += 1
            continue

        # Check current content type
        try:
            head = s3.head_object(Bucket=BUCKET_NAME, Key=key)
            current_ct = head.get("ContentType", "")
        except ClientError:
            current_ct = ""

        if current_ct == content_type:
            skipped += 1
            continue

        # Copy object onto itself with correct ContentType
        try:
            s3.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={"Bucket": BUCKET_NAME, "Key": key},
                Key=key,
                ContentType=content_type,
                MetadataDirective="REPLACE",
            )
            updated += 1
            if updated % 50 == 0:
                print(f"  Updated {updated} so far... last: {key}")
        except ClientError as e:
            failed += 1
            print(f"  FAIL: {key} -> {e}")

print(f"\nDone! Updated: {updated}, Skipped (already correct/unknown ext): {skipped}, Failed: {failed}")
