import boto3, os
from botocore.exceptions import ClientError

ACCOUNT_ID  = "20fe549097cc4110c9f9d5c4f4ed3760"
ACCESS_KEY  = "b3b2985b2c3b441091df72f4aa376e6b"
SECRET_KEY  = "85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365"
BUCKET_NAME = "videos"
ENDPOINT    = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

local_dir = r"c:\Users\mpro\Desktop\mprnew\mpr-main\local"

total = 0
failed = 0
skipped = 0

for root, _, files in os.walk(local_dir):
    for file in files:
        filepath = os.path.join(root, file)
        key = "local/" + os.path.relpath(filepath, local_dir).replace("\\", "/")
        try:
            # Check if already exists
            try:
                s3.head_object(Bucket=BUCKET_NAME, Key=key)
                skipped += 1
                continue
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise

            s3.upload_file(filepath, BUCKET_NAME, key)
            total += 1
            print(f"  OK: {key}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {key} -> {e}")

print(f"\nUploaded: {total}, Skipped (already exists): {skipped}, Failed: {failed}")
