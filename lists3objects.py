import sys
import boto3

def main():
    prefix = ""
    bucket = ""
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("--bucket="):
            bucket = arg.split("=")[1]
        if arg.startswith("--prefix="):
            prefix = arg.split("=")[1]
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            # name, size and last modified
            print(f"{obj['Key']} {obj['Size']} {obj['LastModified']}")

if __name__ == "__main__":
    main()
