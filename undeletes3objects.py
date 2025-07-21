import sys
import boto3

def main():
    prefix = ""
    bucket = ""
    dry_run = True 

    args = sys.argv[1:]
    dry_run = True 

    for arg in args:
        if arg == "--delete":
            dry_run = False
        if arg.startswith("--bucket="):
            bucket = arg.split("=")[1]
        if arg.startswith("--prefix="):
            prefix = arg.split("=")[1]

    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_object_versions")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for dm in page.get("DeleteMarkers", []):
            if not dm["IsLatest"]:
                continue
            key = dm["Key"]
            vid = dm["VersionId"]
            if dry_run:
                print(f"[DRY RUN] would remove delete marker: {key} (version {vid})")
            else:
                s3.delete_object(Bucket=bucket, Key=key, VersionId=vid)
                print(f"Removed delete marker: {key} (version {vid})")

if __name__ == "__main__":
    main()
